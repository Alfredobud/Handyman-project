# Orçamento — Cerca trançada — estudo de 1 módulo (cliente teste1)

**Cliente:** teste1

## Resumo

| | Valor |
|---|---:|
| Materiais (subtotal loja) | $342.64 |
| Imposto sobre material (8.25%) | $28.27 |
| **Total materiais** | **$370.91** |
| Mão de obra (7.7 h × $60.00/h) | $462.60 |
| **Total mão de obra** | **$462.60** |
| **Taxa** | **$150.00** |
| **TOTAL** | **$983.51** |

## Lista de compra

| Material | Compr. | Qtd | Unit. | Subtotal | Obs. | Fonte do preço |
|---|---:|---:|---:|---:|---|---|
| Pinus tratado 6x6 #2 ground contact UC4B S4S | 8' | 1 | $38.00 | $38.00 |  | referencia-media-big-box (conferir) |
| Pinus tratado 1x6 S4S (tábua de cerca/aparência) | 10' | 13 | $9.00 | $117.00 | inclui 1 de sobra (5%) | estimativa (conferir loja) |
| Pinus tratado 1x2 S4S | 8' | 8 | $3.00 | $24.00 | inclui 1 de sobra (5%) | estimativa (conferir loja) |
| PT 2x4 #2 Prime ground contact S4S | 10' | 3 | $8.88 | $26.64 | inclui 1 de sobra (5%) | homedepot.com online (Cornelius nao confirmado) |
| PT 2x6 | 10' | 2 | $12.50 | $25.00 | inclui 1 de sobra (5%) | referencia-media-big-box |
| Concreto ensacado 80 lb (~0.60 cf) |  | 3 | $6.50 | $19.50 | saco — Furos Ø12" x 30" — concreto | referencia-media-big-box |
| Brita/cascalho ensacado 0.5 cf |  | 1 | $5.50 | $5.50 | saco — Brita no fundo dos furos | referencia-media-big-box |
| Parafuso deck trim-head revestido p/ PT/ACQ (caixa 5 lb) |  | 1 | $42.00 | $42.00 | caixa — Parafusos deck trim-head (ocultos) | referencia-media-big-box |
| Stain/selador externo 1 gal (~250 sqft/demão) |  | 1 | $45.00 | $45.00 | galao — Stain semi-transparente (2 faces, 1 demão após secagem) | referencia-media-big-box |

## Cálculos derivados

- **Furos Ø12" x 30" — concreto**: volume_cf = 1.21, sacos = 3

## Peças (lista de corte)

| Peça | Material | Qtd | Compr. (in) | Obs. |
|---|---|---:|---:|---|
| Postes pinus tratado 6x6 ground contact (embutir 24") | pt_6x6 | 1 | 96 |  |
| Tábuas trançadas 1x6 (12/módulo) | pt_1x6 | 12 | 115.75 |  |
| Sarrafos verticais do trançado 1x2 (3/módulo) | pt_1x2 | 3 | 66 |  |
| Batentes do canal nos postes 1x2 (4/módulo) | pt_1x2 | 4 | 66 |  |
| Travessas 2x4 (inferior + superior) | pt_2x4 | 2 | 114.5 |  |
| Capeamento 2x6 (emenda sobre poste) | pt_2x6 | 1 | 120 |  |

## Plano de corte (sem a sobra de perda)

| Material | Tábuas | Compr. | Cortes por tábua | Sobra/tábua (in) |
|---|---:|---:|---|---:|
| pt_6x6 | 1 | 8' | 1x 96" Postes pinus tratado 6x6 ground contact (embutir 24") | 0 |
| pt_1x6 | 12 | 10' | 1x 115.75" Tábuas trançadas 1x6 (12/módulo) | 4.25 |
| pt_1x2 | 3 | 8' | 1x 66" Sarrafos verticais do trançado 1x2 (3/módulo) | 30 |
| pt_1x2 | 4 | 8' | 1x 66" Batentes do canal nos postes 1x2 (4/módulo) | 30 |
| pt_2x4 | 2 | 10' | 1x 114.5" Travessas 2x4 (inferior + superior) | 5.5 |
| pt_2x6 | 1 | 10' | 1x 120" Capeamento 2x6 (emenda sobre poste) | 0 |

## Mão de obra

| Tarefa | Qtd | Unid. | h/unid. | Horas |
|---|---:|---|---:|---:|
| obra_assentar_poste | 1 | poste | 0.45 | 0.5 |
| obra_nivelar_topo | 1 | poste | 0.15 | 0.1 |
| obra_tabua_trancada | 12 | peca | 0.12 | 1.4 |
| obra_sarrafo_trama | 3 | peca | 0.1 | 0.3 |
| obra_batente | 4 | peca | 0.08 | 0.3 |
| obra_travessa_cerca | 2 | peca | 0.25 | 0.5 |
| obra_capa | 1 | peca | 0.3 | 0.3 |
| acabamento_stain | 128 | sqft | 0.02 | 2.6 |
| obra_escavacao_mecanizada | 1 | furo | 0.15 | 0.1 |
| oficina_corte | 22 | peca | 0.04 | 0.9 |
| oficina_acabamento_lixa | 22 | peca | 0.03 | 0.7 |
| **Total** | | | | **7.7** |

## Premissas

- Módulo 120" (10'-0" = 3.05 m) entre eixos: trechos 40'/60'/40' = [4, 6, 4] módulos idênticos, 15 postes.
- Altura total 6'-1 1/2": módulo/altura = 1.633 (φ = 1.618). 12 tábuas 1x6 por módulo.
- Folga de 3" entre a travessa inferior e o terreno.
- Tudo em pinus tratado aplainado S4S; postes 6x6 ground contact embutidos 24" em concreto sobre 6" de brita.
- Trançado montado na obra: travessa inferior + sarrafos, tábuas descem pelo canal dos postes alternando frente/trás; peças pré-cortadas na oficina.
- Stain semi-transparente nas 2 faces em visita após secagem (pinus tratado chega úmido).
- PRELIMINAR: estudo de módulo; preços de 1x6, 1x2 e 6x6 estimados.
- Orçamento de 1 módulo = módulo + 1 poste, sem locação/mobilização (essas entram só no completo).

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
