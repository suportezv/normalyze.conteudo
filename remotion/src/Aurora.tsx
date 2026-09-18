import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { marca } from "./marca";

/**
 * Fundo aurora da marca: manchas desfocadas que derivam devagar sobre base clara.
 * E o mesmo sistema visual dos PNGs em "Fundos da marca" no Drive.
 */
export const Aurora: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = frame / durationInFrames;

  const manchas = [
    { cor: marca.azul, x: 22, y: 28, r: 46, fase: 0 },
    { cor: marca.azulVivo, x: 74, y: 24, r: 40, fase: 0.33 },
    { cor: marca.verdeAgua, x: 62, y: 76, r: 44, fase: 0.66 },
    { cor: marca.azulSuave, x: 30, y: 74, r: 36, fase: 0.85 },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: marca.auroraBase }}>
      {manchas.map((m, i) => {
        const ang = (t + m.fase) * Math.PI * 2;
        const dx = Math.cos(ang) * 4;
        const dy = Math.sin(ang * 0.8) * 3;
        return (
          <AbsoluteFill
            key={i}
            style={{
              // gradiente radial em porcentagem: escala com qualquer formato
              background: `radial-gradient(circle at ${m.x + dx}% ${m.y + dy}%, ${m.cor} 0%, transparent ${m.r}%)`,
              filter: "blur(60px)",
              opacity: 0.55,
            }}
          />
        );
      })}
      {/* veu claro por cima: segura o contraste do texto sem apagar a aurora */}
      <AbsoluteFill
        style={{
          backgroundColor: marca.auroraBase,
          opacity: interpolate(t, [0, 1], [0.24, 0.3]),
        }}
      />
    </AbsoluteFill>
  );
};
