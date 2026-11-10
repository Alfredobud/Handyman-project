---
name: orcamento-madeira
description: Monta orçamentos (materiais + mão de obra) de produtos e estruturas em madeira a partir de fotos, imagens conceito, croquis ou PDFs de projeto — cercas, privacy screens, pergolados, decks, trellis, floreiras, bancos, prateleiras, móveis simples, em madeira maciça, tratada (PT), cedro ou composite/Trex. Faz a leitura da imagem, estima medidas e quantidades, gera lista de corte, lista de compra em tamanhos comerciais (8'/10'/12'/16'...), custo de material, horas de mão de obra e proposta com materiais e mão de obra separados. Use sempre que o usuário enviar foto/imagem/PDF de algo em madeira e pedir preço, orçamento, quote, bid, estimate, lista de materiais, "quanto custa fazer", "quanto cobrar", ou quiser conferir a lista de materiais de um contractor packet — mesmo que não diga a palavra "orçamento".
---

# Orçamento de produtos em madeira

Objetivo: transformar uma referência visual (foto, imagem conceito, PDF) em um orçamento defensável — com quantidades que um carpinteiro reconheceria como corretas, preços rastreáveis e premissas explícitas. O valor do orçamento está menos no número final e mais em mostrar **de onde ele vem**, para que o handyman possa ajustar no campo e o cliente confie na proposta.

## Fluxo

### 1. Entender a referência

Leia todas as entradas (fotos, PDFs — extraia imagens embutidas com `pdfimages -j` e texto com `pdftotext -layout`). Anote:

- **Tipo de produto** e partes que o compõem (estrutura, vedação/ripado, topo, acabamento, ferragens, fundação, paisagismo).
- **Medidas declaradas** (texto, cotas). Medidas escritas valem mais que medidas estimadas da foto.
- **Medidas estimadas** pela imagem, usando referências de escala — veja `references/leitura-fotos.md`. Sempre diga qual referência usou e a faixa de incerteza.
- **Material** e acabamento (PT, cedro, composite, pintura/stain).
- **Inconsistências** entre imagem e texto (ex.: imagem mostra 11 postes, lista diz 6; imagem diz cedro, texto diz composite). Imagens conceito geradas por IA ou de catálogo frequentemente não batem com o escopo escrito — o escopo escrito manda, mas a divergência vira pergunta ao cliente.

### 2. Projetar o suficiente para quantificar

Um orçamento por "olhômetro" erra porque esquece peças que não aparecem na foto (travessas atrás do ripado, apoio intermediário, blocking, emendas). Antes de contar material, decida a estrutura mínima que funciona: espaçamento de postes, vão livre das ripas, onde ficam as emendas, como a peça é fixada. Use as regras práticas de `references/regras-construtivas.md` e registre cada decisão como premissa.

Se a referência deixar uma decisão em aberto que muda muito o preço (material, altura, número de lados acabados), não trave: escolha a opção mais provável, orce, e liste a alternativa com o impacto aproximado.

### 3. Escrever a especificação (JSON)

Descreva o projeto em um arquivo `spec.json` no formato documentado em `references/formato-spec.md` (há um exemplo completo em `assets/exemplo-spec.json`). Componentes disponíveis:

- `pecas` — peças com comprimento definido (postes, vigas, caibros, travessas, peças de móvel). Aceita `por_largura` (peças ripadas lado a lado) e `consumo_in` (peças em ângulo encaixadas que ocupam menos tábua que a soma dos comprimentos).
- `ripado` — painel de ripas: o script calcula fiadas a partir de altura, largura da ripa e espaço mínimo/máximo, e gera os cortes por vão.
- `sapata` — fundações cilíndricas: calcula volume e sacos de concreto.
- `tabuas` — compra direta, quando o diagrama de corte do plano já resolve o encaixe.
- `item` — itens por unidade (ferragens, caixas de parafuso, sacos de pedra, verbas).

Cada componente pode ter uma `tarefa` de mão de obra; as horas vêm de `references/produtividade.csv`. Se o usuário tiver limite de transporte ("vou de carro"), use `parametros.comprimento_max_ft`.

**Móveis a partir de planos** (cadeira Adirondack, banco, floreira): o plano já traz a lista de corte — use-a como fonte das peças, mas recalcule a compra pelo script, porque planos costumam ignorar o kerf. Leia a seção "Móveis a partir de planos" de `regras-construtivas.md`; o tempo de construção divulgado nesses planos é otimista demais para orçar.

### 4. Rodar o cálculo

```bash
python3 <skill>/scripts/orcamento.py spec.json --saida <pasta-do-projeto>/orcamento
```

O script:
- otimiza os cortes em tamanhos comerciais (first-fit decreasing + redução para o menor comprimento que serve, com perda de serra),
- aplica perda/sobra, preço do catálogo (`references/precos.csv`, ou o arquivo indicado em `precos` no spec), markup e contingência,
- soma horas por tarefa × taxa horária,
- gera `orcamento.md` (resumo legível), `orcamento.xlsx` (abas Resumo, Compra, Cortes, Mão de obra) e `orcamento.json`.

Ele avisa quando um material não está no catálogo ou quando um corte é maior que a maior peça comercial (precisa de emenda — resolva no spec, dividindo a peça sobre um apoio).

### 5. Conferir e apresentar

Releia o resultado com olho de carpinteiro antes de entregar: as quantidades fazem sentido comparadas à lista do cliente? Se a sua conta diverge muito de uma lista fornecida, explique por quê (normalmente a lista esqueceu estrutura escondida ou contou ripas por peça e não por fiada).

Na resposta ao usuário, entregue:
1. Total de **materiais** e total de **mão de obra** separados (prática comum em quotes nos EUA e frequentemente pedida explicitamente).
2. Premissas principais e a faixa de incerteza.
3. Perguntas para o cliente / verificações de campo que podem mudar o preço.
4. Caminho dos arquivos gerados.

## Preços

Os preços em `references/precos.csv` são **referência aproximada** e têm data e fonte em cada linha. Preço de madeira varia muito por região e mês. Quando o usuário informar a região/loja, ou quando o orçamento for virar proposta real, atualize os preços (pesquisa web ou valores que o usuário passar) e grave num `precos.csv` próprio do projeto, apontado pelo campo `precos` do spec — assim o catálogo base não é alterado e o orçamento fica reproduzível. Sempre diga ao usuário quais preços são de referência e quais foram confirmados.

## Idioma

Escreva para o handyman no idioma da conversa. Se o usuário pedir a proposta para o cliente final, gere-a no idioma do cliente (o contractor packet é um bom indicativo) usando o modelo `assets/proposta-cliente.md`.

## Segurança e escopo

Estruturas altas expostas a vento (cercas/screens > 6 ft, pergolados) dependem de fundação e fixação adequadas. Os dimensionamentos de `regras-construtivas.md` são regras práticas para orçar, não cálculo estrutural. Sempre inclua no orçamento a ressalva de verificação de código local, licença/HOA, utilidades subterrâneas (811) e especificações do fabricante.
