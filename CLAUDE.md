# Normalyze Conteúdo Studio (memória persistente do projeto)

Este repositório é o **Normalyze Conteúdo Studio**: edição e agendamento de conteúdo para as redes da **Normalyze.ai**. Projeto irmão de `ana-conteudo` e `eita-conteudo` (mesma infraestrutura de estúdio, marca diferente).

**Antes de editar qualquer vídeo ou escrever qualquer caption, leia `FRAMEWORK.md`** (posicionamento, regras, formatos, assinaturas de edição e gotchas técnicos).

## Regras que valem em qualquer resposta pública

- Nunca usar travessão em texto público (caption, lettering, legenda): reescrever a frase.
- Personas diferentes por rede: **nunca agendar a mesma peça em LinkedIn e Instagram**. Conteúdo do Instagram pode replicar para TikTok e YouTube Shorts; LinkedIn tem peça própria. Ver "Personas por rede" no FRAMEWORK.md.
- Posicionamento, tom de voz e claims do produto: **a definir com a equipe** (preencher no FRAMEWORK.md na primeira leva). Não inventar claims sobre o produto.

## Working dirs

- Estúdio: este repo (symlink `~/normalyze-conteudo` aponta para cá). Projetos em `projects/<nome>/`.
- Ferramentas: `video-use` e `hyperframes` clonados em `/workspace/browser-use/` e `/workspace/heygen-com/` (Linux/cloud) ou `~/video-editor/` (Mac). Skills registradas em `~/.claude/skills/`.
- Ambiente novo (container limpo): rode `bash scripts/setup.sh` e depois `bash scripts/validate.sh`.

## IDs e contas

- Metricool: conta da agência suporte@mentoravirtual.com.br, marca "normalyze.ai", **blog_id 6735045**, timezone America/Sao_Paulo. Redes conectadas: Instagram **@normalyze.ai**, Facebook, LinkedIn, TikTok e YouTube. Melhor horário: medir (getBestTimeToPostByNetwork).
- ElevenLabs: chave em `.env` na raiz do video-use (transcrição Scribe + SFX/trilha + TTS; chave com voices_read). **A marca não tem voz própria**: escolher voz do catálogo da conta por peça (vozes profissionais pt-BR disponíveis: masculinas como Paulo `Qrdut83w0Cr152Yb4Xn3`, Juliano `wHnxjlY53t8X9Oi14Awz`, Hugo `NEiOFjKQRRitVnzQNwhS`; femininas como Raquel `GDzHdQOi6jjf8zaXhCYD`, Bia `Eyspt3SYhZzXd1Jd3J8O`, Katiuscia `wXwzHFLHnXex5h3JPBXA`). Registrar aqui a voz padrão quando a equipe aprovar uma. Amostras das 6 candidatas (mesmo texto de teste): `assets/vozes/`.
- Kairogen: conta suporte@zavi.ag, plano Essential (`veo3-1-lite` para vídeo). O Kairogen acessa o mesmo workspace ElevenLabs da conta (mesmos voice_ids): TTS via `generate_audio` kind=speech (3 créditos/amostra) funciona mesmo sem a chave da ElevenLabs no ambiente. Para trazer o áudio ao container quando o proxy bloqueia `cdn.kairogen.ai`, usar `download_audio_from_url` (salva o binário localmente).
- Drive (brutos): pasta do projeto **PENDENTE: criar/apontar** (padrão: "qualquer pessoa com o link: leitor" para download direto).

## Gotchas essenciais (herdados e validados nos projetos irmãos)

