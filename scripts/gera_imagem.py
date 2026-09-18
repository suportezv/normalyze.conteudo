#!/usr/bin/env python3
"""Gera imagens de post para a Normalyze.ai a partir dos presets de formato da marca.

Backends:
  gemini (padrao) - Gemini image models via GEMINI_API_KEY
  openai          - gpt-image via OPENAI_API_KEY

Somente biblioteca padrao: nada para instalar. Usa o proxy e o CA bundle do
ambiente automaticamente (variaveis HTTPS_PROXY / SSL_CERT_FILE).

Exemplos:
  python3 scripts/gera_imagem.py --listar
  python3 scripts/gera_imagem.py -p story -t "tela de dashboard flutuando, luz suave"
  python3 scripts/gera_imagem.py -p feed -t "..." --backend openai --n 3
"""

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTILO_JSON = os.path.join(RAIZ, "assets", "marca", "estilo.json")
SAIDA_PADRAO = os.path.join("projects", "imagens")

MODELO_PADRAO = {"gemini": "gemini-3-pro-image", "openai": "gpt-image-2"}

# Fallback usado quando a API de modelos nao responde.
MODELOS_CONHECIDOS = {
    "gemini": [
        "gemini-3-pro-image",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-lite-image",
        "gemini-2.5-flash-image",
    ],
    "openai": ["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"],
}

# proporcao = a que o preset realmente pede; openai_size = tamanho suportado mais proximo.
PRESETS = {
    "feed": {
        "proporcao": "1:1",
        "gemini_ar": "1:1",
        "openai_size": "1024x1024",
        "descricao": "Post quadrado de feed (Instagram, Facebook)",
        "composicao": "enquadramento quadrado equilibrado, sujeito centralizado, margens generosas",
    },
    "feed-retrato": {
        "proporcao": "4:5",
        "gemini_ar": "4:5",
        "openai_size": "1024x1536",
        "descricao": "Post vertical de feed (mais area na timeline)",
        "composicao": "enquadramento vertical, sujeito no terco superior, espaco limpo embaixo para texto",
    },
    "story": {
        "proporcao": "9:16",
        "gemini_ar": "9:16",
        "openai_size": "1024x1536",
        "descricao": "Story do Instagram e do Facebook",
        "composicao": "vertical cheio, elemento principal no centro vertical, 15% livres no topo e embaixo (area segura da interface)",
    },
    "capa-reel": {
        "proporcao": "9:16",
        "gemini_ar": "9:16",
        "openai_size": "1024x1536",
        "descricao": "Capa de Reel, TikTok ou Short do YouTube",
        "composicao": "vertical cheio, leitura imediata em miniatura, alto contraste, centro da imagem livre para o lettering do hook",
    },
    "linkedin": {
        "proporcao": "16:9",
        "gemini_ar": "16:9",
        "openai_size": "1536x1024",
        "descricao": "Imagem de post no LinkedIn",
        "composicao": "horizontal sobrio, composicao limpa, adequado a contexto profissional",
    },
    "youtube-thumb": {
        "proporcao": "16:9",
        "gemini_ar": "16:9",
        "openai_size": "1536x1024",
        "descricao": "Thumbnail do YouTube",
        "composicao": "horizontal, sujeito grande e legivel em miniatura pequena, alto contraste, fundo simples",
    },
    "og": {
        "proporcao": "16:9",
        "gemini_ar": "16:9",
        "openai_size": "1536x1024",
        "descricao": "Capa de blog / imagem open graph",
        "composicao": "horizontal, composicao editorial, espaco lateral livre para titulo",
    },
}

