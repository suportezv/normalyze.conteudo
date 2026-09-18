#!/usr/bin/env python3
"""Decupa os brutos a partir de ancoras de texto na transcricao.

Cada trecho aproveitado e descrito por duas ancoras, o comeco e o fim da
fala, em vez de timecode na mao: o script casa as ancoras contra as palavras
da transcricao do Scribe e resolve os tempos exatos. Depois corta, junta os
trechos do mesmo clipe, roda o video para vertical, aplica a LUT de
S-Log2 para Rec.709 e normaliza o audio.

Uso: python3 scripts/decupar.py edl.json --brutos DIR --stt DIR --lut X.cube --saida DIR
"""
import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata

CABECA = 0.20   # respiro antes da primeira palavra
RABO = 0.45     # respiro depois da ultima palavra
MARGEM = 0.06   # distancia que se mantem da palavra vizinha


def normaliza(txt):
    """Baixa caixa, tira acento e pontuacao: o casamento nao pode depender disso."""
    txt = unicodedata.normalize("NFD", txt.lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return [t for t in re.split(r"[^a-z0-9]+", txt) if t]


def palavras(stt_path):
    d = json.load(open(stt_path, encoding="utf-8"))
    return [w for w in d.get("words", []) if w.get("type") == "word"]


def acha(seq_norm, alvo, inicio_em=0):
    """Acha a sequencia `alvo` em `seq_norm` a partir de inicio_em.

    Devolve (i, j) com o intervalo semiaberto de indices, ou None.
    """
    n = len(alvo)
    if not n:
        return None
    for i in range(inicio_em, len(seq_norm) - n + 1):
        if seq_norm[i:i + n] == alvo:
            return i, i + n
    return None


def resolve(w, trechos, clipe):
    """Converte as ancoras de texto de um clipe em pares (inicio, fim) em segundos."""
    # cada palavra do Scribe pode virar mais de um token depois de normalizar
    seq, dono = [], []
    for idx, x in enumerate(w):
        for tok in normaliza(x["text"]):
            seq.append(tok)
            dono.append(idx)

    tempos, cursor = [], 0
    for t in trechos:
        # "apos" empurra o cursor: serve quando a mesma frase aparece antes,
        # dita pela equipe fora de cena, e a boa e a de depois
        if t.get("apos"):
            salto = acha(seq, normaliza(t["apos"]), cursor)
            if salto is None:
                raise SystemExit(f"{clipe}: ancora 'apos' nao encontrada: {t['apos']!r}")
            cursor = salto[1]
        a = acha(seq, normaliza(t["de"]), cursor)
        if a is None:
            raise SystemExit(f"{clipe}: ancora inicial nao encontrada: {t['de']!r}")
        # busca o fim a partir do inicio do proprio trecho, para permitir que
        # a ancora final seja a mesma da inicial (trecho de uma frase so)
        b = acha(seq, normaliza(t["ate"]), a[0])
        if b is None:
            raise SystemExit(f"{clipe}: ancora final nao encontrada: {t['ate']!r}")
        # "cabeca"/"rabo" no trecho sobrescrevem o respiro padrao.
        i_pri, i_ult = dono[a[0]], dono[b[1] - 1]
        ini = w[i_pri]["start"] - float(t.get("cabeca", CABECA))
        fim = w[i_ult]["end"] + float(t.get("rabo", RABO))

        # O respiro nunca pode cruzar a palavra vizinha. Nestes brutos a
        # equipe fala colada no take ("Excelente", "Perfeito", "Então"), as
        # vezes a centesimos de segundo do fim da fala, e um respiro fixo
        # arrastaria essa palavra para dentro da peca entregue.
        #
        # Quando a folga ate a vizinha e menor que a margem, o corte vai para
        # o meio da folga: e o unico ponto que nao come a nossa ultima silaba
        # nem deixa entrar a primeira da outra. Nao ha respiro a ter quando
        # nao ha silencio, e forcar um minimo aqui reintroduziria a invasao.
        if i_pri > 0:
            folga = w[i_pri]["start"] - w[i_pri - 1]["end"]
            ini = max(ini, w[i_pri]["start"] - min(MARGEM, folga / 2))
        if i_ult + 1 < len(w):
            folga = w[i_ult + 1]["start"] - w[i_ult]["end"]
            fim = min(fim, w[i_ult]["end"] + min(MARGEM, folga / 2))
        tempos.append((max(0.0, ini), fim))
        cursor = b[1]
    return tempos


def duracao(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def renderiza(entrada, tempos, lut, destino, altura=1920, largura=1080, crf=18):
    total = duracao(entrada)
    partes, cadeia = [], []
    for k, (ini, fim) in enumerate(tempos):
        fim = min(fim, total)
        cadeia.append(f"[0:v]trim=start={ini:.3f}:end={fim:.3f},setpts=PTS-STARTPTS[v{k}]")
        cadeia.append(f"[0:a]atrim=start={ini:.3f}:end={fim:.3f},asetpts=PTS-STARTPTS[a{k}]")
        partes.append(f"[v{k}][a{k}]")

    if len(tempos) > 1:
        cadeia.append(f"{''.join(partes)}concat=n={len(tempos)}:v=1:a=1[vc][ac]")
        vsrc, asrc = "[vc]", "[ac]"
    else:
        vsrc, asrc = "[v0]", "[a0]"

    # transpose=1 gira 90 graus no sentido horario: o bruto foi filmado de lado
    cadeia.append(
        # a LUT roda em RGB de faixa cheia (o ffmpeg converte sozinho, e o
        # S-Log2 da camera de fato ocupa a escala inteira). Na saida voltamos
        # para YUV de faixa limitada, que e o padrao de entrega em H.264.
        f"{vsrc}transpose=1,lut3d=file={lut}:interp=tetrahedral,"
        f"scale={largura}:{altura}:flags=lanczos:out_range=tv,format=yuv420p[vout]"
    )
    cadeia.append(f"{asrc}loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    cmd = [
        "ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", entrada,
        "-filter_complex", ";".join(cadeia),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-color_range", "tv",
        "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        destino,
    ]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("--brutos", default="brutos")
    ap.add_argument("--stt", default="stt")
    ap.add_argument("--lut", required=True)
    ap.add_argument("--saida", default="finais")
    ap.add_argument("--so", default=None,
                    help="renderiza so estes clipes (lista separada por virgula)")
    a = ap.parse_args()

    edl = json.load(open(a.edl, encoding="utf-8"))
    filtro = set(a.so.split(",")) if a.so else None
    os.makedirs(a.saida, exist_ok=True)
    relatorio = []

    for clipe, spec in sorted(edl.items()):
        if filtro and clipe not in filtro:
            continue
        if not spec.get("trechos"):
            relatorio.append((clipe, spec.get("pessoa", "?"), None, spec.get("nota", "descartado")))
            continue

        w = palavras(os.path.join(a.stt, f"{clipe}.json"))
        tempos = resolve(w, spec["trechos"], clipe)
        nome = spec.get("arquivo") or f"{clipe}.mp4"
        destino = os.path.join(a.saida, nome)
        renderiza(os.path.join(a.brutos, f"{clipe}.MP4"), tempos, a.lut, destino)
        dur = duracao(destino)
        relatorio.append((clipe, spec.get("pessoa", "?"), dur, nome))
        print(f"{clipe}  {spec.get('pessoa','?'):22} {dur:5.1f}s  -> {nome}", flush=True)

    print("\n--- descartados ---")
    for c, p, d, n in relatorio:
        if d is None:
            print(f"{c}  {p:22} {n}")


if __name__ == "__main__":
    main()
