#!/usr/bin/env python3
"""Conexao com OpenAI e Gemini para o Normalyze Conteudo Studio.

Uso:
    python3 scripts/llm.py "escreva 3 ganchos para um reel sobre X"
    python3 scripts/llm.py --provider gemini "mesma coisa"
    python3 scripts/llm.py --provider openai --model gpt-5.4-mini "prompt"
    python3 scripts/llm.py --list                 # modelos vivos dos dois
    python3 scripts/llm.py --check                # so testa as duas conexoes

As chaves vem das env vars OPENAI_API_KEY e GEMINI_API_KEY, que o environment
injeta. Nunca commitar chave neste repo.

So usa stdlib de proposito: o estudio ja depende de rede liberada por dominio,
e um SDK a mais e uma versao a mais para quebrar em container novo.
"""

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request

# Defaults. Trocar aqui quando a equipe padronizar outro.
# Gemini: prefira os aliases "-latest"; model id fixo antigo e aposentado e
# devolve 404 com a sugestao do substituto no corpo do erro.
DEFAULTS = {"openai": "gpt-5.5", "gemini": "gemini-flash-latest"}

OPENAI_BASE = "https://api.openai.com/v1"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _opener():
    """urlopen que respeita o agent proxy e o CA bundle do container.

    Sem isto, em cloud com network Custom a chamada sai direto e leva 403 do
    firewall de egresso mesmo com o dominio liberado no environment.
    """
    handlers = []
    ca = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
    ctx = ssl.create_default_context(cafile=ca) if os.path.exists(ca) else ssl.create_default_context()
    handlers.append(urllib.request.HTTPSHandler(context=ctx))
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"https": proxy, "http": proxy}))
    return urllib.request.build_opener(*handlers)


def _request(url, headers, payload=None, timeout=180):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data else "GET")
    try:
        with _opener().open(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:600]
        raise SystemExit(f"[{e.code}] {url}\n{body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"rede indisponivel para {url}: {e.reason}\n"
                         f"Rode `source scripts/env.sh` e confira o allowlist do environment.")


def _key(name, provider):
    k = os.environ.get(name)
    if not k:
        raise SystemExit(f"{name} ausente no ambiente (provider {provider}).")
    return k


def openai_generate(prompt, model, system=None):
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    # Os modelos novos recusam max_tokens e querem max_completion_tokens; como
    # nao precisamos de teto aqui, simplesmente nao mandamos nenhum dos dois.
    out = _request(f"{OPENAI_BASE}/chat/completions",
                   {"Authorization": f"Bearer {_key('OPENAI_API_KEY', 'openai')}",
                    "Content-Type": "application/json"},
                   {"model": model, "messages": msgs})
    return out["choices"][0]["message"]["content"]


def gemini_generate(prompt, model, system=None):
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    out = _request(f"{GEMINI_BASE}/models/{model}:generateContent",
                   {"x-goog-api-key": _key("GEMINI_API_KEY", "gemini"),
                    "Content-Type": "application/json"},
                   payload)
    parts = out["candidates"][0]["content"]["parts"]
    # Modelos com "thinking" devolvem partes sem texto; junte so as que tem.
    return "".join(p["text"] for p in parts if "text" in p)


def list_models():
    o = _request(f"{OPENAI_BASE}/models",
                 {"Authorization": f"Bearer {_key('OPENAI_API_KEY', 'openai')}"})
    print("OpenAI:")
    for i in sorted(m["id"] for m in o["data"]):
        print(f"  {i}")
    g = _request(f"{GEMINI_BASE}/models",
                 {"x-goog-api-key": _key("GEMINI_API_KEY", "gemini")})
    print("\nGemini:")
    for m in g.get("models", []):
        print(f"  {m['name'].removeprefix('models/')}")


def check():
    ok = True
    for provider, fn in (("openai", openai_generate), ("gemini", gemini_generate)):
        model = DEFAULTS[provider]
        try:
            r = fn("Responda apenas: ok", model)
            print(f"OK   {provider:7} {model:22} -> {r.strip()[:40]!r}")
        except SystemExit as e:
            ok = False
            print(f"FALHOU {provider:7} {model:22} -> {str(e).splitlines()[0]}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?", help="o prompt")
    ap.add_argument("--provider", choices=["openai", "gemini"], default="openai")
    ap.add_argument("--model", help=f"default: {DEFAULTS}")
    ap.add_argument("--system", help="instrucao de sistema (ex.: tom de voz da marca)")
    ap.add_argument("--list", action="store_true", help="lista os modelos vivos")
    ap.add_argument("--check", action="store_true", help="testa as duas conexoes")
    a = ap.parse_args()

    if a.list:
        list_models()
        return 0
    if a.check:
        return check()
    if not a.prompt:
        ap.error("informe um prompt (ou --list / --check)")

    model = a.model or DEFAULTS[a.provider]
    fn = openai_generate if a.provider == "openai" else gemini_generate
    print(fn(a.prompt, model, a.system))
    return 0


if __name__ == "__main__":
    sys.exit(main())
