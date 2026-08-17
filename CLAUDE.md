# Normalyze Conteúdo Studio (memória persistente do projeto)

Este repositório é o **Normalyze Conteúdo Studio**: edição e agendamento de conteúdo para as redes da **Normalyze.ai**. Projeto irmão de `ana-conteudo` e `eita-conteudo` (mesma infraestrutura de estúdio, marca diferente).

**Antes de editar qualquer vídeo ou escrever qualquer caption, leia `FRAMEWORK.md`** (posicionamento, regras, formatos, assinaturas de edição e gotchas técnicos).

## Regras que valem em qualquer resposta pública

- Nunca usar travessão em texto público (caption, lettering, legenda): reescrever a frase.
- Posicionamento, tom de voz e claims do produto: **a definir com a equipe** (preencher no FRAMEWORK.md na primeira leva). Não inventar claims sobre o produto.

## Working dirs

- Estúdio: este repo (symlink `~/normalyze-conteudo` aponta para cá). Projetos em `projects/<nome>/`.
- Ferramentas: `video-use` e `hyperframes` clonados em `/workspace/browser-use/` e `/workspace/heygen-com/` (Linux/cloud) ou `~/video-editor/` (Mac). Skills registradas em `~/.claude/skills/`.
- Ambiente novo (container limpo): rode `bash scripts/setup.sh` e depois `bash scripts/validate.sh`.

## IDs e contas

- Metricool: conta da agência suporte@mentoravirtual.com.br, marca "normalyze.ai", **blog_id 6735045**, timezone America/Sao_Paulo. Redes conectadas: Instagram **@normalyze.ai**, Facebook, LinkedIn, TikTok e YouTube. Melhor horário: medir (getBestTimeToPostByNetwork).
- **Regra de agendamento (todas as marcas da agência)**: sempre incluir TODOS os canais conectados da marca no post, exceto YouTube horizontal. YouTube entra como **Short** (`youtubeData: {type: "short", title, madeForKids: false}`); Instagram como REEL; Facebook como REEL; TikTok e LinkedIn com networkData padrão. Nunca publicar vídeo vertical como YouTube horizontal comum.
- ElevenLabs: chave em `.env` na raiz do video-use (transcrição Scribe + SFX/trilha + TTS; chave com voices_read). **A marca não tem voz própria**: escolher voz do catálogo da conta por peça (vozes profissionais pt-BR disponíveis: masculinas como Paulo `Qrdut83w0Cr152Yb4Xn3`, Juliano `wHnxjlY53t8X9Oi14Awz`, Hugo `NEiOFjKQRRitVnzQNwhS`; femininas como Raquel `GDzHdQOi6jjf8zaXhCYD`, Bia `Eyspt3SYhZzXd1Jd3J8O`, Katiuscia `wXwzHFLHnXex5h3JPBXA`). Registrar aqui a voz padrão quando a equipe aprovar uma.
- Kairogen: conta suporte@zavi.ag, plano Essential (`veo3-1-lite` para vídeo).
- Drive (brutos): pasta do projeto **PENDENTE: criar/apontar** (padrão: "qualquer pessoa com o link: leitor" para download direto).

## Gotchas essenciais (herdados e validados nos projetos irmãos)

- Brutos de iPhone são HLG 10-bit: gerar proxy SDR uma vez antes de editar (filtro `colorspace=all=bt709:itrc=bt2020-10:iprimaries=bt2020:ispace=bt2020nc`).
- Legendas SEMPRE por último no filter chain; overlays via PIL em PNG com fade de alpha (ou PNG sequence + qtrle).
- Zoom animado com `zoompan`, não `crop` (crop não aceita `t` em w/h).
- video-use precisa do patch `patches/video-use-is-portrait-source.patch` (senão vertical vira paisagem).
- Metricool MCP: sem delete (cancelar = update draft:true; update devolve id novo); mídia por URL pública (o Metricool copia para o CDN dele na hora).
- Mac: usar ffmpeg-full keg-only com PATH explícito. Linux: ffmpeg do apt já serve.
- Cloud, brutos do Drive: usar environment com network Custom e `drive.google.com` + `drive.usercontent.google.com` + `api.elevenlabs.io` liberados (o environment "ana-conteudo" já está assim). Download direto de arquivo público, qualquer tamanho: `curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`. Conector MCP do Drive: busca e metadados; download só até ~4 MB. Fallback pequeno: Kairogen `download_audio_from_url`.
- Cloud, mídia pública para o Metricool: commit temporário do render na branch (repo público, raw.githubusercontent.com passa no proxy), agendar e remover o arquivo em seguida. Exige `git add -f` com autorização do usuário. **Por isso este repo deve ser público.**
- Trilhas/SFX: ElevenLabs sound-generation (`/v1/sound-generation`, máx ~22s); trilha maior = build+drop com acrossfade. Batidas: detector numpy (fluxo de energia + autocorrelação), ver `ana-conteudo/projects/teste-02-interlagos/edit/beats.py`.
- Claude Design: fluxo na nuvem via botão "Send to Claude Code Web" do projeto de design (a sessão recebe os arquivos e produz os finais); DesignSync direto só em sessão local com /design-login.
