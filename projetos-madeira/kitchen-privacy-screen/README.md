# Kitchen Privacy Screen

**Status:** rev. 7 aprovada: documento final com as duas propostas e as pranchas

**Documento para o cliente (EN):** [`propostas/Kitchen-Privacy-Screen-Proposals.pdf`](propostas/Kitchen-Privacy-Screen-Proposals.pdf): comparação, materiais e acabamento, opções A e B, sequência, condições + pranchas A-1…A-3 (10 postes) e B-1…B-3 (7 postes)

| Opção | Desenhos (PDF/DXF) | Orçamento interno | Total |
|---|---|---|---:|
| **A — 10 postes** (vão/poste = φ³, vão 23 5/16") | [`desenhos/10-postes/`](desenhos/10-postes/) | [`orcamento/`](orcamento/orcamento.md) | **$8,211** |
| **B — 7 postes** (vão/poste = φ⁴, vão 37 3/4") | [`desenhos/7-postes/`](desenhos/7-postes/) | [`orcamento-7-postes/`](orcamento-7-postes/orcamento.md) | **$6,631** |
| 10 postes, 100% PT (referência interna) | — | [`orcamento-pt/`](orcamento-pt/orcamento.md) | $7,101 |

Materiais: núcleos dos postes (enterrados 24") em **pinus tratado (PT SYP #2, ground contact)**; tudo o que é aparente em **cedro Western Red, seco em estufa, aplainado S4S**. Na Lowe's o cedro 2x6/2x8 costuma ser bruto/green: comprar S4S em madeireira.

Para regerar tudo: `python3 gerar_propostas.py` → `orcamento.py` em cada pasta → `privacy_screen.py` para `desenhos/10-postes` e `desenhos/7-postes` → `python3 gerar_documento_propostas.py`.

Decisões: madeira (sem composite, por receio de deformação); postes PT embutidos 36" (mínimo de 2 ft); $60/h, sem markup, taxa de $150; imposto de Mecklenburg de 8.25%.
**Referência:** [`referencias/Kitchen_Privacy_Screen_Contractor_Packet.pdf`](referencias/Kitchen_Privacy_Screen_Contractor_Packet.pdf) · imagem conceito: [`referencias/conceito-000.jpg`](referencias/conceito-000.jpg)

## Resumo do escopo

- Comprimento: **265 in (22 ft 1 in)**, linha reta
- Altura acabada: **~8 ft**
- Objetivo: bloquear a visão entre a casa vizinha e a janela da cozinha, acabamento bonito dos dois lados, pouca manutenção
- Estrutura em madeira tratada (PT); ripas horizontais e acabamento em **Trex/composite**
- Topo decorativo estilo pergolado
- Opcional: manta, borda e pedra de rio na base; previsão para trepadeiras

## Lista de materiais (do packet)

| Qtd | Material | Uso |
|---|---|---|
| 6 | Poste PT 6x6x10' | Estrutura principal |
| 12 | PT 2x6x8' | Travessas estruturais |
| 8 | PT 2x6x4' | Bloqueios / requadro |
| ~65 | Trex/composite ~1x4 | Ripas horizontais |
| 2 | 2x8x12' estrutural | Viga do pergolado |
| 2 | 2x8x10' estrutural | Viga do pergolado |
| ~14 | 2x4 composite ou PT | Caibros decorativos do topo |
| 6 | Base de poste 6x6 galvanizada/inox | Elevar poste do concreto |
| Conf. | Concreto, fixadores inox, fascia/wrap composite, manta/borda/pedra | — |

## Observações / pontos a verificar

1. **Imagem vs. texto:** a imagem conceito diz "100% Natural Cedar", mas o packet pede PT + Trex/composite. Confirmar com o cliente qual material vale para o orçamento.
2. **Número de postes:** a imagem mostra ~10–11 postes; o packet lista 6 (vãos de ~53"). Ripas composite normalmente pedem vãos menores (ver span do fabricante) — pode exigir postes intermediários ou montantes 2x4/2x6 extras.
3. **Quantidade de ripas:** ~65 parece baixa. Com ripa de ~3.5" + vão de 1.5–2" em ~90" de altura ≈ 16–17 fiadas × comprimento total de 265" → recalcular pelo comprimento comercial (12'/16'/20') e pelas emendas nos postes.
4. Cliente pede **mão de obra e materiais separados**, com produto/cor exata do composite.
5. Antes de obra: utilidades subterrâneas (811), divisa/recuo, licença/HOA, fundações, vento.

## Próximos passos

- [x] Definir material final → madeira (sem composite, por receio de deformação)
- [ ] Definir espaçamento de postes e recalcular lista
- [x] Levantar preços online (Lowe's / Home Depot) — [ ] confirmar na loja de Cornelius, principalmente o cedro 2x8x12
- [x] Estimar horas de mão de obra (67.8 h)
- [ ] Montar proposta (materiais + mão de obra separados)
