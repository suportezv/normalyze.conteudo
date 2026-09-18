#!/usr/bin/env bash
# Cria um projeto Remotion a partir do template do estudio.
#   bash scripts/new-remotion.sh <nome-do-projeto>
# Resultado: projects/<nome>/remotion/ pronto para `npm run render`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/scripts/env.sh"

NOME="${1:-}"
[ -n "$NOME" ] || { echo "uso: bash scripts/new-remotion.sh <nome-do-projeto>"; exit 1; }

DEST="$REPO_ROOT/projects/$NOME/remotion"
[ -e "$DEST" ] && { echo "ja existe: $DEST"; exit 1; }

mkdir -p "$DEST"
cp -r "$REPO_ROOT/templates/remotion/." "$DEST/"
cd "$DEST"
npm install --no-audit --no-fund

cat <<EOF

Projeto criado em projects/$NOME/remotion

  source scripts/env.sh                 # sempre antes de npm/npx neste container
  cd projects/$NOME/remotion
  npm run render                        # -> out/video.mp4 (1080x1920, 30fps)
  npm run studio                        # preview interativo

Edite src/Main.tsx para a peca e src/Root.tsx para duracao e formato.
EOF
