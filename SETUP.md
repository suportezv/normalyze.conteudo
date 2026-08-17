# Setup do Normalyze Conteúdo Studio

Espelho do setup dos estúdios irmãos. No cloud:

```bash
bash scripts/setup.sh
bash scripts/validate.sh
```

## Environment (Claude Code cloud)

Usar o environment **"ana-conteudo"** (ou duplicar): network **Custom** com `drive.google.com`, `drive.usercontent.google.com` e `api.elevenlabs.io` liberados, env var `ELEVENLABS_API_KEY` com a chave `sk_...` atual e setup script `bash scripts/setup.sh`. Configura-se no seletor de nuvem acima da caixa de mensagem em claude.ai/code.

## Conectores

- **Metricool**: marca "normalyze.ai", **blog_id 6735045**, timezone America/Sao_Paulo (IG @normalyze.ai, Facebook, LinkedIn, TikTok, YouTube).
- **Google Drive**: pasta de brutos com "qualquer pessoa com o link: leitor" (a apontar).
- **ElevenLabs**: chave `sk_...` (51 chars) no `.env` do video-use. Sem voz própria da marca; escolher do catálogo por peça e registrar a padrão no CLAUDE.md quando aprovada.
- **Kairogen**: conta suporte@zavi.ag, plano Essential (`veo3-1-lite`).

## Validação final

1. `ffmpeg -filters | grep -cE "subtitles|zscale"` >= 2.
2. Transcrever 10s de um vídeo com o helper do video-use: JSON com timestamps por palavra.
3. Rede: `curl -s -o /dev/null -w "%{http_code}" https://drive.google.com/` responde HTTP (não 000).
4. Metricool: `getBrandSettings` lista "normalyze.ai" com as redes conectadas.
5. Kairogen: `get_me_context` mostra plano e créditos.
6. Memória persistente: `CLAUDE.md` deste repo.
