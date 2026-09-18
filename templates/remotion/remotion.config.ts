import {Config} from '@remotion/cli/config';

// O container ja traz o headless shell do Playwright. Sem apontar para ele, o
// Remotion tenta baixar Chrome de remotion.media, que nao esta no allowlist do
// environment, e o render morre com 403 antes do primeiro frame.
// `source scripts/env.sh` na raiz do estudio exporta as duas variaveis.
const chrome = process.env.REMOTION_BROWSER_EXECUTABLE || process.env.CHROME_SHELL;
if (chrome) {
  Config.setBrowserExecutable(chrome);
}

Config.setVideoImageFormat('jpeg');
Config.setCodec('h264');
