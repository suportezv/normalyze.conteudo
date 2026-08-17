#!/usr/bin/env bash
# Setup do Normalyze Conteúdo Studio (Linux/cloud). No Mac, siga SETUP.md manualmente.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="${TOOLS_DIR:-/workspace}"
VIDEO_USE="$TOOLS_DIR/browser-use/video-use"
HYPERFRAMES="$TOOLS_DIR/heygen-com/hyperframes"

echo "== 1/5 ffmpeg =="
if ! command -v ffmpeg >/dev/null; then
  apt-get update -qq && apt-get install -y -qq ffmpeg fonts-liberation
fi
ffmpeg -version | head -1

echo "== 2/5 video-use =="
if [ ! -d "$VIDEO_USE/.git" ]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/browser-use/video-use "$VIDEO_USE"
fi
if git -C "$VIDEO_USE" apply --check "$REPO_ROOT/patches/video-use-is-portrait-source.patch" 2>/dev/null; then
  git -C "$VIDEO_USE" apply "$REPO_ROOT/patches/video-use-is-portrait-source.patch"
  echo "patch is_portrait_source aplicado"
else
  echo "patch is_portrait_source: já aplicado ou não aplicável (verifique manualmente)"
fi
(cd "$VIDEO_USE" && uv sync) || (cd "$VIDEO_USE" && pip install -e .)
mkdir -p ~/.claude/skills
ln -sfn "$VIDEO_USE" ~/.claude/skills/video-use

echo "== 3/5 hyperframes + media-use =="
if [ ! -d "$HYPERFRAMES/.git" ]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/heygen-com/hyperframes "$HYPERFRAMES"
fi
npx --yes hyperframes skills update

echo "== 4/5 Python (PIL para overlays, numpy para batidas) =="
python3 -c 'import PIL' 2>/dev/null || pip3 install pillow
python3 -c 'import numpy' 2>/dev/null || pip3 install numpy

echo "== 5/5 estúdio =="
ln -sfn "$REPO_ROOT" ~/normalyze-conteudo
echo "~/normalyze-conteudo -> $REPO_ROOT"

if [ ! -f "$VIDEO_USE/.env" ]; then
  echo "PENDENTE: gravar ELEVENLABS_API_KEY em $VIDEO_USE/.env (peça ao usuário; chave sk_ de 51 chars)"
fi
echo "Setup concluído. Rode: bash $REPO_ROOT/scripts/validate.sh"
