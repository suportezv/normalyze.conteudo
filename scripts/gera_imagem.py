#!/usr/bin/env python3
"""Gera imagem pela OpenAI ou pelo Gemini, com a mesma interface.

As chaves vem das variaveis de ambiente OPENAI_API_KEY e GEMINI_API_KEY.
Nenhuma chave e aceita por argumento: linha de comando vaza em historico e
em lista de processos.

Uso:
    python3 scripts/gera_imagem.py openai "um gato de oculos" saida.png
    python3 scripts/gera_imagem.py gemini "um gato de oculos" saida.png --modelo gemini-3-pro-image
    python3 scripts/gera_imagem.py --listar
"""
import argparse
import base64
import json
import os
import subprocess
import sys

OPENAI_URL = "https://api.openai.com/v1/images/generations"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

PADRAO = {"openai": "gpt-image-2", "gemini": "gemini-3-pro-image"}


def _post(url, cabecalhos, corpo):
    cmd = ["curl", "-s", "--max-time", "600", "-X", "POST", url]
    for k, v in cabecalhos.items():
        cmd += ["-H", f"{k}: {v}"]
    cmd += ["-H", "Content-Type: application/json", "--data-binary", "@-"]
    r = subprocess.run(cmd, input=json.dumps(corpo), capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"_bruto": r.stdout[:500], "_erro_curl": r.stderr[:300]}


def chave(nome):
    v = os.environ.get(nome, "")
    if not v:
        sys.exit(f"{nome} ausente no ambiente. Cadastre nas variaveis do environment.")
    return v


def openai_imagem(prompt, modelo, tamanho, qualidade):
    d = _post(
        OPENAI_URL,
        {"Authorization": f"Bearer {chave('OPENAI_API_KEY')}"},
        {"model": modelo, "prompt": prompt, "size": tamanho,
         "quality": qualidade, "n": 1},
    )
    if "error" in d:
        return None, d["error"].get("message", str(d["error"]))[:300]
    dados = (d.get("data") or [{}])[0]
    if dados.get("b64_json"):
        return base64.b64decode(dados["b64_json"]), None
    if dados.get("url"):  # modelos antigos devolvem URL em vez de base64
        r = subprocess.run(["curl", "-sL", "--max-time", "300", dados["url"]],
                           capture_output=True)
        return r.stdout, None
    return None, json.dumps(d)[:300]


def gemini_imagem(prompt, modelo):
    d = _post(
        GEMINI_URL.format(modelo=modelo),
        {"x-goog-api-key": chave("GEMINI_API_KEY")},
        {"contents": [{"parts": [{"text": prompt}]}]},
    )
    if "error" in d:
        return None, f"{d['error'].get('code')}: {str(d['error'].get('message'))[:300]}"
    for cand in d.get("candidates", []):
        for parte in cand.get("content", {}).get("parts", []):
            dados = parte.get("inlineData") or parte.get("inline_data")
            if dados and dados.get("data"):
                return base64.b64decode(dados["data"]), None
    return None, json.dumps(d)[:400]


def listar():
    """Lista os modelos de imagem que cada conta enxerga hoje."""
    r = subprocess.run(["curl", "-s", "--max-time", "60",
                        "https://api.openai.com/v1/models",
                        "-H", f"Authorization: Bearer {chave('OPENAI_API_KEY')}"],
                       capture_output=True, text=True)
    ids = sorted(m["id"] for m in json.loads(r.stdout).get("data", []))
    print("OpenAI:", ", ".join(i for i in ids if "image" in i) or "nenhum")

    r = subprocess.run(["curl", "-s", "--max-time", "60",
                        "https://generativelanguage.googleapis.com/v1beta/models",
                        "-H", f"x-goog-api-key: {chave('GEMINI_API_KEY')}"],
                       capture_output=True, text=True)
    ms = [m["name"].split("/")[-1] for m in json.loads(r.stdout).get("models", [])]
    print("Gemini:", ", ".join(m for m in ms if "image" in m) or "nenhum")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("provedor", nargs="?", choices=["openai", "gemini"])
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("destino", nargs="?")
    ap.add_argument("--modelo", default=None)
    ap.add_argument("--tamanho", default="1024x1024", help="so OpenAI")
    ap.add_argument("--qualidade", default="high", help="so OpenAI")
    ap.add_argument("--listar", action="store_true", help="lista modelos e sai")
    a = ap.parse_args()

    if a.listar:
        listar()
        return
    if not (a.provedor and a.prompt and a.destino):
        ap.error("informe provedor, prompt e destino (ou use --listar)")

    modelo = a.modelo or PADRAO[a.provedor]
    if a.provedor == "openai":
        img, erro = openai_imagem(a.prompt, modelo, a.tamanho, a.qualidade)
    else:
        img, erro = gemini_imagem(a.prompt, modelo)

    if erro:
        sys.exit(f"falhou ({a.provedor}/{modelo}): {erro}")
    with open(a.destino, "wb") as fh:
        fh.write(img)
    print(f"{a.destino}  {len(img)/1000:.0f} KB  ({a.provedor}/{modelo})")


if __name__ == "__main__":
    main()
