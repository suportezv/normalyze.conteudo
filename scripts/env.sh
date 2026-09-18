#!/usr/bin/env bash
# Prelúdio de rede para o estúdio na nuvem. Use com `source scripts/env.sh`
# antes de qualquer npm, npx, pip ou uv.
#
# Por que isto existe: o container traz npm_config_noproxy (e no_proxy) com
# registry.npmjs.org, pypi.org e files.pythonhosted.org na lista. Esses hosts
# então CONTORNAM o agent proxy e batem direto no firewall de egresso, que
# responde 403 mesmo com o domínio liberado no environment. Roteando pelo
# agent proxy os mesmos hosts respondem 200. Sem este source, `npx` falha com
# "403 Forbidden - GET https://registry.npmjs.org/<pacote>".

if [ -n "${HTTPS_PROXY:-}" ]; then
  export no_proxy="" NO_PROXY="" HTTP_PROXY="$HTTPS_PROXY"
  export SSL_CERT_FILE="${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}"
  export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
  export NODE_EXTRA_CA_CERTS="${NODE_EXTRA_CA_CERTS:-$SSL_CERT_FILE}"
  export UV_DEFAULT_INDEX="https://pypi.org/simple"
  export npm_config_proxy="$HTTPS_PROXY" npm_config_https_proxy="$HTTPS_PROXY"
  export npm_config_noproxy="" npm_config_cafile="$SSL_CERT_FILE"
fi

# Chrome para render local. O container já traz o headless shell do Playwright,
# então nem o Remotion nem o hyperframes precisam baixar browser (os hosts de
# download, remotion.media entre eles, não estão no allowlist).
CHROME_SHELL="$(find /opt/pw-browsers -maxdepth 3 -type f -name headless_shell 2>/dev/null | head -1)"
if [ -n "$CHROME_SHELL" ]; then
  export CHROME_SHELL
  # Remotion lê esta env var; para a CLI, passe também --browser-executable.
  export REMOTION_BROWSER_EXECUTABLE="$CHROME_SHELL"
  export PUPPETEER_EXECUTABLE_PATH="$CHROME_SHELL"
  export PUPPETEER_SKIP_DOWNLOAD=1
  # hyperframes: sem esta var o `browser ensure` fica preso em "Looking for an
  # existing browser" e o render local nao sai.
  export HYPERFRAMES_BROWSER_PATH="$CHROME_SHELL"
fi
