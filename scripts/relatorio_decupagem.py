#!/usr/bin/env python3
"""Monta o relatorio da decupagem: o que ficou, o que caiu e por que.

Le o EDL, os brutos e os finais ja renderizados, e transcreve o resultado
final de cada peca para provar que a fala aproveitada sobreviveu inteira.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decupar as D


def transcreve(mp3, chave):
    r = subprocess.run([
        "curl", "-s", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text",
        "-H", f"xi-api-key: {chave}", "-F", f"file=@{mp3}",
        "-F", "model_id=scribe_v1", "-F", "language_code=por",
    ], capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("text", "").strip()
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("--brutos", default="brutos")
    ap.add_argument("--finais", default="finais")
    ap.add_argument("--destino", default="RELATORIO.md")
    ap.add_argument("--sem-transcricao", action="store_true")
    a = ap.parse_args()

    chave = os.environ.get("ELEVENLABS_API_KEY", "")
    edl = json.load(open(a.edl, encoding="utf-8"))

    usados, caidos = [], []
    seg_bruto = seg_final = 0.0

    for clipe, spec in sorted(edl.items()):
        bruto = os.path.join(a.brutos, f"{clipe}.MP4")
        db = D.duracao(bruto) if os.path.exists(bruto) else 0.0
        seg_bruto += db
        if not spec.get("trechos"):
            caidos.append((clipe, spec.get("pessoa", "?"), db, spec.get("nota", "")))
            continue
        nome = spec.get("arquivo") or f"{clipe}.mp4"
        final = os.path.join(a.finais, nome)
        df = D.duracao(final) if os.path.exists(final) else 0.0
        seg_final += df
        texto = ""
        if df and not a.sem_transcricao and chave:
            mp3 = f"/tmp/_rel_{clipe}.mp3"
            subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", final,
                            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame",
                            "-q:a", "4", "-y", mp3], check=True)
            texto = transcreve(mp3, chave)
            os.remove(mp3)
        usados.append((clipe, spec.get("pessoa", "?"), db, df, nome,
                       len(spec["trechos"]), texto))

    with open(a.destino, "w", encoding="utf-8") as fh:
        fh.write("# Relatório da decupagem\n\n")
        fh.write(f"**{len(usados) + len(caidos)} clipes brutos** "
                 f"({seg_bruto/60:.1f} min) geraram **{len(usados)} peças finais** "
                 f"({seg_final/60:.1f} min).\n\n")
        fh.write("## Aproveitados\n\n")
        fh.write("| Clipe | Pessoa | Bruto | Final | Trechos | Arquivo |\n")
        fh.write("|---|---|---:|---:|---:|---|\n")
        for c, p, db, df, n, nt, _ in usados:
            fh.write(f"| {c} | {p} | {db:.0f}s | {df:.0f}s | {nt} | `{n}` |\n")

        fh.write("\n## Descartados\n\n")
        fh.write("| Clipe | Pessoa | Bruto | Motivo |\n|---|---|---:|---|\n")
        for c, p, db, nota in caidos:
            fh.write(f"| {c} | {p} | {db:.0f}s | {nota} |\n")

        if any(t for *_, t in usados):
            fh.write("\n## Fala de cada peça final\n\n")
            fh.write("Transcrito do arquivo entregue, não do bruto: serve de prova de "
                     "que o corte não comeu palavra na entrada nem na saída.\n\n")
            fh.write("Duas ressalvas sobre esta evidência. O reconhecedor às vezes "
                     "**larga um fragmento curto no fim** da peça (aconteceu com o "
                     "\"E aí?\" do C0019, que está no arquivo mas não aparece abaixo); "
                     "e ele **não transcreve pedaço de palavra**, então este texto não "
                     "prova ausência de fragmento da equipe nas emendas. Para isso vale "
                     "a checagem de linha do tempo contra as palavras vizinhas, que é o "
                     "que o corte já garante.\n\n")
            for c, p, _db, df, n, _nt, t in usados:
                if t:
                    fh.write(f"**{c} — {p}** ({df:.0f}s)\n\n> {t}\n\n")

    print(f"{a.destino}: {len(usados)} aproveitados, {len(caidos)} descartados")


if __name__ == "__main__":
    main()