- Brutos de iPhone são HLG 10-bit: gerar proxy SDR uma vez antes de editar (filtro `colorspace=all=bt709:itrc=bt2020-10:iprimaries=bt2020:ispace=bt2020nc`).
- Legendas SEMPRE por último no filter chain; overlays via PIL em PNG com fade de alpha (ou PNG sequence + qtrle).
- Zoom animado com `zoompan`, não `crop` (crop não aceita `t` em w/h).
- **O patch `video-use-is-portrait-source` foi aposentado (18/set/2026).** O upstream reescreveu `is_portrait_source` para ler também o `rotation` do side data, cobrindo mais casos que o patch cobria. O `validate.sh` agora testa **comportamento** (retrato, paisagem e paisagem com matriz de rotação 90) em vez de procurar o patch no código.
- Metricool MCP: sem delete (cancelar = update draft:true; update devolve id novo); mídia por URL pública (o Metricool copia para o CDN dele na hora).
- Mac: usar ffmpeg-full keg-only com PATH explícito. Linux: ffmpeg do apt já serve.
- Cloud, brutos do Drive: usar environment com network Custom e `drive.google.com` + `drive.usercontent.google.com` + `api.elevenlabs.io` liberados (o environment "ana-conteudo" já está assim). Download direto de arquivo público, qualquer tamanho: `curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`. Conector MCP do Drive: busca e metadados; download só até ~4 MB. Fallback pequeno: Kairogen `download_audio_from_url`.
- Cloud, mídia pública para o Metricool: commit temporário do render na branch (repo público, raw.githubusercontent.com passa no proxy), agendar e remover o arquivo em seguida. Exige `git add -f` com autorização do usuário. **Por isso este repo deve ser público.**
- Trilhas/SFX: ElevenLabs sound-generation (`/v1/sound-generation`, máx ~22s); trilha maior = build+drop com acrossfade. Batidas: detector numpy (fluxo de energia + autocorrelação), ver `ana-conteudo/projects/teste-02-interlagos/edit/beats.py`.
- Claude Design: fluxo na nuvem via botão "Send to Claude Code Web" do projeto de design (a sessão recebe os arquivos e produz os finais); DesignSync direto só em sessão local com /design-login.

## Rede do environment (gotcha central, custou tempo)

`pypi.org`, `files.pythonhosted.org` e `registry.npmjs.org` vêm na variável `no_proxy` do container. Por isso **contornam o agent proxy** e batem direto no firewall de egresso, que responde **403 "Host not in allowlist"** mesmo estando na allowlist. **Roteando pelo agent proxy respondem 200.** O contorno está embutido no `scripts/setup.sh`: quando existe `HTTPS_PROXY`, ele limpa `no_proxy` e aponta pip, uv e npm para o proxy com o CA bundle `/root/.ccr/ca-bundle.crt`.

- **A allowlist é literal por subdomínio.** Cadastrar `googleapis.com` não cobre `generativelanguage.googleapis.com`. O campo aceita `*`, então para um site inteiro use `*.dominio.com` junto do apex.
- **Diagnóstico em um comando**: `curl -sv https://host/ 2>&1 | grep CONNECT`. `HTTP/1.1 403` no CONNECT é allowlist; qualquer outra resposta significa que a rede passou e o problema é outro (chave, quota, rota).
- **Chromium não contorna a allowlist**: usa o mesmo agent proxy e devolve `ERR_TUNNEL_CONNECTION_FAILED` no host que o `curl` recusa.
- **WebFetch tem rota de egresso própria** e pode falhar num domínio que o `curl` do container acessa. Na dúvida, usar `curl`.

## Ferramentas portadas do estúdio Profissio.ai (18/set/2026)

Cinto de ferramentas genérico, trazido conforme o `PORTAR.md` daquele estúdio. Nenhum destes scripts tem marca dentro:

