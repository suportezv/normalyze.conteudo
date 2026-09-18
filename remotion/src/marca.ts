/**
 * Paleta e tokens da Normalyze.
 *
 * PROVISÓRIO: a identidade visual oficial ainda consta como "a definir com a
 * equipe" no FRAMEWORK.md. Todos os hexes abaixo foram amostrados das artes já
 * publicadas da marca (posts e carrosséis do LinkedIn), ou seja, refletem o que
 * está no ar, não um manual de marca aprovado. Quando a equipe fechar a paleta,
 * este arquivo é o único lugar a trocar: Aurora e CartaoTitulo leem tudo daqui.
 */
export const marca = {
  /** Azul dominante dos fundos das artes. Cor de destaque sobre fundo claro. */
  azul: "#3330BD",
  /** Azul mais claro do gradiente do logo. */
  azulVivo: "#4A57DD",
  /** Índigo sólido dos botões de CTA. */
  indigo: "#393BC6",
  /** Azul dessaturado, para a mancha mais discreta da aurora. */
  azulSuave: "#7D7DD5",
  /** Verde-água de acento, segundo tom do gradiente do logo. */
  verdeAgua: "#2DC4B2",
  /** Verde mais claro, usado em números e destaques sobre fundo escuro. */
  verdeVivo: "#4CE8AF",
  /** Azul fechado, para sombra e profundidade. */
  azulProfundo: "#2D3591",
  fundoEscuro: "#17171D",
  superficie: "#1E1E2A",
  /** Base clara dos fundos aurora, medida nas artes de fundo claro. */
  auroraBase: "#EDEDED",
  tinta: "#17171D",
  /** PENDENTE: fonte oficial não confirmada; cai para a sans do sistema. */
  fonte: '"Inter Tight", "Inter", system-ui, -apple-system, sans-serif',
} as const;