# A identidade visual da Normalyze ainda esta "a definir" no FRAMEWORK.md.
# Ate a equipe aprovar, o script usa esta base neutra e avisa em toda execucao.
ESTILO_PADRAO = {
    "marca": "Normalyze.ai",
    "estilo_visual": "visual limpo e moderno de produto digital, luz suave e difusa, "
    "superficies foscas, profundidade sutil, sem excesso de elementos",
    "paleta": ["azul profundo", "cinza claro", "branco"],
    "acento": "a definir com a equipe",
    "evitar": [
        "texto ilegivel ou embaralhado",
        "logotipos ou marcas de terceiros",
        "estetica de banco de imagens generico",
        "pessoas em poses artificiais de stock",
    ],
    "_pendente": True,
}

REGRAS_FIXAS = (
    "Se houver qualquer texto na imagem, escreva em portugues do Brasil, "
    "curto e legivel, e nunca use travessao. "
    "Nao invente logotipo, nome de produto nem numeros de resultado."
)


def carrega_estilo():
    """Le assets/marca/estilo.json quando existir; senao usa a base neutra."""
    if os.path.exists(ESTILO_JSON):
        try:
            with open(ESTILO_JSON, encoding="utf-8") as fh:
                estilo = json.load(fh)
            estilo.setdefault("_pendente", False)
            return estilo
        except (OSError, ValueError) as erro:
            print(f"aviso: {ESTILO_JSON} ilegivel ({erro}); usando o estilo neutro.",
                  file=sys.stderr)
    return dict(ESTILO_PADRAO)


def monta_prompt(preset, texto, estilo, aplicar_estilo=True):
    texto = texto.strip()
    if texto and texto[-1] not in ".!?":
        texto += "."
    partes = [texto]
    partes.append(f"Composicao: {preset['composicao']}, proporcao {preset['proporcao']}.")
    if aplicar_estilo:
        visual = [estilo.get("estilo_visual", "")]
        paleta = estilo.get("paleta") or []
        if paleta:
            visual.append("paleta: " + ", ".join(paleta))
        acento = estilo.get("acento")
        if acento and "definir" not in str(acento).lower():
            visual.append(f"cor de acento: {acento}")
        partes.append("Estilo da marca: " + "; ".join(p for p in visual if p) + ".")
        evitar = estilo.get("evitar") or []
        if evitar:
            partes.append("Evitar: " + ", ".join(evitar) + ".")
    partes.append(REGRAS_FIXAS)
    return " ".join(partes)


def slug(texto, limite=40):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return (texto[:limite].rstrip("-")) or "imagem"


def pede_json(url, corpo, cabecalhos, timeout):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode("utf-8"),
                                 headers=cabecalhos, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def erro_http(erro):
    try:
        detalhe = json.loads(erro.read().decode("utf-8"))
        return detalhe.get("error", {}).get("message", str(detalhe))[:500]
    except Exception:
        return f"HTTP {erro.code}"


def le_referencias(caminhos):
    partes = []
    for caminho in caminhos:
        ext = os.path.splitext(caminho)[1].lower()
        mime = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
        with open(caminho, "rb") as fh:
            partes.append({"inlineData": {"mimeType": mime,
                                          "data": base64.b64encode(fh.read()).decode()}})
    return partes


