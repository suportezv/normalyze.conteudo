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
- **Antes de qualquer `npm`, `npx`, `pip` ou `uv` na mao: `source scripts/env.sh`.** Sem isso o npm contorna o agent proxy e leva 403 do firewall mesmo com o dominio liberado. O env.sh tambem aponta Remotion e hyperframes para o Chrome que ja vem no container.

## IDs e contas

- Metricool: conta da agência suporte@mentoravirtual.com.br, marca "normalyze.ai", **blog_id 6735045**, timezone America/Sao_Paulo. Redes conectadas: Instagram **@normalyze.ai**, Facebook, LinkedIn, TikTok e YouTube. Melhor horário: medir (getBestTimeToPostByNetwork).
- **Regra de agendamento (todas as marcas da agência)**: sempre incluir TODOS os canais conectados da marca no post, exceto YouTube horizontal. YouTube entra como **Short** (`youtubeData: {type: "short", title, madeForKids: false}`); Instagram como REEL; Facebook como REEL; TikTok e LinkedIn com networkData padrão. Nunca publicar vídeo vertical como YouTube horizontal comum.
- ElevenLabs: chave em `.env` na raiz do video-use (transcrição Scribe + SFX/trilha + TTS; chave com voices_read). **A marca não tem voz própria**: escolher voz do catálogo da conta por peça (vozes profissionais pt-BR disponíveis: masculinas como Paulo `Qrdut83w0Cr152Yb4Xn3`, Juliano `wHnxjlY53t8X9Oi14Awz`, Hugo `NEiOFjKQRRitVnzQNwhS`; femininas como Raquel `GDzHdQOi6jjf8zaXhCYD`, Bia `Eyspt3SYhZzXd1Jd3J8O`, Katiuscia `wXwzHFLHnXex5h3JPBXA`). Registrar aqui a voz padrão quando a equipe aprovar uma.
- OpenAI e Gemini: as chaves chegam como **env var do environment** (`OPENAI_API_KEY`, `GEMINI_API_KEY`), nunca versionadas no repo. Ambas validadas em 18/set/2026 com chamada real de geracao. Gemini: model ids antigos (`gemini-2.0-flash`) foram aposentados e devolvem 404 com a sugestao do substituto; antes de usar, listar com `GET https://generativelanguage.googleapis.com/v1beta/models` (ha `gemini-flash-latest` e `gemini-pro-latest`, que nao envelhecem).
- Kairogen: conta suporte@zavi.ag, plano Essential (`veo3-1-lite` para vídeo).
- Drive (brutos): pasta do projeto **PENDENTE: criar/apontar** (padrão: "qualquer pessoa com o link: leitor" para download direto).

## Rede do environment (cloud)

O allowlist e aplicado **quando o container nasce**. Mudar os dominios no environment so vale em **sessao nova**: a sessao ja aberta continua com a lista antiga.

Lista minima para o estudio funcionar inteiro:

| Dominio | Para que |
|---|---|
| `github.com` | clone do video-use e do hyperframes; build estatico do ffmpeg (BtbN releases) |
| `raw.githubusercontent.com` | `hyperframes skills update` e midia publica para o Metricool |
| `registry.npmjs.org` | Remotion e o CLI `npx hyperframes` |
| `cdn.jsdelivr.net` | **PENDENTE**: composicoes do hyperframes carregam o GSAP daqui. Sem ele o render morre com `sub_timeline_script_failure`. Workaround: `bash scripts/vendor-gsap.sh <projeto>` |
| `pypi.org` + `files.pythonhosted.org` | deps do video-use, pillow (overlays), numpy (batidas) |
| `drive.google.com` + `drive.usercontent.google.com` | brutos |
| `api.elevenlabs.io` | transcricao, TTS, SFX |
| `api.openai.com` | validado 18/set/2026 com chamada real |
| `generativelanguage.googleapis.com` | validado 18/set/2026 com chamada real |

Atencao ao editar a lista: tirar `github.com`, `drive.google.com` ou `api.elevenlabs.io` quebra, respectivamente, ffmpeg + clones, brutos e audio.

## Producao de video: qual ferramenta

Tres caminhos, validados ponta a ponta em 18/set/2026 neste container:

| Ferramenta | Para que | Como |
|---|---|---|
| **video-use** | editar footage real (brutos, cortes, legendas, grade) | skill `/video-use` |
| **hyperframes** | motion graphics, explainer, promo, deck (HTML + GSAP) | skill `/hyperframes` e a CLI `npx hyperframes` |
| **Remotion** | peca em React quando o time ja tem componente pronto | `bash scripts/new-remotion.sh <nome>` |

