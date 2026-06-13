#!/usr/bin/env bash
# Baixa os 27 PDFs de "Hospitais de Referência" (soro antipeçonhento) do gov.br/saude
# e extrai o texto com layout preservado. Saída em data/pdfs e data/txt.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/pdfs data/txt
BASE="https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/a/animais-peconhentos/hospitais-de-referencia"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
SLUGS=(acre alagoas amapa amazonas bahia ceara distrito-federal espirito-santo goias
  maranhao mato-grosso mato-grosso-do-sul minas-gerais para paraiba parana pernambuco
  piaui rio-de-janeiro rio-grande-do-norte rio-grande-do-sul rondonia roraima
  santa-catarina sao-paulo sergipe tocantins)

for s in "${SLUGS[@]}"; do
  echo "baixando $s ..."
  curl -s -A "$UA" -H "Accept: */*" -H "Accept-Language: pt-BR,pt;q=0.9" \
    -H "Referer: $BASE" --compressed -L \
    -o "data/pdfs/$s.pdf" "$BASE/$s/@@download/file"
  pdftotext -layout "data/pdfs/$s.pdf" "data/txt/$s.txt" 2>/dev/null || true
done
echo "ok: $(ls data/pdfs | wc -l) PDFs em data/pdfs/"
