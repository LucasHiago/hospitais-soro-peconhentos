#!/usr/bin/env python3
# Gera cidades.json (todas as cidades do Brasil + coordenadas) a partir do
# dataset municipios-brasileiros (IBGE), para a busca "hospitais perto de mim".
import csv, json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
out=[]
for r in csv.DictReader(open('data/municipios.csv', encoding='utf-8')):
    out.append({'n':r['nome'],'uf':r['codigo_uf'],
                'lat':round(float(r['latitude']),4),'lon':round(float(r['longitude']),4)})
# mapeia codigo_uf numerico -> sigla
COD={'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA',
 '22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA',
 '31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS',
 '51':'MT','52':'GO','53':'DF'}
for c in out: c['uf']=COD.get(c['uf'], c['uf'])
out.sort(key=lambda c:(c['n'], c['uf']))
json.dump(out, open('cidades.json','w'), ensure_ascii=False, separators=(',',':'))
print('cidades:', len(out))
