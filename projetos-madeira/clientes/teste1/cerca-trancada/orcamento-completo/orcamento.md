# Orçamento — Cerca trançada — estudo de 1 módulo (cliente teste1)

**Cliente:** teste1

## Resumo

| | Valor |
|---|---:|
| Materiais (subtotal loja) | $4,268.40 |
| Imposto sobre material (8.25%) | $352.14 |
| **Total materiais** | **$4,620.54** |
| Mão de obra (117.7 h × $60.00/h) | $7,059.00 |
| **Total mão de obra** | **$7,059.00** |
| **Taxa** | **$150.00** |
| **TOTAL** | **$11,829.54** |

## Lista de compra

| Material | Compr. | Qtd | Unit. | Subtotal | Obs. | Fonte do preço |
|---|---:|---:|---:|---:|---|---|
| Pinus tratado 6x6 #2 ground contact UC4B S4S | 8' | 15 | $38.00 | $570.00 |  | referencia-media-big-box (conferir) |
| Pinus tratado 1x6 S4S (tábua de cerca/aparência) | 10' | 177 | $9.00 | $1,593.00 | inclui 9 de sobra (5%) | estimativa (conferir loja) |
| Pinus tratado 1x2 S4S | 8' | 103 | $3.00 | $309.00 | inclui 5 de sobra (5%) | estimativa (conferir loja) |
| PT 2x4 #2 Prime ground contact S4S | 10' | 30 | $8.88 | $266.40 | inclui 2 de sobra (5%) | homedepot.com online (Cornelius nao confirmado) |
| PT 2x6 | 10' | 15 | $12.50 | $187.50 | inclui 1 de sobra (5%) | referencia-media-big-box |
| Concreto ensacado 80 lb (~0.60 cf) |  | 31 | $6.50 | $201.50 | saco — Furos Ø12" x 30" — concreto | referencia-media-big-box |
| Brita/cascalho ensacado 0.5 cf |  | 12 | $5.50 | $66.00 | saco — Brita no fundo dos furos | referencia-media-big-box |
| Parafuso deck trim-head revestido p/ PT/ACQ (caixa 5 lb) |  | 4 | $42.00 | $168.00 | caixa — Parafusos deck trim-head (ocultos) | referencia-media-big-box |
| Stain/selador externo 1 gal (~250 sqft/demão) |  | 8 | $45.00 | $360.00 | galao — Stain semi-transparente (2 faces, 1 demão após secagem) | referencia-media-big-box |
| Aluguel mini skid steer com auger 12in — 1 dia |  | 1 | $350.00 | $350.00 | dia — Locação: mini skid steer com auger 12" (1 dia) | estimativa locadora local (conferir) |
| Entrega/retirada do equipamento alugado |  | 1 | $100.00 | $100.00 | verba — Entrega/retirada do equipamento | estimativa locadora local (conferir) |
| Preservativo para corte de PT (copper naphthenate) 1 qt |  | 1 | $22.00 | $22.00 | un — Preservativo nos cortes do PT | referencia-media-big-box |
| Descarte de entulho / caçamba pequena |  | 1 | $75.00 | $75.00 | verba — Descarte | referencia-media-big-box |

## Cálculos derivados

- **Furos Ø12" x 30" — concreto**: volume_cf = 18.19, sacos = 31

## Peças (lista de corte)

