#!/usr/bin/env bash
# Setup do Normalyze Conteúdo Studio (Linux/cloud). No Mac, siga SETUP.md manualmente.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="${TOOLS_DIR:-/workspace}"
VIDEO_USE="$TOOLS_DIR/browser-use/video-use"
HYPERFRAMES="$TOOLS_DIR/heygen-com/hyperframes"

# --- Rota de rede (cloud) ---------------------------------------------------
# O bloco vive em scripts/env.sh porque toda chamada manual de npm/npx/pip
# precisa dele tambem, nao so este setup. Ver os comentarios de la.
# shellcheck source=/dev/null
source "$REPO_ROOT/scripts/env.sh"

echo "== 1/6 ffmpeg =="
# No cloud com network Custom o apt fica bloqueado (403 no archive.ubuntu.com), então
# o caminho confiável é o build estático do BtbN via GitHub Releases, que o proxy libera.
# O build "gpl" traz libass (subtitles) e zimg (zscale), ambos obrigatórios aqui.
# IMPORTANTE: este script roda como setup de TODO container novo do environment.
# Nenhum passo pode derrubar o boot: falhas viram AVISO e a sessão nasce mesmo assim.
instala_ffmpeg_estatico() {
  # Atencao a forma da URL: "releases/download/latest/" e a tag rolante do
  # BtbN e serve o arquivo. "releases/latest/download/" parece equivalente e
  # NAO e: resolve para a autobuild do dia, cujos assets tem outro nome, e
  # devolve 404. Em 18/set/2026 isso quebrou o setup de todos os estudios.
  local urls=(
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-linux64-gpl.tar.xz"
  )
  local tmp url ffdir
  tmp="$(mktemp -d)" || return 1
  for url in "${urls[@]}"; do
    curl -sL --max-time 600 -o "$tmp/ff.tar.xz" "$url" || continue
    # Um 404 vem como corpo de texto e o tar falharia com mensagem confusa.
    # Conferir a assinatura XZ antes de extrair transforma isso em diagnostico.
    if [ "$(head -c 6 "$tmp/ff.tar.xz" | od -An -tx1 | tr -d ' \n')" != "fd377a585a00" ]; then
      echo "  $url nao devolveu um .tar.xz (provavel 404); tentando proxima"
      continue
    fi
    tar -xf "$tmp/ff.tar.xz" -C "$tmp" || continue
    ffdir="$(find "$tmp" -maxdepth 1 -type d -name 'ffmpeg-master-*' | head -1)"
    [ -n "$ffdir" ] || continue
    if install -m755 "$ffdir/bin/ffmpeg" "$ffdir/bin/ffprobe" /usr/local/bin/; then
      rm -rf "$tmp"; return 0
    fi
  done
  rm -rf "$tmp"; return 1
}

if ! command -v ffmpeg >/dev/null; then
  if ! (apt-get update -qq && apt-get install -y -qq ffmpeg fonts-liberation) 2>/dev/null; then
    echo "apt indisponível; instalando build estático do GitHub Releases"
    instala_ffmpeg_estatico \
      || echo "AVISO: ffmpeg não instalado (download/extração falhou). Edição de vídeo indisponível até rodar setup de novo."
  fi
fi
ffmpeg -version 2>/dev/null | head -1 || true

echo "== 2/6 video-use =="
if [ ! -d "$VIDEO_USE/.git" ]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/browser-use/video-use "$VIDEO_USE" || { echo "AVISO: clone do video-use falhou"; }
fi
# O patch local de is_portrait_source foi aposentado em 18/set/2026: o upstream
# reescreveu a funcao e agora le tambem o "rotation" do side data, cobrindo o
# caso da camera que grava na vertical sem girar o pixel. O que importa nao e
# se um patch aplicou, e se a funcao acerta, entao o validate.sh testa o
# comportamento com arquivos sinteticos.
if grep -q "stream_side_data=rotation" "$VIDEO_USE/helpers/render.py" 2>/dev/null; then
  echo "is_portrait_source: versao upstream com deteccao de rotacao"
