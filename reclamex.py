import time
from bs4 import BeautifulSoup
import requests
import aiohttp
import asyncio
import unidecode
import warnings
import argparse
from colorama import init, Fore
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
import re

warnings.simplefilter('ignore', InsecureRequestWarning)
init()

parser = argparse.ArgumentParser(description = 'Extrator de CPF do ReclameAqui.')
parser.add_argument('-e', action = 'store', dest = 'emp',
                           required = True,
                           help = 'O nome da empresa.')
arguments = parser.parse_args()

proxy = {
    'http': 'http://127.0.0.1:8080',
    'https': 'http://127.0.0.1:8080',
}
proxy_aiohttp = "http://127.0.0.1:8080"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.0; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en,pt-BR;q=0.9,pt;q=0.8,en-US;q=0.7"
}

async def extraiCPF(session, link):
    url = f'https://www.reclameaqui.com.br/{link}/'
    async with session.request(url=url,method="GET",headers=headers, ssl=False) as response:
        soup = BeautifulSoup(await response.text(), 'html.parser')
        try:
            desc = soup.find('p',{"data-testid": "complaint-description"}).getText()
            cpfs = re.findall(r' [0-9]{11}', desc)
            cpfs.append(re.findall(r'\d{3}\.\d{3}\.\d{3}\-\d{2}', desc))
            if len(cpfs) > 1:
                for c in cpfs:
                    print (f'[+] {c} {url}')
                    return ({"cpfs":{c},"url": {url}})
            return ({"cpfs":None,"url": {url}})
        except:
            return ({"cpfs":None,"url": {url}})

async def buscaCpf(emp):
    start_time = time.time()
    timeout = aiohttp.ClientTimeout(total=20)
    print (f"{Fore.LIGHTYELLOW_EX}[!] Filtrando reclamações da {emp['companyName']} pelo termo 'cpf'\033[0m")

    count = 1
    idBusca = 10
    while count > 0:
        response = requests.request('GET',f'https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/query/cpf/10/{idBusca}?company={emp["id"]}', proxies=proxy, headers=headers, verify=False)
        json = response.json()
        count = json['complainResult']['complains']['count']
        idBusca += 10
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = []
            for r in json['complainResult']['complains']['data']:
                titulo = unidecode.unidecode(r['title'].lower())
                titulo = re.sub(r'[!@#$%^&*.]+','',titulo)
                titulo = re.sub(r"\s+",'-',titulo)
                link = f'{r["companyShortname"]}/{titulo}_{r["id"]}'
                task = asyncio.ensure_future(extraiCPF(session,link))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print (f"{Fore.LIGHTYELLOW_EX}[!] Search complete in {round(time.time() - start_time,1)} seconds\033[0m")

def buscaEmp(busca):
    print (f"{Fore.LIGHTYELLOW_EX}[!] Buscando a empresa '{busca}' no Reclame Aqui\033[0m")

    response = requests.request('GET',f'https://iosearch.reclameaqui.com.br/raichu-io-site-search-v1/companies/search/{requests.utils.quote(busca)}', headers=headers, verify=False)
    json = response.json()
    if len(json['companies']) > 0:
        companies = []
        i = 0
        for c in json['companies']:
            print (f"{i} - {c['companyName']}")
            companies.append({"companyName": c['companyName'], "id": c['id']})
            i += 1
        idOpcao = input ('Digite o número da empresa desejada: ')
        emp = companies[int(idOpcao)]
        asyncio.run(buscaCpf(emp))


if arguments.emp:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    buscaEmp(arguments.emp)