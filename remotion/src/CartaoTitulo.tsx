import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Aurora } from "./Aurora";
import { marca } from "./marca";

export type PropsCartao = {
  titulo: string;
  /** Palavra do titulo que recebe o azul da marca. Opcional. */
  destaque?: string;
  rodape?: string;
};

/**
 * Cartao de titulo na gramatica do estudio: fundo aurora com muito espaco
 * negativo, uma linha curta de tipografia contida (nunca display gigante) e
 * revelacao palavra a palavra, como nas referencias do @elevenlabsio.
 */
export const CartaoTitulo: React.FC<PropsCartao> = ({ titulo, destaque, rodape }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const palavras = titulo.split(" ");

  return (
    <AbsoluteFill>
      <Aurora />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: "0 10%",
          fontFamily: marca.fonte,
        }}
      >
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "0.28em",
            fontSize: 74,
            fontWeight: 600,
            letterSpacing: "-0.02em",
            lineHeight: 1.18,
            textAlign: "center",
          }}
        >
          {palavras.map((p, i) => {
            // cada palavra entra um pouco depois da anterior
            const entrada = spring({
              frame: frame - 6 - i * 4,
              fps,
              config: { damping: 200 },
            });
            const ehDestaque = destaque
              ? p.replace(/[.,!?]/g, "").toLowerCase() === destaque.toLowerCase()
              : false;
            return (
              <span
                key={i}
                style={{
                  color: ehDestaque ? marca.azul : marca.tinta,
                  opacity: entrada,
                  transform: `translateY(${interpolate(entrada, [0, 1], [14, 0])}px)`,
                  display: "inline-block",
                }}
              >
                {p}
              </span>
            );
          })}
        </div>

        {rodape ? (
          <div
            style={{
              marginTop: 34,
              fontSize: 25,
              color: marca.tinta,
              // o rodape so aparece depois que o titulo assentou
              opacity: interpolate(
                frame,
                [durationInFrames - fps * 2.2, durationInFrames - fps * 1.6],
                [0, 0.62],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
              ),
            }}
          >
            {rodape}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
