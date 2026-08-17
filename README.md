# Normalyze Conteúdo Studio

Estúdio de edição e agendamento de conteúdo para as redes da **Normalyze.ai**. Projeto irmão de [`ana-conteudo`](https://github.com/suportezv/ana-conteudo) e [`eita-conteudo`](https://github.com/suportezv/eita-conteudo); mesma infraestrutura, marca própria.

- **`FRAMEWORK.md`**: posicionamento (a preencher com a equipe), regras, formatos e fluxo por vídeo.
- **`CLAUDE.md`**: memória persistente do projeto (IDs, contas, gotchas).
- **`projects/`**: um subdiretório por peça (briefing, transcrição, scripts de edição, caption).
- **`scripts/`**: setup e validação do ambiente (Linux/cloud).
- **`patches/`**: correções necessárias nas ferramentas.

## Primeiro uso (cloud)

```bash
bash scripts/setup.sh
bash scripts/validate.sh
```

| Serviço | Uso | Configuração |
|---|---|---|
| Metricool | Agendamento | Marca "normalyze.ai", blog_id 6735045 (IG, FB, LinkedIn, TikTok, YouTube) |
| Google Drive | Brutos | Conector oficial + pasta pública (a apontar) |
| ElevenLabs | Transcrição, trilha, SFX, narração | Chave `sk_...` no `.env` do video-use; voz por peça (sem voz própria) |
| Kairogen | B-roll por IA | Conta suporte@zavi.ag (Essential) |
