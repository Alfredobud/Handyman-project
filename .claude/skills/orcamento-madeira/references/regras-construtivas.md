# Regras práticas para orçar (não substituem cálculo estrutural)

Estas regras servem para **não esquecer material** e chegar a uma estrutura plausível. Confirme sempre com código local, fabricante e, para estruturas altas, com profissional habilitado.

## Madeira — medidas nominais × reais

| Nominal | Real |
|---|---|
| 1x4 / 1x6 / 1x8 | 0.75" × 3.5" / 5.5" / 7.25" |
| 2x4 / 2x6 / 2x8 / 2x10 | 1.5" × 3.5" / 5.5" / 7.25" / 9.25" |
| 4x4 / 6x6 | 3.5" × 3.5" / 5.5" × 5.5" |
| Composite deck board "1x6" | ~0.94" × 5.5" |

Comprimentos comerciais: PT e dimensional 8', 10', 12', 14', 16' (20' em alguns lugares); composite 12', 16', 20'.

## Cercas e privacy screens

- **Espaçamento de postes**: 6'–8' entre centros é o usual; para screens de 8' de altura com muita área de vento, prefira ≤ 6'.
- **Fundação**: profundidade ~1/3 da altura exposta (mín. abaixo da linha de congelamento local); diâmetro ~3× a largura do poste (6x6 → 16"–18"). Com base metálica (post base) sobre sapata, a sapata precisa de pino/chumbador e o fabricante limita a altura/carga — screens altos com post base sobre concreto podem não ser aprovados; enterrar o poste PT ground-contact é alternativa comum.
- **Folga do chão**: 2"–4" entre ripas/madeira e o terreno.
- **Travessas**: no mínimo superior e inferior; acima de ~6' de painel, adicione uma intermediária.
- **Ripas de composite**: composite flexiona — não use como estrutura. Regra prática: apoio a cada 16"–24" ao longo da ripa (confirme o span do fabricante para uso vertical/cerca). Vãos maiores pedem montante intermediário (2x4/2x6) no meio do vão.
- **Ripas de madeira** (cedro/PT 1x): apoio a cada ≤ 4'. Se o cliente teme empeno ou deformação, prefira **5/4x6** (1" real) a 1x6 (3/4"), porque a ripa mais espessa arqueia e encanoa bem menos. Some um montante no meio do vão (apoio a cada ~2') e use parafuso inox em todo apoio; em cedro, galvanizado mancha (tanino).
- **Espaço entre ripas**: 1/4"–1/2" para privacidade forte; 1"–2" é decorativo e deixa ver através em ângulo.
- **Expansão** (composite): folga nas pontas conforme fabricante e temperatura de instalação (tipicamente 1/8"–1/4").
- **Acabado dos dois lados**: dobra fascia/wrap e pode exigir ripas dos dois lados ou estrutura escondida no meio do painel.

## Pinus autoclavado (PT) × cedro nas partes visíveis

- O PT (SYP) chega úmido: encolhe, empena e trinca ao secar. Prefira KDAT ou deck board premium e escolha as tábuas na loja.
- O stain em PT só pode ser aplicado depois da secagem (1–3 meses): orce uma **segunda visita** + stain de tudo. Com isso, a economia do PT sobre o cedro costuma cair para poucos %.
- Poste enterrado: sempre PT ground contact (UC4B), com preservativo no corte; cedro em contato com o solo dura menos.

## Pergolados / topo estilo pergolado

- **Vigas**: normalmente duplas (uma de cada lado dos postes), aparafusadas com parafuso passante ou estrutural.
- **Balanço (overhang)** de vigas: 12"–24" além do último poste.
- **Emendas de viga**: sempre sobre um poste.
- **Caibros/rafters**: espaçamento 12"–24"; comprimento = profundidade + 2 × balanço.
- **Cortes decorativos** nas pontas: adicione mão de obra (ver produtividade).

## Decks (referência rápida)

- Joists 16" OC (composite exige 16" ou 12" em diagonal).
- Joist 2x8 vence ~12'; 2x10 ~14'–15' (PT SYP #2, 16" OC) — confirmar tabela local.
- Ledger com flashing e fixação estrutural.

## Ferragens e fixadores

- Em PT use galvanizado a quente (G185/ZMAX) ou inox; com composite use os parafusos do fabricante.
- Estime parafusos: ripa fixada em cada apoio com 2 parafusos por face.
- Litoral / próximo a água salgada: inox 316.

## Perdas típicas

| Material | Perda |
|---|---|
| Dimensional/PT | 5%–10% |
| Composite | 5%–10% |
| Madeira com cortes decorativos | 10%–15% |
| Concreto | 10% |

## Itens que costumam ser esquecidos

Blocking, montantes intermediários, sobra para emenda, sapata extra no fim da linha, parafusos estruturais, broca/serra descartável, descarte de entulho, entrega/frete, aluguel de perfuratriz (auger), licença.

## Móveis a partir de planos (cadeiras, bancos, floreiras)

- **Use a lista de corte do plano** como fonte das peças, mas refaça a lista de compra pelo script: planos costumam ignorar a espessura da serra (kerf) e às vezes listam uma tábua a menos (ex.: 36 + 30 + 30 = 96" não cabe numa 8' depois de 2 cortes).
- **Ripagem**: peça mais estreita que a tábua (ex.: 3" de uma 1x4) sai da mesma tábua sem ganho; duas peças de 3" de um 2x8 dividem o comprimento → `por_largura: 2`.
- **Nesting**: pernas e braços com corte em ângulo/curva são desenhados encaixados no diagrama de corte do plano. Use `consumo_in` com o comprimento ocupado no diagrama ou, se o plano já traz a lista de compra, componente `tabuas`.
- **Retalhos aproveitados** (ex.: brace feito da sobra da perna): não conte como corte separado; registre como premissa.
- **Tempo do plano** ("build time 1 hour") é de quem já tem as peças cortadas e a ferramenta montada. Para orçar, use a produtividade por peça + acabamento; um móvel simples de exterior fica tipicamente entre 4 e 8 h com acabamento.
- **Lote**: para várias unidades iguais, multiplique `qtd` (o encaixe entre unidades reduz a perda) e reduza a produtividade por peça em ~20%–30% a partir da 3ª unidade (gabaritos já prontos) usando `tarefa_qtd`.
- **Ferragens de móvel**: parafusos deck por caixa de 1 lb (uma caixa por bitola usada), cola PVA exterior, carriage bolts se o plano sugerir reforço, stain/selador (1 qt cobre ~1 cadeira com 2 demãos).
