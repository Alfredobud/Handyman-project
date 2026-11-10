# Reel — "Made it with AI. Who's going to build it?"

**Marca:** Real Special Projects — *When AI meets the real world* (sem logo: usar marca em texto)
**Formato:** Instagram Reel / TikTok / Shorts · 9:16 · 1080x1920 · ~60 s · 30 fps
**Estilo:** faceless, sem narração; o texto na tela conta a história (funciona no mudo)
**Áudio:** exportar SEM som; a música licenciada é adicionada no app do Instagram (acústico/lo-fi)
**Cliente:** ANÔNIMO — nunca mostrar "Bill", "Cornelius", endereço ou preços
**Skills usadas:** `social-media-skills:reels-script` (roteiro); próximos: `caption-writer`, `instagram-reels-publishing`
**Status:** prévia aprovada; MP4 gerado (`marketing/reel-made-it-with-ai.mp4`, 60 s, sem áudio) + capa (`marketing/reel-capa.jpg`). Próximo: `caption-writer` → `instagram-reels-publishing`. Ajuste aprovado: "We engineered it" → "We detailed it".

## Regras de honestidade
- A cerca AINDA NÃO foi construída (cliente analisando). Terminar em "build-ready project", nunca "we built it".
- Abertura com mensagem é encenação → mostrar "dramatization" pequeno no canto.
- Números de engenharia = verificação prática nossa → rotular "design check" (não "engineered"/"stamped").
- Não falar mal da IA: "a IA dá a ideia, a gente tira do papel".
- Proposta aparece sem valores.

## Roteiro (texto na tela em inglês)

| Tempo | Visual | Texto na tela |
|---|---|---|
| **1 · Gancho** | | |
| 0:00–0:04 | Tela de celular: conversa; bolha do "Homeowner" com digitação + imagem de IA anexada | "Hey! I need a fence by my kitchen. Look what I made with AI 👇" → grande: **"Made it with AI."** / **"Who's going to build it?"** · canto: "dramatization" |
| 0:04–0:08 | Imagem de IA (`referencias/conceito-000.jpg`) em tela cheia, zoom lento | "Beautiful. But can it actually be built?" |
| **2 · Engenharia** | | |
| 0:08–0:12 | Diagrama animado da elevação: postes surgindo, cotas dos vãos | "Post spacing: golden-ratio bays, kept under the slat's warp limit." |
| 0:12–0:16 | Poste com setas de vento + barras de tensão: 4x4 ~1,740 psi · 4x6 ~706 psi · 6x6 ~449 psi | "Wind load design check: a 4x4 core is too close to the limit, so we chose 4x6." |
| 0:16–0:20 | Corte da fundação: brita 6", sapata Ø16", embutimento 36", colar de concreto | "Foundation: 36" deep, 16" footing, 6" gravel, concrete collar." |
| 0:20–0:23 | Recomendações, um item por vez | "Treated pine below grade. Planed lumber. Hidden-head screws." |
| **3 · Tentativas** | barra de progresso no topo "v1 → final" | |
| 0:23–0:27 | Prancha antiga (`desenhos/arquivo-rev7/`) + carimbo "CHANGED" | "v1: composite base → owner worried it would warp. Switched to all wood." |
| 0:27–0:31 | Croqui/detalhe do poste revestido (núcleo + 2x6 + serrilhado) | "Owner's idea: wrap the post, notch the sides. We engineered it." |
| 0:31–0:35 | Comparativo 7 vs 10 postes, ✓ no 7 | "10 posts vs 7: kept 7." |
| 0:35–0:39 | Nova referência (`referencias/referencia-rev8-6-postes.webp`) ao lado da prancha nova | "New reference: pergola top. Redesigned with 24 slats per bay." |
| 0:39–0:43 | Detalhe do topo antes/depois (tampa removida, viga parafusada no núcleo) | "Top detail: no end cap, beam bolted straight to the core." |
| 0:43–0:46 | Lado a lado cedro vs pinho tratado (renders 3D, `__paint('A'/'B')`) | "Two options: cedar or treated pine." |
| **4 · Resultado** | | |
| 0:46–0:50 | Proposta (capa/páginas sem preços) + pranchas rev9 deslizando | "Final: proposal + shop drawings." |
| 0:50–0:54 | Celular com o visualizador 3D: toque "Top detail" → "B · Treated pine", girando | "Then the owner explored it in 3D, on their phone." |
| 0:54–1:00 | `referencias/referencia-rev8-6-postes.webp` (cerca junto à casa) → marca | "From AI picture to a build-ready project." → **REAL SPECIAL PROJECTS** · *When AI meets the real world* · "Lake Norman area · DM 'DESIGN'" |

**Capa:** imagem de IA + "Made it with AI. Who builds it?" em negrito no centro (área segura do grid) + "Real Special Projects" pequeno.

**Legenda (rascunho):**
> You made it with AI — we make it real. Custom privacy screen, Lake Norman area: from an AI picture to a build-ready design, with engineering checks, shop drawings and a 3D model the homeowner explored on their phone.
> Planning a fence, screen or pergola? DM "DESIGN".
> #privacyscreen #cedarfence #lakenorman #pergola #woodworking

**Compartilhamento:** quem também gerou imagem com IA e quer saber se dá para construir; envia para o cônjuge.

## Material disponível (tudo nesta pasta do projeto)
- Imagens de IA do cliente: `referencias/conceito-000.jpg` (pedido) e `referencias/referencia-rev8-6-postes.webp` (nova referência/foto final). Usuário aprovou usar sem borrar.
- Pranchas rev9: `desenhos/rev9-a-cedro/privacy-screen-A-{1,2,3}.svg` e `desenhos/rev9-b-pinus/`. **Anonimizar antes de renderizar:** `sed 's/Bill/Homeowner/g; s/Cornelius, NC/Lake Norman area, NC/g; s/Cornelius/Lake Norman area/g'` (o carimbo traz "(Cornelius, NC) — Bill").
- Revisões antigas: `desenhos/arquivo-rev7/`, `propostas/arquivo-rev7/`. Conferir e anonimizar também.
- Proposta: `propostas/Kitchen-Privacy-Screen-Proposal-rev9.pdf` (cortar/ocultar preços e nome).
- Comparativo de núcleos: `orcamento-c/comparativo-nucleo.md`.
- 3D: `renders/web/kitchen-privacy-screen-3d.html` (gerado por `gerar_3d_web.py`). Tem ganchos para gerar quadros: `window.__view(nome)`, `window.__orbit(th, ph, rad, x, y, z)`, `window.__get()`, `window.__paint('A'|'B')`. Esconder a UI com o CSS `.bar{display:none}`.
- Renders PNG: `python3 gerar_3d.py orcamento-c/cedro-4x6 --topo 2x` (vistas geral/topo/ripas/base/vizinho/casa).

## Plano técnico sugerido
1. Playwright (Chromium com `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`) para gerar as sequências de quadros do 3D (giro e detalhes) e as capturas do celular (viewport 390x780, deviceScaleFactor 2).
2. Composição dos quadros em Python/PIL (fonte Inter já instalada): textos, zoom lento, diagramas de engenharia desenhados em código e mockup do celular.
3. `ffmpeg` (instalado em /usr/bin) → H.264, yuv420p, 1080x1920, 30 fps, sem áudio.
4. Mostrar ao usuário 6 quadros-chave antes do MP4 final (regra do projeto: prévia antes do final).
5. Salvar o script em `marketing/gerar_reel.py`; o MP4 vai em `marketing/` (os PNGs são ignorados pelo git).