else
  echo "AVISO: is_portrait_source sem deteccao de rotacao; rode scripts/validate.sh"
fi
if ! (cd "$VIDEO_USE" && uv sync) && ! (cd "$VIDEO_USE" && pip install -e .); then
  echo "AVISO: deps do video-use não instaladas (pypi.org bloqueado?). Ver 'Rede do environment' no CLAUDE.md."
fi
mkdir -p ~/.claude/skills
ln -sfn "$VIDEO_USE" ~/.claude/skills/video-use

echo "== 3/6 hyperframes + media-use =="
if [ ! -d "$HYPERFRAMES/.git" ]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/heygen-com/hyperframes "$HYPERFRAMES" || { echo "AVISO: clone do hyperframes falhou"; }
fi
# O `skills update` do hyperframes confere atualizacao contra um manifesto em
# raw.githubusercontent.com. Esse host costuma estar fora da allowlist do
# environment, e ai o comando recusa reportar sucesso mesmo com o npm liberado.
# O clone ja traz todas as skills em skills/<nome>/SKILL.md, entao o fallback e
# registra-las direto, sem depender da rede.
if ! npx --yes hyperframes skills update 2>/dev/null; then
  echo "hyperframes skills update indisponivel; registrando do clone local"
  mkdir -p ~/.claude/skills
  n=0
  for d in "$HYPERFRAMES"/skills/*/; do
    [ -f "$d/SKILL.md" ] || continue
    ln -sfn "${d%/}" ~/.claude/skills/"$(basename "$d")"
    n=$((n+1))
  done
  echo "$n skills do hyperframes registradas a partir de $HYPERFRAMES/skills"
fi

echo "== 4/6 Python (PIL para overlays, numpy para batidas) =="
python3 -c 'import PIL' 2>/dev/null || pip3 install pillow || echo "AVISO: pillow não instalado (pypi bloqueado). Lettering/overlays indisponíveis."
python3 -c 'import numpy' 2>/dev/null || pip3 install numpy || echo "AVISO: numpy não instalado (pypi bloqueado). Detecção de batidas indisponível."

echo "== 5/6 Remotion =="
# Remotion e por projeto (templates/remotion + scripts/new-remotion.sh), entao
# aqui so confirmamos que o registry responde e que ha Chrome para o render.
if npm view remotion version >/dev/null 2>&1; then
  echo "registry.npmjs.org OK (remotion $(npm view remotion version 2>/dev/null))"
else
  echo "AVISO: registry.npmjs.org inacessivel; Remotion e o CLI do hyperframes nao instalam."
fi
if [ -n "${CHROME_SHELL:-}" ]; then
  echo "Chrome para render: $CHROME_SHELL"
else
  echo "AVISO: headless shell nao encontrado em /opt/pw-browsers; render local indisponivel."
fi

echo "== 6/6 estúdio =="
ln -sfn "$REPO_ROOT" ~/normalyze-conteudo
echo "~/normalyze-conteudo -> $REPO_ROOT"

# Propaga a chave da ElevenLabs do environment para o .env do video-use.
if [ ! -f "$VIDEO_USE/.env" ] && [ -n "${ELEVENLABS_API_KEY:-}" ]; then
  printf 'ELEVENLABS_API_KEY=%s\n' "$ELEVENLABS_API_KEY" > "$VIDEO_USE/.env"
  chmod 600 "$VIDEO_USE/.env"
  echo "ELEVENLABS_API_KEY gravada em $VIDEO_USE/.env (a partir da env var)"
elif [ ! -f "$VIDEO_USE/.env" ]; then
  echo "PENDENTE: gravar ELEVENLABS_API_KEY em $VIDEO_USE/.env (peça ao usuário; chave sk_ de 51 chars)"
fi
echo "Setup concluído. Rode: bash $REPO_ROOT/scripts/validate.sh"
