#!/usr/bin/env python3
# Extract CNES codes + antivenom info from the gov.br reference-hospital PDFs.
# Robust approach (layout-independent): CNES = standalone 7-digit number
# (DF uses 5-digit). Antivenom keywords are assigned to the nearest code line.
# Municipality / name / address / coords come later from the CNES open-data API.
import re, os, json, glob, unicodedata

UF = {
 'acre':'AC','alagoas':'AL','amapa':'AP','amazonas':'AM','bahia':'BA','ceara':'CE',
 'distrito-federal':'DF','espirito-santo':'ES','goias':'GO','maranhao':'MA',
 'mato-grosso':'MT','mato-grosso-do-sul':'MS','minas-gerais':'MG','para':'PA',
 'paraiba':'PB','parana':'PR','pernambuco':'PE','piaui':'PI','rio-de-janeiro':'RJ',
 'rio-grande-do-norte':'RN','rio-grande-do-sul':'RS','rondonia':'RO','roraima':'RR',
 'santa-catarina':'SC','sao-paulo':'SP','sergipe':'SE','tocantins':'TO'}

def norm(s): return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().upper()

SERA = [(r'BOTROPIC','Botrópico'),(r'CROTALIC','Crotálico'),(r'LAQUETIC','Laquético'),
 (r'ELAPIDIC','Elapídico'),(r'LOXOSCEL','Loxoscélico'),(r'FONEUTRIC','Fonêutrico'),
 (r'ESCORPION','Escorpiônico'),(r'ARACNID','Aracnídico'),(r'LONOMIC','Lonômico')]
def sera_of(text):
    t=norm(text); out=[]
    for pat,lab in SERA:
        if re.search(pat,t) and lab not in out: out.append(lab)
    return out

def codes_in(line, five=False):
    pat = r'(?<!\d)\d{5}(?!\d)' if five else r'(?<!\d)\d{7}(?!\d)'
    return re.findall(pat, line)

def parse_file(path, slug):
    five = (slug=='distrito-federal')
    lines = open(path,encoding='utf-8',errors='replace').read().split('\n')
    # per line: list of codes found, and serum keywords found
    code_lines = []   # (line_idx, code)
    for i,ln in enumerate(lines):
        for c in codes_in(ln, five):
            code_lines.append((i,c))
    if not code_lines: return []
    # assign each line's serum keywords to nearest code line
    anchors = [i for i,_ in code_lines]
    agg = {c:set() for _,c in code_lines}
    # keep first code per anchor-line order, but allow multiple codes/line
    for i,ln in enumerate(lines):
        s = sera_of(ln)
        if not s: continue
        ai = min(range(len(anchors)), key=lambda k: abs(anchors[k]-i))
        agg[code_lines[ai][1]].update(s)
    seen=set(); recs=[]
    for _,c in code_lines:
        if c in seen: continue
        seen.add(c)
        recs.append({'uf':UF[slug],'cnes':c,
                     'antivenenos':[lab for _,lab in SERA if lab in agg[c]]})
    return recs

all_recs=[]
for f in sorted(glob.glob("data/txt/*.txt")):
    slug=os.path.basename(f)[:-4]
    if slug=='piaui': continue
    r=parse_file(f,slug); all_recs+=r
    print(f'{slug:22} {len(r)}')

# Piaui (image-only PDF) — transcribed from rendered pages
piaui=[('Amarante','2364883'),('Barras','2323915'),('Bom Jesus','2364816'),
 ('Campo Maior','2777754'),('Corrente','2777770'),('Floriano','2365146'),
 ('Fronteiras','2694301'),('Oeiras','2777762'),('Parnaíba','8015899'),
 ('Paulistana','2364913'),('Picos','4009622'),('Piripiri','2777746'),
 ('São João do Piauí','2365383'),('São Raimundo Nonato','2777649'),
 ('Teresina','2323338'),('Uruçui','2323680'),('Valença','2777789')]
full=['Botrópico','Crotálico','Elapídico','Fonêutrico','Loxoscélico','Laquético','Escorpiônico']
basic=['Botrópico','Crotálico','Elapídico','Escorpiônico']
fullset={'2364816','2777754','2777770','2777762','4009622','2323680','2777789'}
loxset={'2323915','8015899'}  # Botr,Crot,Elap,Fone,Loxo,Escorp
for mun,c in piaui:
    if c in fullset: a=full
    elif c in loxset: a=['Botrópico','Crotálico','Elapídico','Fonêutrico','Loxoscélico','Escorpiônico']
    else: a=basic
    all_recs.append({'uf':'PI','cnes':c,'antivenenos':a})
print('piaui                 ',len(piaui))

json.dump(all_recs,open('parsed.json','w'),ensure_ascii=False,indent=1)
print('TOTAL',len(all_recs))
