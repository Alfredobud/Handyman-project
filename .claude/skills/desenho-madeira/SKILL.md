---
name: desenho-madeira
description: Gera desenhos técnicos 2D estilo CAD (pranchas com elevação, planta, cortes, detalhes, cotas, lista de peças e carimbo) de produtos e estruturas em madeira — privacy screens, cercas, pergolados, decks, floreiras, bancos, cadeiras e móveis simples — em PDF, SVG e DXF (abre no AutoCAD, LibreCAD, SketchUp, Fusion). Usa o mesmo spec.json da skill orcamento-madeira, então desenho e orçamento ficam coerentes. Use sempre que o usuário pedir desenho, planta, projeto, croqui técnico, corte, elevação, detalhe construtivo, shop drawing, "como um CAD", DXF, ou quiser mostrar ao cliente/equipe como a peça será construída — mesmo sem dizer "CAD".
---

# Desenho técnico de projetos em madeira

Objetivo: pranchas que um carpinteiro consiga usar na obra e que o cliente entenda: vistas em escala, cotas em pés e polegadas, materiais diferenciados, cortes mostrando como as peças se encaixam e uma lista de peças coerente com o orçamento.

## Fluxo

1. **Partir do spec.** Se o projeto já tem `spec.json` (skill `orcamento-madeira`), use-o. As dimensões de desenho ficam no bloco `"geometria"` do spec, para que orçamento e desenho mudem juntos. Se não houver spec, crie um com pelo menos `projeto` e `geometria`.
2. **Escolher o template** em `templates/`:
   - `privacy_screen.py`: cerca ou privacy screen de ripas horizontais entre postes, com topo pergolado opcional (vigas duplas e caibros), postes embutidos em sapata de concreto.
   - Produto sem template: escreva um novo em `templates/<produto>.py` usando `scripts/cad.py`, seguindo `references/como-criar-template.md`. Copie a estrutura do `privacy_screen.py` (classe de geometria → funções de vista → `main` com pranchas).
3. **Rodar:**
   ```bash
   pip install ezdxf   # uma vez, para exportar DXF (sem ele, saem só PDF/SVG)
   python3 <skill>/templates/privacy_screen.py <projeto>/orcamento/spec.json --saida <projeto>/desenhos --png
   ```
   Saídas: `privacy-screen.pdf` (todas as pranchas), `privacy-screen-A-N.svg`, `privacy-screen.dxf` e PNGs para conferência (`--png`; não precisam ir para o repositório).
4. **Conferir visualmente** os PNGs antes de entregar. Os problemas mais comuns são textos de cotas pequenas sobrepostos, chamadas cruzadas e vistas saindo da folha. Ajuste a posição das vistas (`Prancha.add`), as cadeias de cotas ou as chamadas, e rode de novo. Duas rodadas costumam bastar.
5. **Checar coerência com o orçamento.** A lista de peças da prancha deve bater com a lista de corte do `orcamento.md` (mesmos comprimentos e quantidades). Se você mudou alguma dimensão no desenho, atualize os componentes do spec e rode o orçamento de novo.
6. **Entregar** o PDF ao usuário e citar o DXF para quem quiser editar no CAD.

## Convenções de desenho

- Unidades: polegadas no modelo; cotas em `22'-1"` / `46 3/8"` (precisão 1/16"). Madeira com medidas **reais** (2x4 = 1 1/2" x 3 1/2").
- Escalas usuais em folha 17x11 (ANSI B): conjunto 1:32 ou 1:24; cortes 1:16 ou 1:12; detalhes 1:6 a 1:4.
- Cores e hachuras por material (`cad.MATERIAIS`): PT esverdeado, cedro laranja, concreto pontilhado, brita, solo hachurado. Peça cortada pelo plano do corte leva um X.
- Toda prancha leva carimbo com projeto, título, número (A-1, A-2...), data e revisão, mais a ressalva "Conferir no campo. Não é projeto estrutural."
- Sempre que houver fundação, desenhe um detalhe com profundidade de embutimento, diâmetro do furo, brita e concreto. Nas notas: 811 e licença/HOA.

## Limites

Desenho 2D de apresentação e execução, não modelo 3D paramétrico nem projeto estrutural com cálculo. Para estruturas altas ou com carga (decks elevados, pergolados grandes), recomende ao usuário a validação de um profissional habilitado ou do código local.
