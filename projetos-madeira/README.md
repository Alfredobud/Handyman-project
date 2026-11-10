# Projetos de Madeira

Pasta para projetos de marcenaria/carpintaria externa e interna (cercas, privacy screens, pergolados, decks, móveis).

## Estrutura padrão de cada projeto

```
projetos-madeira/
└── <nome-do-projeto>/
    ├── README.md        # escopo, medidas, status, decisões
    ├── referencias/     # fotos, PDFs, imagens conceito
    └── orcamento/       # lista de materiais, custos, mão de obra
```

## Projetos

| Projeto | Status | Descrição |
|---|---|---|
| [kitchen-privacy-screen](kitchen-privacy-screen/) | Orçamento preliminar | Privacy screen horizontal 265" x ~8 ft com topo estilo pergolado — [orçamento](kitchen-privacy-screen/orcamento/orcamento.md) · [desenhos](kitchen-privacy-screen/desenhos/privacy-screen.pdf) |

## Planos de referência

Em [`planos-referencia/`](planos-referencia/): planos de cadeira Adirondack (YellaWood e Rogue Engineer), usados também como casos de teste da skill.

## Skills

- [`desenho-madeira`](../.claude/skills/desenho-madeira/SKILL.md): pranchas técnicas 2D (PDF/SVG/DXF) a partir do mesmo `spec.json`.

### Orçamento

A skill [`orcamento-madeira`](../.claude/skills/orcamento-madeira/SKILL.md) monta orçamentos a partir de fotos, imagens ou PDFs. Fluxo: ler a referência → escrever `spec.json` → rodar o script:

```bash
python3 .claude/skills/orcamento-madeira/scripts/orcamento.py projetos-madeira/<projeto>/orcamento/spec.json --saida projetos-madeira/<projeto>/orcamento
```

Gera `orcamento.md`, `orcamento.xlsx` e `orcamento.json`. Preços de referência ficam em `.claude/skills/orcamento-madeira/references/precos.csv`; horas por tarefa em `produtividade.csv`.
