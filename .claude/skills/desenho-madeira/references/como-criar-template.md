# Como criar um template novo com `cad.py`

## API

```python
from cad import Vista, Prancha, exportar, pes_pol

v = Vista("ELEVAÇÃO FRONTAL", escala=12)            # 1:12; o subtítulo da escala é automático
v.peca(x, y, w, h, "pt" | "cedro" | "madeira" | "composite" | "metal" | "vazio",
       x_corte=False, tracejado=False)              # retângulo de peça; x_corte = peça seccionada
v.poligono(pts, "concreto" | "brita" | "solo" | material, tracejado=False)
v.linha(pts, espessura=0.6, tracejado=False)
v.circulo(cx, cy, r, "vazio", tracejado=True)
v.texto(x, y, "texto", tam=7, ancora="middle"|"start"|"end", negrito=False, rot=0)
v.cota((x1, y), (x2, y), deslocamento)              # horizontal: deslocamento em y (polegadas de modelo)
v.cota((x, y1), (x, y2), deslocamento)              # vertical: deslocamento em x
v.cotas_corrente([x0, x1, x2], y, desl)             # cadeia; horizontal=False para vertical
v.chamada(p_alvo, p_texto, "texto\nsegunda linha")  # seta de chamada
v.eixo(p1, p2, "1")                                 # linha de eixo com bolha
v.marca_corte(p1, p2, "A")                          # linha de corte A-A

p = Prancha("Projeto", "Título da prancha", "A-1", notas=["..."], data="", revisao="0")
p.add(v, x_papel, y_papel)                          # canto inferior-esquerdo da vista (polegadas, a partir do canto inferior-esquerdo da folha)
p.tabela(x, y_topo, colunas, linhas, larguras_pol, "LISTA DE PEÇAS")
exportar([p, ...], "saida/nome", png=True)          # .svg por prancha, .pdf único, .dxf, .png
```

O tamanho do texto é em pontos de papel, independe da escala. A área útil da folha 17x11 vai de x 0.35 a 16.65 e de y 0.35 a 10.65; o carimbo ocupa x 12.05–16.65 e y 0.35–1.8, e as notas ficam logo acima dele.

## Receita

1. **Classe de geometria:** recebe o bloco `geometria` do spec (mesclado com `PADRAO`) e calcula todas as coordenadas uma vez só (posições de postes, níveis, fiadas). As vistas apenas leem essas coordenadas; assim, planta, elevação e corte nunca divergem.
2. **Sistema de eixos:** x ao longo do comprimento, y vertical (0 = terreno ou piso), z na profundidade. A elevação usa (x, y), a planta (x, z) e o corte transversal (z, y).
3. **Ordem de desenho:** terreno → fundação → peças de trás → peças da frente → cotas e chamadas (o que vem depois fica por cima).
4. **Pranchas sugeridas:**
   - A-1: elevação + planta (1:32 ou 1:24) + notas gerais.
   - A-2: corte transversal + detalhes (fundação, ligações, perfis decorativos) + lista de peças.
   - Móveis: A-1 com vistas frontal, lateral e superior (1:8 a 1:4) e A-2 com o diagrama de corte das tábuas (tábua de 96" com as peças desenhadas encaixadas).
5. **Conferência:** rode com `--png`, olhe as imagens, corrija sobreposições e rode de novo.

## Ideias de template

- `deck.py`: planta com joists a 16" OC, vigas e pilares; corte com ledger e flashing.
- `pergolado.py`: elevação frontal e lateral, planta de caibros.
- `movel_plano.py`: vistas ortográficas + diagrama de corte a partir das peças do spec (`componentes` do tipo `pecas`).
