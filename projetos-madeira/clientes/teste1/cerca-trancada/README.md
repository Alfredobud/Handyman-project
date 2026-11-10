# Cerca trançada — cliente teste1

**Status:** estudo de **1 módulo** (prévia, sem PDF final). Definir os detalhes com o cliente antes do projeto completo.
**Referência:** [`referencias/referencia-cerca-trancada.jpg`](referencias/referencia-cerca-trancada.jpg): cerca horizontal trançada (tábuas passam na frente e atrás de sarrafos verticais), com capeamento e LED.

## Premissas do módulo (rev. 0)
| Item | Definição |
|---|---|
| Trechos | laterais de 40' + fundo de 60' (em "U", aberto para a casa) |
| Módulo | **10'-0" entre eixos (3.05 m)**: o único entre 2.5 e 3 m que divide 40' e 60' exatamente → 4 + 6 + 4 = **14 módulos iguais, 15 postes** |
| Altura | **6'-1 1/2"** → módulo/altura = 1.633 ≈ φ (1.618) |
| Folga do terreno | 3" sob a travessa inferior |
| Postes | pinus tratado 6x6 ground contact, 8', embutidos 24" em concreto (furo Ø12") sobre 6" de brita |
| Trançado | 12 tábuas 1x6 por módulo, 3 sarrafos 1x2 verticais (2'-4 5/8" entre si), canal de 2 1/4" com batentes 1x2 nos postes |
| Estrutura | travessa 2x4 inferior e superior, capeamento 2x6 contínuo |
| Material | tudo em pinus tratado aplainado S4S, sem composite; stain semi-transparente após secagem |

## Orçamento preliminar
| | Materiais | Mão de obra | Total |
|---|---:|---:|---:|
| [1 módulo + 1 poste](orcamento-modulo/orcamento.md) (sem mobilização) | $371 | $463 (7.7 h) | $984 |
| [Cerca completa, 140 ft](orcamento-completo/orcamento.md) (14 módulos, 15 postes) | $4,621 | $7,059 (118 h) | **$11,830** (~$845/módulo) |

Specs gerados por `gerar_specs.py` a partir da geometria do desenho (`.claude/skills/desenho-madeira/templates/cerca_trancada.py`).

## A definir
- [ ] Altura: 6'-1 1/2" pela proporção áurea; o HOA ou o código local limita a 6'-0"?
- [ ] Iluminação LED atrás das tábuas (como na foto)?
- [ ] Portões: quantos e onde?
- [ ] Terreno plano ou com desnível (escalonar os módulos)?
- [ ] Stain: pincel (~36 h) × pistola (~18 h) × natural sem stain
- [ ] Espessura da tábua (1x6 de 3/4") × 5/8" (trança com mais facilidade)
