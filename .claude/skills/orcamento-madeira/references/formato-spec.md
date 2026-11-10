# Formato do `spec.json`

Exemplo completo: `assets/exemplo-spec.json` (privacy screen com pergolado). Medidas em **polegadas** (`_in`), comprimentos comerciais em **pés** (`_ft`), preços em USD.

```json
{
  "projeto": "Nome do projeto",
  "cliente": "opcional",
  "precos": "precos.csv",              // opcional: CSV do projeto, relativo ao spec; sobrescreve o catálogo base por id
  "parametros": {                      // todos opcionais (padrões abaixo)
    "taxa_hora_usd": 65,
    "perda": 0.05,                     // sobra extra DEPOIS da otimização de cortes
    "kerf_in": 0.125,
    "markup_material": 0.15,
    "imposto_material": 0.0,
    "contingencia": 0.10,
    "comprimento_max_ft": 8,           // opcional: só compra tábuas até esse tamanho (transporte)
    "taxa_fixa_usd": 150,              // opcional: taxa fixa somada ao total (ex.: no lugar do markup)
    "taxa_fixa_descricao": "Taxa de serviço"
  },
  "componentes": [ ... ],
  "tarefas_extra": [
    {"tarefa": "locacao", "qtd": 1},
    {"descricao": "Ajuste no campo", "horas": 2}   // horas diretas, sem tabela de produtividade
  ],
  "premissas": ["texto", "..."],
  "perguntas": ["texto", "..."]
}
```

## Componentes

Campos comuns: `tipo`, `nome`, `material` (id do `precos.csv`), `tarefa` (id do `produtividade.csv`, opcional), `tarefa_qtd` (opcional; por padrão = nº de peças/unidades), `perda` (sobrescreve a perda padrão para esse material).

### `pecas` — peças de comprimento definido
```json
{"tipo": "pecas", "nome": "Travessa", "material": "pt_2x6", "comprimento_in": 46.4, "qtd": 15, "tarefa": "travessa"}
```
Opcionais:
- `por_largura`: quantas peças saem lado a lado da largura da tábua (rip). Ex.: duas ripas de 3" de um 2x8 ripado ao meio → `"por_largura": 2`; as 2 peças ocupam um único trecho de comprimento.
- `consumo_in`: comprimento de tábua realmente ocupado por trecho, quando é diferente do comprimento da peça. Use para **peças com corte em ângulo encaixadas** (ex.: duas pernas de 33.5" invertidas que ocupam 55" juntas → `qtd: 2, por_largura: 2, consumo_in: 55`). Também serve para incluir uma folga de acerto.

Cortes maiores que a maior tábua comercial geram aviso: divida a peça no spec, com a emenda sobre um apoio.

### `ripado` — painel de ripas
```json
{"tipo": "ripado", "nome": "Ripas", "material": "composite_1x6",
 "vao_in": 46.4, "n_vaos": 5,           // ou "vaos_in": [46.4, 46.4, 40]
 "altura_in": 84, "largura_peca_in": 5.5,
 "espaco_min_in": 1.5, "espaco_max_in": 2.0,   // ou "espaco_in": 1.75 (espaço fixo)
 "lados": 1, "tarefa": "ripa_composite"}
```
Com `espaco_min_in`, o script usa o máximo de fiadas que respeita o espaço mínimo e redistribui o espaço para cobrir a altura toda (informa `espaco_real_in`). Com `espaco_in` fixo, a altura coberta pode sobrar (informa `altura_coberta_in`). `lados: 2` dobra as ripas (screen acabado com ripa dos dois lados).

### `sapata` — fundação cilíndrica
```json
{"tipo": "sapata", "nome": "Sapatas", "qtd": 6, "diametro_in": 16, "profundidade_in": 42,
 "material": "concreto_80lb", "rendimento_cf": 0.60, "desconto_poste_in2": 30.25, "tarefa": "poste_sapata"}
```
`desconto_poste_in2` = área do poste enterrado (6x6 → 30.25), para descontar o volume dele. Saco de 80 lb ≈ 0.60 cf; 60 lb ≈ 0.45 cf.

### `tabuas` — compra direta
Quando o plano já traz a lista de compra e o encaixe das peças não é linear (muitos cortes em ângulo/nesting), use a quantidade do plano:
```json
{"tipo": "tabuas", "nome": "Deck boards (lista do plano)", "material": "pt_5_4x6", "comprimento_ft": 8, "qtd": 3}
```

### `item` — por unidade
```json
{"tipo": "item", "nome": "Bases de poste", "material": "post_base_6x6", "qtd": 6, "tarefa": "poste_base_metalica"}
```

## Catálogo de preços (`precos.csv`)

`id,descricao,unidade,comprimento_ft,preco_usd,fonte,data`. Material linear tem uma linha por comprimento comercial; item unitário deixa `comprimento_ft` vazio. Para um projeto, crie um `precos.csv` ao lado do spec só com as linhas que mudaram (mesmo `id` e `comprimento_ft`), ou com ids novos.
