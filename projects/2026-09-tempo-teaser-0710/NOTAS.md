# Tempo by Porsche · teaser do programa de saúde mental (07/10)

**Peça:** comunicado interno, 1080x1350, gancho de Setembro Amarelo, tom de teaser (save the date).
**Fonte da verdade:** `comunicado.html`. Renderizar com `bash render.sh`.

## Pendências
- **Logo da Tempo by Porsche é placeholder tipográfico.** O site está fora do allowlist do environment. Quando o arquivo chegar (SVG ou PNG com fundo transparente), salvar em `assets/tempo-logo.svg` e trocar o `<div class="tempo">` por `<img src="assets/tempo-logo.svg">`.
- Logo da Normalyze foi extraído do slide 01 do carrossel "Diagnósticos envelhecem" (sem arquivo oficial no repo). Se o time mandar o vetor, substituir `assets/normalyze-logo.png`.

## Decisões
- Fontes Sora (títulos) e Inter (texto) via `@fontsource`, porque Google Fonts está bloqueado. Arquivos em `assets/`.
- Paleta: navy `#0b0f1a` + gradiente teal→azul da Normalyze + amarelo `#ffd23f` só como acento da campanha.
- Sem travessão em nenhum texto (regra da marca).
- Data 07/10/2026 é quarta-feira (conferido).