def gera_gemini(prompt, preset, modelo, n, refs, timeout):
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        raise SystemExit("erro: GEMINI_API_KEY nao esta no ambiente.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    cabecalhos = {"Content-Type": "application/json", "x-goog-api-key": chave}
    imagens = []
    # A API de imagem do Gemini devolve uma imagem por chamada.
    for _ in range(n):
        partes = le_referencias(refs) + [{"text": prompt}]
        corpo = {
            "contents": [{"parts": partes}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": preset["gemini_ar"]},
            },
        }
        try:
            resposta = pede_json(url, corpo, cabecalhos, timeout)
        except urllib.error.HTTPError as erro:
            msg = erro_http(erro)
            if erro.code == 429:
                raise SystemExit(
                    "erro: a chave GEMINI_API_KEY nao tem cota para modelos de imagem "
                    f"(429). Ative o faturamento em ai.google.dev ou rode com "
                    f"--backend openai.\ndetalhe: {msg}")
            raise SystemExit(f"erro Gemini ({erro.code}): {msg}")
        for cand in resposta.get("candidates", []):
            for parte in cand.get("content", {}).get("parts", []):
                dados = parte.get("inlineData") or parte.get("inline_data")
                if dados:
                    imagens.append(base64.b64decode(dados["data"]))
                elif parte.get("text"):
                    print(f"modelo respondeu em texto: {parte['text'][:200]}", file=sys.stderr)
    return imagens


def gera_openai(prompt, preset, modelo, n, qualidade, timeout):
    chave = os.environ.get("OPENAI_API_KEY")
    if not chave:
        raise SystemExit("erro: OPENAI_API_KEY nao esta no ambiente.")
    corpo = {"model": modelo, "prompt": prompt, "size": preset["openai_size"],
             "quality": qualidade, "n": n}
    cabecalhos = {"Content-Type": "application/json", "Authorization": f"Bearer {chave}"}
    try:
        resposta = pede_json("https://api.openai.com/v1/images/generations",
                             corpo, cabecalhos, timeout)
    except urllib.error.HTTPError as erro:
        raise SystemExit(f"erro OpenAI ({erro.code}): {erro_http(erro)}")
    return [base64.b64decode(item["b64_json"]) for item in resposta.get("data", [])]


def modelos_vivos(backend, timeout=20):
    """Lista os modelos de imagem direto da API; devolve None se nao der."""
    try:
        if backend == "gemini":
            chave = os.environ.get("GEMINI_API_KEY")
            if not chave:
                return None
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={chave}&pageSize=200"
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                dados = json.loads(resp.read().decode("utf-8"))
            nomes = [m["name"].split("/")[-1] for m in dados.get("models", [])]
            return sorted(n for n in nomes if "image" in n)
        chave = os.environ.get("OPENAI_API_KEY")
        if not chave:
            return None
        req = urllib.request.Request("https://api.openai.com/v1/models",
                                     headers={"Authorization": f"Bearer {chave}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
        return sorted(m["id"] for m in dados.get("data", []) if "image" in m["id"])
    except Exception:
        return None


def lista(args):
    estilo = carrega_estilo()
    print("PRESETS DE FORMATO (Normalyze.ai)\n")
    cab = f"{'preset':<14} {'proporcao':<10} {'openai':<11} descricao"
    print(cab)
    print("-" * max(len(cab), 72))
    for nome, p in PRESETS.items():
        print(f"{nome:<14} {p['proporcao']:<10} {p['openai_size']:<11} {p['descricao']}")
    print("\nO backend openai so aceita 1024x1024, 1024x1536 e 1536x1024:")
    print("  4:5 e 9:16 saem como 2:3 e 16:9 sai como 3:2. O backend gemini respeita a proporcao exata.")

    for backend in ("gemini", "openai"):
        vivos = modelos_vivos(backend)
        origem = "da API" if vivos is not None else "conhecidos (API fora de alcance)"
        modelos = vivos if vivos else MODELOS_CONHECIDOS[backend]
        chave = "GEMINI_API_KEY" if backend == "gemini" else "OPENAI_API_KEY"
        estado = "configurada" if os.environ.get(chave) else "AUSENTE"
        print(f"\nMODELOS {backend.upper()} ({origem}) | {chave}: {estado}")
        for m in modelos:
            print(f"  {m}{'   <- padrao' if m == MODELO_PADRAO[backend] else ''}")

    print("\nESTILO DA MARCA")
    if estilo.get("_pendente"):
        print("  base neutra (identidade ainda a definir no FRAMEWORK.md)")
        print(f"  para fixar: crie {os.path.relpath(ESTILO_JSON, RAIZ)}")
    else:
        print(f"  {os.path.relpath(ESTILO_JSON, RAIZ)}")
    print(f"  estilo_visual: {estilo.get('estilo_visual', '')}")
    print(f"  paleta: {', '.join(estilo.get('paleta') or []) or '-'}")
    print(f"  acento: {estilo.get('acento', '-')}")
    return 0


def gerar(args):
    preset = PRESETS[args.preset]
    estilo = carrega_estilo()
    if estilo.get("_pendente") and not args.sem_estilo:
        print("aviso: identidade visual da Normalyze ainda a definir; usando o estilo neutro "
              "(veja FRAMEWORK.md).", file=sys.stderr)
    prompt = monta_prompt(preset, args.prompt, estilo, aplicar_estilo=not args.sem_estilo)
    modelo = args.modelo or MODELO_PADRAO[args.backend]

    if args.backend == "gemini":
        imagens = gera_gemini(prompt, preset, modelo, args.n, args.ref, args.timeout)
    else:
        if args.ref:
            raise SystemExit("erro: --ref so funciona no backend gemini.")
        imagens = gera_openai(prompt, preset, modelo, args.n, args.qualidade, args.timeout)

    if not imagens:
        raise SystemExit("erro: o modelo nao devolveu nenhuma imagem.")

    os.makedirs(args.saida, exist_ok=True)
    carimbo = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"{args.preset}_{slug(args.prompt)}_{carimbo}"
    caminhos = []
    for i, dados in enumerate(imagens, 1):
        sufixo = f"_{i}" if len(imagens) > 1 else ""
        caminho = os.path.join(args.saida, f"{base}{sufixo}.png")
        with open(caminho, "wb") as fh:
            fh.write(dados)
        caminhos.append(caminho)

    if args.json:
        print(json.dumps({"preset": args.preset, "backend": args.backend, "modelo": modelo,
                          "prompt_final": prompt, "arquivos": caminhos},
                         ensure_ascii=False, indent=2))
    else:
        for caminho in caminhos:
            tamanho = os.path.getsize(caminho) // 1024
            print(f"ok  {caminho}  ({tamanho} KB)")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Gera imagens de post da Normalyze.ai a partir dos presets de formato.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="exemplos:\n"
               "  %(prog)s --listar\n"
               "  %(prog)s -p story -t \"dashboard flutuando sobre fundo azul\"\n"
               "  %(prog)s -p feed -t \"...\" --backend openai --n 3\n")
    ap.add_argument("--listar", "-l", action="store_true",
                    help="lista presets, modelos disponiveis e o estilo da marca")
    ap.add_argument("--preset", "-p", choices=sorted(PRESETS), help="formato do post")
    ap.add_argument("--prompt", "-t", help="descricao da imagem, em portugues")
    ap.add_argument("--backend", "-b", choices=("gemini", "openai"), default="gemini",
                    help="provedor de geracao (padrao: gemini)")
    ap.add_argument("--modelo", "-m", help="modelo especifico (padrao por backend)")
    ap.add_argument("--n", type=int, default=1, help="quantas imagens gerar (padrao: 1)")
    ap.add_argument("--ref", action="append", default=[], metavar="ARQUIVO",
                    help="imagem de referencia, repetivel (so no backend gemini)")
    ap.add_argument("--qualidade", choices=("low", "medium", "high", "auto"), default="high",
                    help="qualidade no backend openai (padrao: high)")
    ap.add_argument("--saida", "-o", default=SAIDA_PADRAO,
                    help=f"pasta de saida (padrao: {SAIDA_PADRAO})")
    ap.add_argument("--sem-estilo", action="store_true",
                    help="nao anexar a camada de estilo da marca ao prompt")
    ap.add_argument("--json", action="store_true", help="saida em JSON, com o prompt final")
    ap.add_argument("--timeout", type=int, default=300, help="timeout por chamada, em segundos")
    args = ap.parse_args()

    if args.listar:
        return lista(args)
    if not args.preset or not args.prompt:
        ap.error("informe --preset e --prompt, ou use --listar")
    if args.n < 1:
        ap.error("--n precisa ser 1 ou mais")
    for caminho in args.ref:
        if not os.path.isfile(caminho):
            ap.error(f"referencia nao encontrada: {caminho}")
    return gerar(args)


if __name__ == "__main__":
    sys.exit(main())
