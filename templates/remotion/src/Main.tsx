import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

// Lettering de exemplo. Regra da marca: nunca usar travessao em texto publico.
const LINHAS = ['Seus dados', 'estao onde', 'voce acha?'];

export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const saida = interpolate(frame, [durationInFrames - fps / 2, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#0b0f1a', justifyContent: 'center', padding: 96}}>
      <AbsoluteFill style={{justifyContent: 'center', padding: 96, opacity: saida}}>
        {LINHAS.map((linha, i) => {
          const entrada = spring({frame: frame - i * 6, fps, config: {damping: 200}});
          return (
            <div
              key={linha}
              style={{
                color: '#e6edf7',
                fontFamily: 'Helvetica, Arial, sans-serif',
                fontSize: 104,
                fontWeight: 800,
                lineHeight: 1.1,
                opacity: entrada,
                transform: `translateY(${interpolate(entrada, [0, 1], [40, 0])}px)`,
              }}
            >
              {linha}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
