# Projetos de Madeira

Hub dos orçamentos e projetos de marcenaria/carpintaria. **Cada orçamento fica na pasta do seu cliente.**

## Estrutura

```
projetos-madeira/
├── README.md                     # este índice
├── clientes/
│   └── <cliente>/                # nome do cliente em minúsculas, com hífens (ex.: bill, john-smith)
│       └── <projeto>/            # ex.: kitchen-privacy-screen
│           ├── README.md         # status, decisões, links e totais
│           ├── referencias/      # fotos, PDFs e croquis recebidos
│           ├── orcamento*/       # spec.json + orcamento.md/.xlsx/.json (uma pasta por opção)
│           ├── desenhos/         # pranchas PDF/SVG/DXF (uma subpasta por opção)
│           ├── propostas/        # documento final para o cliente
│           └── plano-corte/      # plano de corte da oficina (quando aprovado)
└── referencias/                  # material genérico, sem cliente (ex.: planos de cadeira)
```

## Clientes e projetos

| Cliente | Projeto | Status | Proposta |
|---|---|---|---|
| Bill | [Kitchen Privacy Screen](clientes/bill/kitchen-privacy-screen/) | Proposta enviada (A: 10 postes cedro $8,211 · B: 7 postes pinus tratado $5,881); plano de corte da opção B pronto | [PDF](clientes/bill/kitchen-privacy-screen/propostas/Kitchen-Privacy-Screen-Proposals.pdf) |

## Referências

- [`referencias/planos/`](referencias/planos/): planos de cadeira Adirondack (YellaWood e Rogue Engineer).

## Skills

- [`orcamento-madeira`](../.claude/skills/orcamento-madeira/SKILL.md): orçamento (materiais + mão de obra) a partir de fotos, PDFs ou croquis.
- [`desenho-madeira`](../.claude/skills/desenho-madeira/SKILL.md): pranchas técnicas 2D (PDF/SVG/DXF) a partir do mesmo `spec.json`.
