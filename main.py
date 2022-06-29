#pip install yfinance quandl investpy

import json
import http.cookiejar
import urllib.request

from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

import yfinance
import quandl
import investpy as inv

import pandas as pd
import numpy as np
import argparse
import os
import csv

# Pega o histórico de Dividend Yield...
# Últimos 5 anos...
# https://statusinvest.com.br/acao/companytickerprovents?ticker=TRPL4&chartProventsType=1

def loadJson(i):
  url = f'https://statusinvest.com.br/acao/companytickerprovents?ticker={i}&chartProventsType=1'
  with opener.open(url) as link:
    company_indicators = link.read().decode('ISO-8859-1')
  return json.loads(company_indicators)

def ArrumaData(dia, data):
  while dia != 'Friday':
    data = data - timedelta(days=1)
    dia = pd.to_datetime(data, dayfirst=True).strftime('%A')
  return data

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201'),
                      ('Accept', 'text/html, text/plain, text/css, text/sgml, */*;q=0.01')]

lista_Ativos = []
lista_Ativos_SA = []

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--inputfile')
args = vars(parser.parse_args())

if not args.get('inputfile', False):
  print('Erro, nenhuma entrada encontrada')
  exit()
else:
  column_names = ['Ativos']
  df = pd.read_csv("input.csv", names=column_names)
  letters = df.Ativos.to_list()
  letters.pop(0)
  lista_Ativos = letters

date_now = datetime.date(datetime.now())
date_now_Day = pd.to_datetime(date_now, dayfirst=True).strftime('%A')
date_now_Month = pd.to_datetime(date_now, dayfirst=True).strftime('%B')

for i in lista_Ativos:
  lista_Ativos_SA.append(i+'.SA')

if date_now_Day == 'Monday' or date_now_Day == 'Sunday' or date_now_Day == 'Saturday':
  yesterday = (ArrumaData(date_now_Day, date_now)).strftime('%Y-%m-%d')
else:
  yesterday = (date_now - timedelta(days=1)).strftime('%Y-%m-%d')

conjunto_date_dy = []

for i in lista_Ativos:
  company_indicators = loadJson(i)
  company_indicators_dy = company_indicators['assetEarningsModels']

  date_dy = []

  for cont_company_indicators_dy, i in enumerate(company_indicators_dy):
    date_dy.append(company_indicators_dy[cont_company_indicators_dy].get('ed'))

  date_dy_config = pd.to_datetime(date_dy, dayfirst=True).strftime('%B')
  fdist=dict(zip(*np.unique(date_dy_config, return_counts=True)))
  conjunto_date_dy.append(fdist)

listEmpresas = []
listEmpresas_SA = []
extractAll = []

for cont_conjunto_date_dy, i in enumerate(conjunto_date_dy):
  for key in conjunto_date_dy[cont_conjunto_date_dy]:
    if key == date_now_Month:
      listEmpresas.append(lista_Ativos[cont_conjunto_date_dy])

for i in listEmpresas:
  listEmpresas_SA.append(i+'.SA')

listEmpresasDownload = yfinance.download(lista_Ativos_SA, start = yesterday, end = date_now)['Close']

for cont_listEmpresas, i in enumerate(listEmpresas):
  company_indicators = loadJson(i)
  company_indicators_media = company_indicators['assetEarningsYearlyModels']

  dy_media = []

  for cont_company_indicators_media, i in enumerate(company_indicators_media):
    dy_media.append(company_indicators_media[cont_company_indicators_media].get('value'))

  avg = sum(dy_media) / len(dy_media)
  precoTeto = avg/(6/100) #Dividend yield desejado de 6%
  value = listEmpresasDownload[listEmpresas_SA[cont_listEmpresas]].iloc[0]

  extract = {}
  extract['Ativo'] = listEmpresas[cont_listEmpresas]
  extract['Media_DY_5_anos'] = "R$%.2f" % round(avg, 2)
  extract['Preco_Teto'] = "R$%.2f" % round(precoTeto, 2)
  extract['CotacaoAtual'] = "R$%.2f" % round(value, 2)
  extract['StatusCompra'] = 'Sim' if value < precoTeto else 'Nao'
  extractAll.append(extract)

  with open('output.csv', 'w', newline='') as csvfile:
    fieldnames = ['Ativo', 'Media_DY_5_anos', 'Preco_Teto', 'CotacaoAtual', 'StatusCompra']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(extractAll)