| Peça | Material | Qtd | Compr. (in) | Obs. |
|---|---|---:|---:|---|
| Postes pinus tratado 6x6 ground contact (embutir 24") | pt_6x6 | 15 | 96 |  |
| Tábuas trançadas 1x6 (12/módulo) | pt_1x6 | 168 | 115.75 |  |
| Sarrafos verticais do trançado 1x2 (3/módulo) | pt_1x2 | 42 | 66 |  |
| Batentes do canal nos postes 1x2 (4/módulo) | pt_1x2 | 56 | 66 |  |
| Travessas 2x4 (inferior + superior) | pt_2x4 | 28 | 114.5 |  |
| Capeamento 2x6 (emenda sobre poste) | pt_2x6 | 14 | 120 |  |

## Plano de corte (sem a sobra de perda)

| Material | Tábuas | Compr. | Cortes por tábua | Sobra/tábua (in) |
|---|---:|---:|---|---:|
| pt_6x6 | 15 | 8' | 1x 96" Postes pinus tratado 6x6 ground contact (embutir 24") | 0 |
| pt_1x6 | 168 | 10' | 1x 115.75" Tábuas trançadas 1x6 (12/módulo) | 4.25 |
| pt_1x2 | 42 | 8' | 1x 66" Sarrafos verticais do trançado 1x2 (3/módulo) | 30 |
| pt_1x2 | 56 | 8' | 1x 66" Batentes do canal nos postes 1x2 (4/módulo) | 30 |
| pt_2x4 | 28 | 10' | 1x 114.5" Travessas 2x4 (inferior + superior) | 5.5 |
| pt_2x6 | 14 | 10' | 1x 120" Capeamento 2x6 (emenda sobre poste) | 0 |

## Mão de obra

| Tarefa | Qtd | Unid. | h/unid. | Horas |
|---|---:|---|---:|---:|
| obra_assentar_poste | 15 | poste | 0.45 | 6.8 |
| obra_nivelar_topo | 15 | poste | 0.15 | 2.2 |
| obra_tabua_trancada | 168 | peca | 0.12 | 20.2 |
| obra_sarrafo_trama | 42 | peca | 0.1 | 4.2 |
| obra_batente | 56 | peca | 0.08 | 4.5 |
| obra_travessa_cerca | 28 | peca | 0.25 | 7.0 |
| obra_capa | 14 | peca | 0.3 | 4.2 |
| acabamento_stain | 1790 | sqft | 0.02 | 35.8 |
| obra_transporte_equipamento | 1 | verba | 1 | 1.0 |
| obra_escavacao_mecanizada | 15 | furo | 0.15 | 2.2 |
| oficina_corte | 308 | peca | 0.04 | 12.3 |
| oficina_acabamento_lixa | 308 | peca | 0.03 | 9.2 |
| locacao | 1 | verba | 1 | 1.0 |
| compras_transporte | 1 | verba | 3 | 3.0 |
| limpeza | 1 | verba | 2 | 2.0 |
| Visita de retorno para stain após secagem | 2 | h | 1 | 2.0 |
| **Total** | | | | **117.7** |

## Premissas

- Módulo 120" (10'-0" = 3.05 m) entre eixos: trechos 40'/60'/40' = [4, 6, 4] módulos idênticos, 15 postes.
- Altura total 6'-1 1/2": módulo/altura = 1.633 (φ = 1.618). 12 tábuas 1x6 por módulo.
- Folga de 3" entre a travessa inferior e o terreno.
- Tudo em pinus tratado aplainado S4S; postes 6x6 ground contact embutidos 24" em concreto sobre 6" de brita.
- Trançado montado na obra: travessa inferior + sarrafos, tábuas descem pelo canal dos postes alternando frente/trás; peças pré-cortadas na oficina.
- Stain semi-transparente nas 2 faces em visita após secagem (pinus tratado chega úmido).
- PRELIMINAR: estudo de módulo; preços de 1x6, 1x2 e 6x6 estimados.
- Inclui locação do equipamento, mobilização, compras, limpeza e visita do stain.

## Perguntas / verificações de campo

- [ ] Altura: 6'-1 1/2" (proporção áurea). HOA/código de Cornelius costuma limitar cerca lateral/fundo a 6'-0"?
- [ ] Iluminação LED atrás das tábuas (como na foto): incluir?
- [ ] Portão(ões): quantos e onde?
- [ ] Terreno plano ou com desnível (degraus nos módulos)?

## Fontes de preço

- estimativa (conferir loja) (2026-11)
- estimativa locadora local (conferir) (2026-11)
- homedepot.com online (Cornelius nao confirmado) (2026-11)
- referencia-lowes-online (2026-11)
- referencia-media-big-box (2026-11)
- referencia-media-big-box (conferir) (2026-11)

_Preços de referência devem ser confirmados na loja/região antes da proposta final. Dimensionamento estrutural, licença/HOA, utilidades subterrâneas (811) e especificações do fabricante devem ser verificados antes da obra._
