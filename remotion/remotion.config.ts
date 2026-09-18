import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
// O container nao tem Chrome proprio. Usa o headless_shell que vem com o
// Playwright: o Chromium normal de la removeu o headless antigo que o
// Remotion pede, e o download do browser proprio do Remotion esta fora da
// allowlist de rede deste environment.
Config.setBrowserExecutable("/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell");
