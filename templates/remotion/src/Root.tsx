import {Composition} from 'remotion';
import {Main} from './Main';

// Formato padrao do estudio: 9:16 para reel, short e TikTok.
export const RemotionRoot: React.FC = () => (
  <Composition
    id="Main"
    component={Main}
    durationInFrames={30 * 6}
    fps={30}
    width={1080}
    height={1920}
  />
);
