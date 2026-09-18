#!/usr/bin/env python3
"""Gera uma LUT 3D .cube de S-Log2 / S-Gamut para Rec.709.

O material da camera Sony (ILCE-7M3) vem em S-Log2 com primarias S-Gamut,
declarado no XML da propria camera. Sem essa conversao a imagem fica
chapada e dessaturada. A LUT faz:

    codigo S-Log2 -> cena linear -> S-Gamut para Rec.709 -> ombro nas altas
    -> gama de exibicao

Uso: python3 scripts/gera_lut_slog2.py saida.cube [--size 33] [--contraste 1.0]
"""
import argparse

import colour
import numpy as np


def rolloff_altas(x, joelho=0.80):
    """Comprime o que passa do joelho com um ombro suave, sem clipar nada.

    Abaixo do joelho a curva e identidade, entao o meio-tom nao se mexe.
    Acima, um Reinhard deslocado leva o infinito para 1.0 de forma continua.
    """
    x = np.maximum(x, 0.0)
    folga = 1.0 - joelho
    alto = joelho + folga * (x - joelho) / (folga + (x - joelho))
    return np.where(x < joelho, x, alto)


def construir(size=33, contraste=1.0, exposicao=0.0, joelho=0.80):
    eixo = np.linspace(0.0, 1.0, size)
    # ordem do .cube: o canal R varia mais rapido
    b, g, r = np.meshgrid(eixo, eixo, eixo, indexing="ij")
    rgb = np.stack([r, g, b], axis=-1)

    # 1) curva log -> cena linear (0.18 = cinza medio, 0.9 = branco de referencia)
    linear = colour.models.log_decoding_SLog2(
        rgb, bit_depth=10, in_normalised_code_value=True, out_reflection=True
    )
    linear = np.maximum(linear, 0.0)

    # 2) primarias S-Gamut -> Rec.709. Os dois espacos sao D65, entao a
    #    adaptacao cromatica e neutra; fica explicita so por seguranca.
    linear = colour.RGB_to_RGB(
        linear,
        colour.RGB_COLOURSPACES["S-Gamut"],
        colour.RGB_COLOURSPACES["ITU-R BT.709"],
        chromatic_adaptation_transform="CAT02",
    )
    linear = np.maximum(linear, 0.0)

    # 3) exposicao em stops, aplicada na cena linear (onde e fisicamente correta)
    if exposicao:
        linear = linear * (2.0 ** exposicao)

    # 4) ombro nas altas antes de codificar, para nao estourar o branco
    linear = rolloff_altas(linear, joelho)

    # 5) gama de exibicao. 0.18^(1/2.4) = 0.487, ou seja, o cinza medio da
    #    cena cai quase exatamente no meio da escala de video.
    saida = np.power(np.clip(linear, 0.0, 1.0), 1.0 / 2.4)

    # 6) contraste opcional em torno do cinza medio (1.0 = desligado)
    if contraste != 1.0:
        pivo = 0.487
        saida = np.clip((saida - pivo) * contraste + pivo, 0.0, 1.0)

    return np.clip(saida, 0.0, 1.0).reshape(-1, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("destino")
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--contraste", type=float, default=1.0)
    ap.add_argument("--exposicao", type=float, default=0.0,
                    help="stops aplicados na cena linear (negativo escurece)")
    ap.add_argument("--joelho", type=float, default=0.80,
                    help="onde comeca o ombro das altas, na cena linear")
    a = ap.parse_args()

    tabela = construir(a.size, a.contraste, a.exposicao, a.joelho)
    with open(a.destino, "w", encoding="utf-8") as fh:
        fh.write("# S-Log2 / S-Gamut -> Rec.709\n")
        fh.write(f"# gerado por scripts/gera_lut_slog2.py "
                 f"contraste={a.contraste} exposicao={a.exposicao} joelho={a.joelho}\n")
        fh.write(f"LUT_3D_SIZE {a.size}\n")
        fh.write("DOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n")
        for v in tabela:
            fh.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
    print(f"{a.destino}: {a.size}^3 = {len(tabela)} entradas")


if __name__ == "__main__":
    main()