| Script | O que faz |
|---|---|
| `scripts/decupar.py` | Decupa vídeo por **âncoras de texto** ("de tal frase até tal frase") casadas contra transcrição com timestamp por palavra. Junta trechos, gira, aplica LUT, normaliza áudio |
| `scripts/relatorio_decupagem.py` | Retranscreve as peças finais e monta o relatório do que ficou e do que caiu |
| `scripts/gera_lut_slog2.py` | Gera LUT 3D de S-Log2/S-Gamut para Rec.709 a partir das transferências da `colour-science` |
| `scripts/zip_index_remoto.py` | Lista e extrai arquivos de um ZIP gigante no Drive por *range request*, sem baixar o ZIP |
| `scripts/gera_imagem.py` | Gera imagem pela OpenAI ou pelo Gemini, mesma interface, chaves só do ambiente |
| `scripts/sobe_para_drive.py` | Sobe arquivos para uma pasta do Drive com token de acesso |

Chaves ficam **nas variáveis de ambiente do environment**, nunca no repo: `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`. Variável cadastrada com sessão já aberta só vale em **sessão nova** (a env entra na criação do container); conferir com `printenv | grep -c API_KEY` antes de acusar o script. Chave válida também não significa quota: no Gemini, `429` com `quotaId: ...-FreeTier` quer dizer que o projeto daquela chave não está no faturamento.

### Gotchas de craft herdados

- **Brutos de Sony em S-Log2: converter, não "filtrar".** O XML lateral do clipe declara `CaptureGammaEquation` e `CaptureColorPrimaries`; quando diz `s-log2`/`s-gamut`, a imagem chega chapada. Usar `scripts/gera_lut_slog2.py`, com **exposição −0,5 stop e joelho em 0,65** (sem isso o branco estoura), conferindo que o ffmpeg aplica a `lut3d` **em RGB, não em YUV**. Saída sempre com `out_range=tv` e `-color_range tv`.
- **Câmera pode gravar na vertical sem gravar a flag de rotação.** O arquivo vem deitado e o ffprobe não mostra rotação nenhuma; só olhando um frame se descobre. Corrigir com `transpose=1` antes de escalar, e checar um frame de qualquer lote novo.
- **Decupagem por âncora de texto, não por timecode.** Revisar um corte vira editar uma frase. O campo `apos` empurra o cursor quando a mesma frase aparece antes.
- **Remotion renderiza com o `headless_shell`, não com o Chromium do Playwright.** O `chromium-1194` removeu o headless antigo e o launch morre com "Old Headless mode has been removed". O binário certo é `/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`, fixado em `remotion/remotion.config.ts`.
- **Sem rede de fontes no render.** Google Fonts está fora da allowlist e o Remotion cai para a sans do sistema. Para usar a fonte da marca, embutir o arquivo como asset local.
- **Processo em background com `nohup`/`setsid` é recolhido quando a tool call retorna.** Usar `run_in_background: true` da própria ferramenta Bash, ou deixar estourar o timeout do primeiro plano. Em lote longo, `flock` num arquivo de lock evita corrida.
- **Metricool: rascunho com data vencida não publica e não avisa.** Um post `draft:true` cuja data passa continua aparecendo em `getScheduledPosts` como se estivesse agendado, mas nunca dispara. **Quem agenda tira do rascunho na mesma sessão e confirma com `getScheduledPosts`**; data no passado não resolve, é preciso data nova.
- **Ler o índice de um ZIP gigante no Drive sem baixar o arquivo**: `drive.usercontent.google.com` aceita `Range`; pegar os últimos ~64 KB, achar o EOCD (`PK\x05\x06`), e em arquivo >4 GB o ZIP64 EOCD via locator `PK\x06\x07`. Com entradas `method=0` (stored), cada arquivo sai sozinho por outro `Range`. Ver `scripts/zip_index_remoto.py`.
- **Skills do hyperframes sem rede**: `npx hyperframes skills update` falha quando `raw.githubusercontent.com` está fora da allowlist. Não precisa liberar: o `setup.sh` registra as skills a partir do clone local.
- **Em sessão nova, conferir `ls /workspace`** antes de contar com video-use ou hyperframes. O gatilho de boot do environment não roda o `setup.sh` de forma confiável; rodar à mão resolve.