Notas que custaram tempo para descobrir:

- **Remotion** ignora `REMOTION_BROWSER_EXECUTABLE` na CLI: o que vale e `Config.setBrowserExecutable()` no `remotion.config.ts` (o template ja faz) ou a flag `--browser-executable`. Sem isso ele tenta baixar Chrome de `remotion.media` e morre com 403.
- **hyperframes** precisa de `HYPERFRAMES_BROWSER_PATH` apontando para o headless shell; sem ela o `browser ensure` fica preso em "Looking for an existing browser". O `scripts/env.sh` exporta.
- **hyperframes** so renderiza com o GSAP acessivel. Enquanto `cdn.jsdelivr.net` nao estiver liberado, rode `bash scripts/vendor-gsap.sh projects/<nome>/<projeto-hf>` depois do `init`.
- O `hyperframes skills update` depende de `raw.githubusercontent.com`. As 20 skills ja ficam registradas pelo fallback do `setup.sh`, entao a atualizacao e opcional.

## Texto e ideacao: OpenAI e Gemini

`scripts/llm.py` fala com os dois usando so stdlib. As chaves vem das env vars do environment (`OPENAI_API_KEY`, `GEMINI_API_KEY`), nunca do repo.

```bash
source scripts/env.sh
python3 scripts/llm.py --check                       # testa as duas conexoes
python3 scripts/llm.py --list                        # modelos vivos
python3 scripts/llm.py --system "<tom de voz>" "<prompt>"
python3 scripts/llm.py --provider gemini "<prompt>"
```

Defaults em `DEFAULTS` no topo do script: `gpt-5.5` e `gemini-flash-latest`. Passar o tom de voz da marca em `--system` quando o FRAMEWORK.md estiver preenchido.

## Gotchas essenciais (herdados e validados nos projetos irmãos)

- Brutos de iPhone são HLG 10-bit: gerar proxy SDR uma vez antes de editar (filtro `colorspace=all=bt709:itrc=bt2020-10:iprimaries=bt2020:ispace=bt2020nc`).
- Legendas SEMPRE por último no filter chain; overlays via PIL em PNG com fade de alpha (ou PNG sequence + qtrle).
- Zoom animado com `zoompan`, não `crop` (crop não aceita `t` em w/h).
- video-use e vertical: o patch `patches/video-use-is-portrait-source.patch` foi aposentado em 18/set/2026, o upstream passou a ler o `rotation` do side data. O `validate.sh` confere o comportamento, nao a presenca do patch. Se a deteccao sumir do upstream, vertical volta a virar paisagem.
- Metricool MCP: sem delete (cancelar = update draft:true; update devolve id novo); mídia por URL pública (o Metricool copia para o CDN dele na hora).
- Mac: usar ffmpeg-full keg-only com PATH explícito. Linux: ffmpeg do apt já serve.
- Cloud, brutos do Drive: usar environment com network Custom e `drive.google.com` + `drive.usercontent.google.com` + `api.elevenlabs.io` liberados (o environment "ana-conteudo" já está assim). Download direto de arquivo público, qualquer tamanho: `curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`. Conector MCP do Drive: busca e metadados; download só até ~4 MB. Fallback pequeno: Kairogen `download_audio_from_url`.
- Cloud, mídia pública para o Metricool: commit temporário do render na branch (repo público, raw.githubusercontent.com passa no proxy), agendar e remover o arquivo em seguida. Exige `git add -f` com autorização do usuário. **Por isso este repo deve ser público.**
- Trilhas/SFX: ElevenLabs sound-generation (`/v1/sound-generation`, máx ~22s); trilha maior = build+drop com acrossfade. Batidas: detector numpy (fluxo de energia + autocorrelação), ver `ana-conteudo/projects/teste-02-interlagos/edit/beats.py`.
- hyperframes: o `npx hyperframes skills update` depende de `raw.githubusercontent.com` e se recusa a reportar sucesso sem ele. O `scripts/setup.sh` ja cai no fallback e registra as skills direto do clone (20 skills, incluindo `remotion-to-hyperframes`). O CLI em si (`npx hyperframes`) precisa de `registry.npmjs.org` e de Node 22+.
- Remotion: o container ja traz Chromium em `/opt/pw-browsers` (inclusive `chromium_headless_shell`). Apontar o Remotion para esse binario evita depender de download de browser em dominio fora do allowlist.
- Claude Design: fluxo na nuvem via botão "Send to Claude Code Web" do projeto de design (a sessão recebe os arquivos e produz os finais); DesignSync direto só em sessão local com /design-login.
