#!/usr/bin/env python3
"""Sobe arquivos para uma pasta do Google Drive com um token de acesso.

Só depende de `www.googleapis.com`, que é o único host do Google liberado
neste environment. `oauth2.googleapis.com` e `accounts.google.com` estão
bloqueados, então **não dá para gerar o token aqui**: ele tem que ser gerado
fora e passado pronto (variável GOOGLE_OAUTH_TOKEN ou --token).

Como gerar, pelo navegador, em https://developers.google.com/oauthplayground:
  1. engrenagem > "Use your own OAuth credentials" é opcional
  2. escopo `https://www.googleapis.com/auth/drive.file`
     (esse escopo só enxerga arquivos criados pelo próprio app: é o mais
      estreito que serve, e não dá acesso ao resto do seu Drive)
  3. "Authorize APIs", depois "Exchange authorization code for tokens"
  4. copiar o `access_token`. Ele vale 1 hora.

Uso:
    GOOGLE_OAUTH_TOKEN=ya29.... python3 scripts/sobe_para_drive.py \
        --pasta <folder_id> finais/*.mp4
"""
import argparse
import json
import mimetypes
import os
import subprocess
import sys

BASE = "https://www.googleapis.com/upload/drive/v3/files"


def curl(args, entrada=None):
    r = subprocess.run(["curl", "-s", "--max-time", "1800", *args],
                       capture_output=True, text=True, input=entrada)
    return r.stdout


def sobe(caminho, pasta, token):
    """Upload resumable: aguenta arquivo grande e devolve erro legivel."""
    nome = os.path.basename(caminho)
    tipo = mimetypes.guess_type(nome)[0] or "application/octet-stream"
    tamanho = os.path.getsize(caminho)
    meta = json.dumps({"name": nome, "parents": [pasta]})

    # 1) abre a sessao e pega a URL de upload
    cab = curl([
        "-D", "-", "-o", "/dev/null",
        "-X", "POST", f"{BASE}?uploadType=resumable&supportsAllDrives=true",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json; charset=UTF-8",
        "-H", f"X-Upload-Content-Type: {tipo}",
        "-H", f"X-Upload-Content-Length: {tamanho}",
        "--data-binary", meta,
    ])
    url = ""
    for linha in cab.splitlines():
        if linha.lower().startswith("location:"):
            url = linha.split(":", 1)[1].strip()
    if not url:
        return None, f"não abriu a sessão de upload: {cab.strip()[:300]}"

    # 2) manda o conteudo
    saida = curl([
        "-X", "PUT", url,
        "-H", f"Content-Type: {tipo}",
        "-H", f"Content-Length: {tamanho}",
        "--upload-file", caminho,
    ])
    try:
        d = json.loads(saida)
    except Exception:
        return None, f"resposta inesperada: {saida.strip()[:300]}"
    if "id" not in d:
        return None, json.dumps(d)[:300]
    return d["id"], None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--pasta", required=True, help="id da pasta de destino")
    ap.add_argument("--token", default=os.environ.get("GOOGLE_OAUTH_TOKEN", ""))
    a = ap.parse_args()

    if not a.token:
        sys.exit("sem token: use --token ou a variável GOOGLE_OAUTH_TOKEN "
                 "(veja o cabeçalho deste arquivo para gerar)")

    ok = falhas = 0
    for c in a.arquivos:
        fid, erro = sobe(c, a.pasta, a.token)
        if fid:
            ok += 1
            print(f"OK   {os.path.basename(c)}  -> {fid}", flush=True)
        else:
            falhas += 1
            print(f"FALHA {os.path.basename(c)}: {erro}", flush=True)
    print(f"\n{ok} enviados, {falhas} falharam")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
