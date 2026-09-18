# Normalyze Conteúdo Studio: FRAMEWORK

Estúdio de edição e agendamento para as redes da **Normalyze.ai**. Espelho da infraestrutura dos estúdios `ana-conteudo` e `eita-conteudo`; a camada de marca desta página deve ser preenchida com a equipe na primeira leva de conteúdo.

## Posicionamento e voz da marca

**A DEFINIR COM A EQUIPE** antes da primeira peça pública:

- O que é a Normalyze.ai em uma frase (não inventar claims).
- Tom de voz (formal? direto? técnico? leve?) e a quem fala (persona do público).
- CTA padrão e link.
- Identidade visual: paleta, tipografia, logo (integrar via design system do Claude Design se existir).
- Voz de narração padrão do catálogo ElevenLabs (candidatas pt-BR listadas no CLAUDE.md; aprovar uma com teste de ouvido).

### Personas por rede

- **LinkedIn e Instagram têm personas diferentes.** Todo conteúdo nasce para uma das duas, com tom e formato próprios. **Nunca agendar a mesma peça em LinkedIn e Instagram.**
- **Grupo Instagram**: o que for para Instagram pode também ir para TikTok e YouTube vertical (Shorts), mesma peça e mesma persona.
- **Grupo LinkedIn**: peça própria (texto longo e/ou formato horizontal), sem replicar no grupo Instagram.
- Detalhe de cada persona (quem é, tom, dores): **a definir com a equipe**.

### REGRAS INEGOCIÁVEIS

1. **Nunca usar travessão em texto público.** Reescrever a frase.
2. Nenhum claim de produto sem validação da equipe.
3. **Nunca agendar a mesma peça em LinkedIn e Instagram** (personas diferentes). Instagram replica só para TikTok e YouTube Shorts.
4. Regras adicionais da marca: **a definir**.

## Pilares de conteúdo

**A DEFINIR.** Rascunho de hipóteses para discutir (padrão de marca de produto digital):

| Pilar | Formato | Observação |
|---|---|---|
| A | Demo de produto (tela + narração) | validar material disponível |
| B | Educacional do domínio | dor do público, dica prática |
| C | Prova social / casos | depoimentos, resultados |
| D | Institucional / marca | lançamentos, bastidores |

Nota: a marca tem **LinkedIn e YouTube** conectados além de Instagram/TikTok, então a leva pode incluir formatos horizontais e texto longo (LinkedIn) além de reels.

## Assinaturas de edição (herdadas, ajustar cores à marca)

- Hook verbal ou visual + título na tela nos **2 primeiros segundos**.
- Lettering condensado caps com sombra; **cor de acento: usar a da identidade da Normalyze** (substituir o amarelo #FFE234 dos projetos irmãos).
- Legendas frase a frase, terço inferior, SEMPRE por último no filter chain.
- Cortes secos; punch-ins 1.10 a 1.22x; freeze frames com card para punchlines; cutaways como payoff.
- Trilha discreta (vol ~0.12 a 0.15) via ElevenLabs sound-generation; SFX sincronizados aos cortes.
- Duração alvo: 20 a 60s (reels/TikTok); YouTube e LinkedIn podem ter cortes próprios. Loudness final: **-14 LUFS**.

## Fórmula da caption

**A definir por rede** (Instagram/TikTok curta com CTA; LinkedIn mais longa). Base: hook 1 linha, 2-3 parágrafos curtos, CTA, pergunta.

## Fluxo por vídeo

1. Bruto (Drive público ou anexo) + briefing (pilar, mensagem central, duração, data, redes de destino)
2. Proxy SDR (se HLG) + transcrição Scribe (timestamps por palavra)
3. Decupagem/cortes
4. Cor
5. Lettering/motion
6. **Legendas por último**
7. Trilha + SFX
8. Preview para aprovação na conversa
9. Caption por rede
10. Agendamento no Metricool como rascunho (blog_id 6735045), por rede

## Gotchas técnicos

Ver "Gotchas essenciais" no `CLAUDE.md` deste repo. Histórico completo e scripts de referência: repos `suportezv/ana-conteudo` e `suportezv/eita-conteudo`.

## Escolha do framework de motion: HyperFrames ou Remotion

O estúdio mantém os dois, e a escolha **não é preferência do momento**: cada peça declara o seu no `BRIEFING.md`, na primeira linha. Sem isso, quem pegar o projeto depois não sabe onde mexer.

**O que decide**: a ponte entre os dois só existe num sentido. Há a skill `remotion-to-hyperframes`; **não existe o inverso**. Então peça feita em HyperFrames é definitiva, e peça feita em Remotion ainda pode migrar. Na dúvida, Remotion é a aposta reversível.

| Use **HyperFrames** quando | Use **Remotion** quando |
|---|---|
| É peça da série recorrente, na gramática já documentada | A peça é exceção, fora do padrão da série |
| Você quer o fluxo pronto: brief, storyboard, registry de blocos, legendas, áudio, render em nuvem | A composição precisa de lógica de programação, dados ou parametrização |
| O visual pedido já existe no registry | Você vai gerar **N variações** da mesma peça mudando nome, número ou idioma |
| Ninguém vai reprocessar a peça em outro framework | Há chance real de a peça mudar de destino depois |

**Padrão declarado: HyperFrames.** É o que está integrado ao fluxo do estúdio e o que tem as skills registradas. O Remotion entra por decisão consciente, não por inércia.

**Custo de manter os dois, para vigiar**: dois `node_modules`, dois caminhos de render e dois lugares onde a paleta pode divergir. O terceiro está mitigado, porque os tokens do Remotion vivem em `remotion/src/marca.ts`, mas **se a paleta da marca mudar, atualizar os dois lados**.

## Identidade visual (provisória, amostrada das artes)

A paleta oficial segue **a definir com a equipe**. Enquanto isso, `remotion/src/marca.ts` carrega os hexes amostrados das artes já publicadas no LinkedIn, para que o Remotion renderize na cara da marca em vez de na paleta de outro estúdio:

| Token | Hex | Onde aparece |
|---|---|---|
| `azul` | `#3330BD` | fundo dominante das artes; destaque sobre fundo claro |
| `azulVivo` | `#4A57DD` | tom claro do gradiente do logo |
| `indigo` | `#393BC6` | botão de CTA |
| `verdeAgua` | `#2DC4B2` | acento, segundo tom do gradiente do logo |
| `verdeVivo` | `#4CE8AF` | números e destaques sobre fundo escuro |
| `auroraBase` | `#EDEDED` | fundo claro das artes |
| `tinta` / `fundoEscuro` | `#17171D` | texto e fundo escuro |

**Cor de acento para lettering de vídeo**: usar `#2DC4B2` (ou `#4CE8AF` sobre fundo escuro) no lugar do amarelo `#FFE234` dos projetos irmãos. **Fonte oficial ainda pendente**; o render cai para a sans do sistema até a equipe informar e o arquivo ser embutido como asset local.
