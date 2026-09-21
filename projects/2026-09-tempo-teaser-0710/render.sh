#!/usr/bin/env bash
# Renderiza comunicado.html em PNG (2x e 1x) com o headless shell do container.
set -euo pipefail
cd "$(dirname "$0")"
CH="${CHROME_SHELL:-$(find /opt/pw-browsers -maxdepth 3 -type f -name headless_shell | head -1)}"
mkdir -p out
"$CH" --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1080,1350 \
  --force-device-scale-factor=2 --virtual-time-budget=5000 \
  --screenshot="$PWD/out/comunicado@2x.png" "file://$PWD/comunicado.html" 2>/dev/null
python3 -c "
from PIL import Image
Image.open('out/comunicado@2x.png').convert('RGB').resize((1080,1350), Image.LANCZOS).save('out/comunicado.png')"
echo "out/comunicado.png (1080x1350) e out/comunicado@2x.png (2160x2700)"
