#!/usr/bin/env bash
# Validação do Normalyze Conteúdo Studio. Itens de MCP (Metricool, Kairogen) validam-se
# dentro da sessão do Claude, não aqui.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/scripts/env.sh"

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
# O patch local de is_portrait_source foi aposentado em 18/set/2026: o upstream
# passou a ler o "rotation" do side data. O que importa é o comportamento, não
# a presença do patch, então conferimos a detecção de rotação.
if grep -q "stream_side_data=rotation" "$VIDEO_USE/helpers/render.py" 2>/dev/null; then
  echo "OK (is_portrait_source lê rotação do side data)"
else
  echo "FALHOU (is_portrait_source sem detecção de rotação; vertical vira paisagem)"
fi

echo "== 3. Rede do environment =="
for host in registry.npmjs.org pypi.org github.com raw.githubusercontent.com \
            drive.google.com drive.usercontent.google.com api.elevenlabs.io \
            api.openai.com generativelanguage.googleapis.com cdn.jsdelivr.net; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 12 "https://$host" 2>/dev/null)
  case "$code" in
    000|403) echo "  BLOQUEADO $host (liberar no environment)";;
    *)       echo "  OK        $host ($code)";;
  esac
done

echo "== 4. ElevenLabs =="
if grep -q '^ELEVENLABS_API_KEY=sk_' "$VIDEO_USE/.env" 2>/dev/null; then
  echo "OK (chave sk_ presente; transcrição real gasta créditos, rodar sob demanda)"
else
  echo "PENDENTE: ELEVENLABS_API_KEY sk_ ausente no .env do video-use"
fi

echo "== 5. OpenAI + Gemini =="
python3 "$REPO_ROOT/scripts/llm.py" --check 2>&1 | sed 's/^/  /'

echo "== 6. Remotion =="
if npm view remotion version >/dev/null 2>&1; then
  echo "OK (registry responde: remotion $(npm view remotion version 2>/dev/null))"
else
  echo "FALHOU (registry.npmjs.org inacessível)"
fi
[ -n "${CHROME_SHELL:-}" ] && echo "OK (Chrome: $CHROME_SHELL)" || echo "FALHOU (headless shell não encontrado)"

echo "== 7. hyperframes =="
if npx --yes hyperframes --version >/dev/null 2>&1; then
  echo "OK (CLI $(npx --yes hyperframes --version 2>/dev/null))"
else
  echo "FALHOU (CLI não roda; precisa de registry.npmjs.org e Node 22+)"
fi
[ -e ~/.claude/skills/hyperframes/SKILL.md ] && echo "OK (skills registradas)" || echo "PENDENTE: skills do hyperframes"

echo "== 8. Skills registradas =="
[ -e ~/.claude/skills/video-use/SKILL.md ] && echo "OK video-use" || echo "PENDENTE video-use"

echo "== 9. Na sessão do Claude, validar ainda: =="
echo " - Metricool: getBrandSettings deve listar a marca da Normalyze com Instagram conectado (blog_id 6735045)"
echo " - Kairogen: get_me_context mostra plano Essential+ e créditos"
