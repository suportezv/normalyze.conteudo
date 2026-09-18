#!/usr/bin/env bash
# Baixa o GSAP para dentro de um projeto hyperframes e reescreve o index.html
# para apontar para a copia local.
#
#   bash scripts/vendor-gsap.sh <dir-do-projeto-hyperframes>
#
# Por que: composicoes do hyperframes carregam o GSAP de cdn.jsdelivr.net, que
# nao esta no allowlist do environment. O Chrome do render busca esse script
# direto, sem passar pelo agent proxy, e o render morre com
# "sub_timeline_script_failure". Com o dominio liberado isto vira desnecessario.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/scripts/env.sh"

DIR="${1:-.}"
INDEX="$DIR/index.html"
[ -f "$INDEX" ] || { echo "nao achei $INDEX"; exit 1; }

# A versao vem do proprio index.html, para nao descolar do que a composicao pede.
VERSAO="$(grep -oE 'gsap@[0-9]+\.[0-9]+\.[0-9]+' "$INDEX" | head -1 | cut -d@ -f2)"
[ -n "$VERSAO" ] || { echo "index.html nao referencia gsap por CDN; nada a fazer"; exit 0; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -sL --max-time 120 -o "$TMP/gsap.tgz" "https://registry.npmjs.org/gsap/-/gsap-$VERSAO.tgz"
tar -xzf "$TMP/gsap.tgz" -C "$TMP"
mkdir -p "$DIR/vendor"
cp "$TMP/package/dist/gsap.min.js" "$DIR/vendor/gsap.min.js"

sed -i "s#https://cdn.jsdelivr.net/npm/gsap@$VERSAO/dist/gsap.min.js#vendor/gsap.min.js#g" "$INDEX"
echo "gsap $VERSAO em $DIR/vendor/gsap.min.js e index.html reescrito"
