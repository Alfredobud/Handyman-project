# Kitchen Privacy Screen — cliente Bill

**Cliente:** Bill (Cornelius, NC)  
**Status:** **rev. 9**, proposta nova pronta: mesmo desenho (7 postes, 8 ft, núcleo 4x6, 24 ripas 2x2, viga parafusada no núcleo, sem end cap) em duas opções de material.

**Documento para o cliente (EN):** [`propostas/Kitchen-Privacy-Screen-Proposal-rev9.pdf`](propostas/Kitchen-Privacy-Screen-Proposal-rev9.pdf): escopo, comparação, materiais e acabamento, preços, sequência e condições + pranchas A-1…A-3 (cedro) e B-1…B-3 (pinus)

| Opção | Desenhos (PDF/DXF) | Orçamento interno | Total |
|---|---|---|---:|
| **A — cedro aparente** (núcleo PT 4x6) | [`desenhos/rev9-a-cedro/`](desenhos/rev9-a-cedro/) | [`orcamento-c/cedro-4x6/`](orcamento-c/cedro-4x6/orcamento.md) | **$7,580** |
| **B — 100% pinus tratado** S4S (núcleo 4x6) | [`desenhos/rev9-b-pinus/`](desenhos/rev9-b-pinus/) | [`orcamento-c/pt-4x6/`](orcamento-c/pt-4x6/orcamento.md) | **$6,742** |

- Comparativo de núcleo (4x4 / 4x6 / 6x6): [`orcamento-c/comparativo-nucleo.md`](orcamento-c/comparativo-nucleo.md); o 4x6 foi escolhido (mesmo custo do 4x4, ~2.5x mais folga no nível do chão).
- Postes enterrados **36"** (furo Ø16", 6" de brita) para os 8 ft de altura.
- Para regerar: `python3 gerar_opcao_c.py` → `privacy_screen.py` em `orcamento-c/cedro-4x6` e `orcamento-c/pt-4x6` (saída `desenhos/rev9-*`) → `python3 gerar_documento_rev9.py`.
- **Histórico:** a proposta rev. 7 (10 × 7 postes, 6'-1" de altura) e os desenhos dela estão em `propostas/arquivo-rev7/` e `desenhos/arquivo-rev7/`. O plano de corte em `plano-corte/` é da rev. 7 e precisa ser regerado para a rev. 9 quando o Bill escolher a opção.

Decisões: madeira (sem composite, por receio de deformação); postes PT embutidos 36" (mínimo de 2 ft); $60/h, sem markup, taxa de $150; imposto de Mecklenburg de 8.25%.
**Referência:** [`referencias/Kitchen_Privacy_Screen_Contractor_Packet.pdf`](referencias/Kitchen_Privacy_Screen_Contractor_Packet.pdf) · imagem conceito: [`referencias/conceito-000.jpg`](referencias/conceito-000.jpg)

## Resumo do escopo (packet original do cliente — histórico; o projeto atual não usa composite)

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
