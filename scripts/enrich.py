#!/usr/bin/env python3
# Enriquece os códigos CNES (parsed.json) com nome, endereço, telefone e
# coordenadas oficiais via API de Dados Abertos do CNES/DATASUS.
# Nome do município e centroide (fallback de coordenada) vêm do dataset
# municipios-brasileiros (IBGE).  Saída: hospitais.json
import json, os, csv, urllib.request, urllib.error, concurrent.futures as cf, time

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CACHE='data/cnes_cache'; os.makedirs(CACHE, exist_ok=True)
UA={'User-Agent':'Mozilla/5.0','Accept':'application/json'}
MUNI_CSV='data/municipios.csv'
MUNI_URL='https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv'

UF_BY_COD={11:'RO',12:'AC',13:'AM',14:'RR',15:'PA',16:'AP',17:'TO',21:'MA',22:'PI',
 23:'CE',24:'RN',25:'PB',26:'PE',27:'AL',28:'SE',29:'BA',31:'MG',32:'ES',33:'RJ',
 35:'SP',41:'PR',42:'SC',43:'RS',50:'MS',51:'MT',52:'GO',53:'DF'}

def get_json(url, tries=3, timeout=25):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            time.sleep(1+t)
        except Exception:
            time.sleep(1+t)
    return None

# municipios: codigo_ibge(6) -> (nome, lat, lon)
if not os.path.exists(MUNI_CSV):
    urllib.request.urlretrieve(MUNI_URL, MUNI_CSV)
muni_name={}; muni_centroid={}
for row in csv.DictReader(open(MUNI_CSV, encoding='utf-8')):
    k=row['codigo_ibge'][:6]
    muni_name[k]=row['nome']
    muni_centroid[k]=(float(row['latitude']), float(row['longitude']))
print('municipios:', len(muni_name))

def fetch(code):
    fp=os.path.join(CACHE, code+'.json')
    if os.path.exists(fp):
        try: return json.load(open(fp))
        except: pass
    d=get_json(f'https://apidadosabertos.saude.gov.br/cnes/estabelecimentos/{code}')
    json.dump(d, open(fp,'w'))
    return d

recs=json.load(open('parsed.json'))
print('consultando', len(recs), 'CNES...')
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(fetch, [r['cnes'] for r in recs]))

out=[]; not_found=0; approx_n=0
for r in recs:
    d=fetch(r['cnes'])
    if not d or 'codigo_cnes' not in d:
        not_found+=1; continue
    lat=d.get('latitude_estabelecimento_decimo_grau')
    lon=d.get('longitude_estabelecimento_decimo_grau')
    cm=str(d.get('codigo_municipio') or '')
    approx=False
    if (lat in (None,0) or lon in (None,0)) or not(-34<=(lat or -99)<=6 and -74<=(lon or -99)<=-34):
        c=muni_centroid.get(cm)
        if not c: continue
        lat,lon=c; approx=True; approx_n+=1
    end=' '.join(x for x in [d.get('endereco_estabelecimento'), d.get('numero_estabelecimento'),
         d.get('bairro_estabelecimento')] if x).strip()
    out.append({'cnes':r['cnes'],'uf':UF_BY_COD.get(d.get('codigo_uf'), r['uf']),
        'municipio':muni_name.get(cm,''),
        'nome':(d.get('nome_fantasia') or d.get('nome_razao_social') or '').strip(),
        'endereco':end,'cep':d.get('codigo_cep_estabelecimento'),
        'telefone':d.get('numero_telefone_estabelecimento'),
        'lat':round(lat,6),'lon':round(lon,6),'aprox':approx,
        'antivenenos':r['antivenenos']})

# dedupe global por CNES (mantém a lista de soros mais completa)
by={}
for r in out:
    k=r['cnes']
    if k not in by or len(r['antivenenos'])>len(by[k]['antivenenos']): by[k]=r
out=sorted(by.values(), key=lambda r:(r['uf'], r['municipio'], r['nome']))
json.dump(out, open('hospitais.json','w'), ensure_ascii=False, indent=1)
print(f'hospitais={len(out)} nao_encontrados={not_found} coord_aproximada={approx_n}')
