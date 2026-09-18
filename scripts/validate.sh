#!/usr/bin/env bash
# Validação do Normalyze Conteúdo Studio. Itens de MCP (Metricool, Kairogen)
# validam-se dentro da sessão do Claude, não aqui.
set -uo pipefail

TOOLS_DIR="${TOOLS_DIR:-/workspace}"
VIDEO_USE="$TOOLS_DIR/browser-use/video-use"
[ -d "$VIDEO_USE" ] || VIDEO_USE="$HOME/video-editor/video-use"
FF_PATH="/opt/homebrew/opt/ffmpeg-full/bin"
[ -d "$FF_PATH" ] && export PATH="$FF_PATH:$PATH"

echo "== 1. ffmpeg: subtitles + zscale =="
N=$(ffmpeg -filters 2>/dev/null | grep -cE "subtitles|zscale")
if [ "${N:-0}" -ge 2 ]; then echo "OK ($N filtros)"; else echo "FALHOU (esperado >=2, obtido ${N:-0})"; fi

echo "== 2. video-use helpers =="
if (cd "$VIDEO_USE" && { [ -d .venv ] && .venv/bin/python helpers/timeline_view.py --help >/dev/null 2>&1 || python3 helpers/timeline_view.py --help >/dev/null 2>&1; }); then
  echo "OK (helpers importam)"
else
  echo "FALHOU (helpers não rodam em $VIDEO_USE)"
fi
# Testa o comportamento, nao a presenca de um patch: gera tres arquivos
# sinteticos (retrato, paisagem e paisagem com matriz de rotacao 90, que e o
# caso da camera que grava em pe) e confere as tres respostas.
_tmp="$(mktemp -d)"
ffmpeg -hide_banner -v error -f lavfi -i testsrc=size=540x960:duration=1:rate=10 \
  -c:v libx264 -pix_fmt yuv420p -y "$_tmp/retrato.mp4" 2>/dev/null
ffmpeg -hide_banner -v error -f lavfi -i testsrc=size=960x540:duration=1:rate=10 \
  -c:v libx264 -pix_fmt yuv420p -y "$_tmp/paisagem.mp4" 2>/dev/null
ffmpeg -hide_banner -v error -display_rotation 90 -i "$_tmp/paisagem.mp4" \
  -c copy -y "$_tmp/girado.mp4" 2>/dev/null
if python3 - "$VIDEO_USE" "$_tmp" <<'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from helpers import render
tmp = Path(sys.argv[2])
casos = [("retrato.mp4", True), ("paisagem.mp4", False), ("girado.mp4", True)]
ruins = [n for n, esperado in casos if render.is_portrait_source(tmp / n) != esperado]
if ruins:
    print("falhou em: " + ", ".join(ruins))
    sys.exit(1)
PYEOF
then
  echo "OK (is_portrait_source acerta retrato, paisagem e girado)"
else
  echo "FALHA: is_portrait_source erra a orientação; vertical vai sair em paisagem"
fi
rm -rf "$_tmp"

echo "== 3. ElevenLabs =="
if grep -q '^ELEVENLABS_API_KEY=sk_' "$VIDEO_USE/.env" 2>/dev/null; then
  echo "OK (chave sk_ presente; transcrição real gasta créditos, rodar sob demanda)"
else
  echo "PENDENTE: ELEVENLABS_API_KEY sk_ ausente no .env do video-use"
fi

echo "== 4. Rede (environment com domínios liberados) =="
for D in https://drive.google.com/ https://drive.usercontent.google.com/ https://api.elevenlabs.io/v1/user; do
  C=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$D")
  if [ "$C" = "000" ]; then echo "FALHOU $D (000: domínio não liberado)"; else echo "OK $D (HTTP $C)"; fi
done

echo "== 5. Remotion =="
REMOTION="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/remotion"
if [ ! -d "$REMOTION/node_modules/remotion" ]; then
  echo "PENDENTE: deps do Remotion não instaladas (rode scripts/setup.sh)"
else
  _shell="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
  if [ ! -x "$_shell" ]; then
    echo "AVISO: headless_shell do Playwright ausente; o render do Remotion vai falhar"
  else
    # Prova real: renderiza 1 frame. O Chromium normal do Playwright nao serve
    # (removeu o headless antigo), por isso o config aponta para o headless_shell.
    _png="$(mktemp -d)/frame.png"
    if (cd "$REMOTION" && npx --no-install remotion still src/index.ts \
        CartaoTituloVertical "$_png" --frame=90 >/dev/null 2>&1) && [ -s "$_png" ]; then
      echo "OK (render de 1 frame funciona: $(node -p "require('$REMOTION/package.json').dependencies.remotion"))"
    else
      echo "FALHA: Remotion não renderizou; ver remotion/remotion.config.ts"
    fi
    rm -rf "$(dirname "$_png")"
  fi
fi

echo "== 6. Skills registradas =="
[ -e ~/.claude/skills/video-use/SKILL.md ] && echo "OK video-use" || echo "PENDENTE video-use"
HF=$(ls -d ~/.claude/skills/*/ 2>/dev/null | while read -r d; do [ -f "$d/SKILL.md" ] && basename "$d"; done | grep -cE 'hyperframes|media-use|motion-graphics|embedded-captions')
if [ "${HF:-0}" -ge 4 ]; then echo "OK hyperframes ($HF skills com SKILL.md)"; else echo "PENDENTE hyperframes (rode scripts/setup.sh)"; fi

echo "== 7. Na sessão do Claude, validar ainda: =="
echo " - Metricool: getBrandSettings lista a marca normalyze.ai com blog_id 6735045"
echo " - Kairogen: get_me_context mostra plano Essential e créditos"
