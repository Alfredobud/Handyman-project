# Atalaia · Mapa de Ameaças

Painel único e ao vivo que junta, em um globo, conflitos, protestos, desastres, terremotos, incêndios,
surtos, aeronaves militares e clima espacial, a partir de fontes públicas. Tem amostra gratuita e acesso
completo por código de membro.

Sem dependências: só Node 20 ou mais novo.

## Rodar

```bash
npm start
```

Abra `http://localhost:8080`. No primeiro boot o log mostra o **token de administrador** e um
**primeiro código de membro**.

Com Docker:

```bash
docker build -t atalaia . && docker run -p 8080:8080 -v atalaia-data:/data atalaia
```

Qualquer hospedagem que rode um contêiner ou um processo Node serve (Render, Railway, Fly.io, uma VPS).
Monte um volume persistente em `DATA_DIR`: é lá que ficam códigos, chat e o segredo das sessões.
As opções estão em `.env.example`.

## Como funciona

| Parte | Arquivo | O que faz |
|---|---|---|
| Coletores | `server/sources.js` | Busca cada fonte em um intervalo próprio e normaliza. Se uma fonte cai, o último dado bom continua no ar. |
| Localização | `server/geo.js` | Acha o país citado em cada manchete e classifica por palavras-chave. |
| Servidor | `server/index.js` | `GET /feed`, sessões por cookie assinado, códigos, teste grátis, chat e rotas de admin. |
| Dados | `server/store.js` | Arquivo JSON em `DATA_DIR`. Os códigos são guardados só como hash. |
| Página | `public/` | JavaScript puro com MapLibre GL em globo, PWA com cópia offline do último feed. |

O bloqueio é feito no servidor: quem não tem acesso recebe apenas uma amostra de cada camada
(`SAMPLE` em `server/index.js`) e a contagem do que ficou de fora. Os dados completos nunca
chegam ao navegador de quem não entrou.

## Fontes

USGS (terremotos), GDACS (desastres), NASA EONET (incêndios, vulcões, tempestades), adsb.fi e
adsb.lol (aeronaves militares), NOAA SWPC (índice Kp), NWS (alertas severos nos EUA), OMS (surtos)
e RSS de BBC, Al Jazeera, The Guardian, DW e France 24. Adicione feeds com `EXTRA_FEEDS`.

Antes de uso comercial, confira os termos de cada fonte e do mapa base. Os tiles vêm de
`tile.openstreetmap.org`, cuja política não cobre tráfego alto: troque por um provedor contratado
quando o site crescer (a URL fica em `public/app.js`).

## Administração

```bash
# criar um código (validade em dias é opcional; 0 = sem validade)
curl -X POST localhost:8080/admin/codes -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" -d '{"note":"cliente 1","days":30}'
```

Outras rotas: `GET /admin/codes`, `POST /admin/revoke {id}`, `POST /admin/chat/delete {id}`,
`POST /admin/default-layers {layers:[...]}`.

## Pagamentos

Não há integração automática de pagamento. Coloque os links de checkout do seu provedor em
`CHECKOUT_*` e os preços em `PRICE_*`; depois de receber, gere o código e envie ao cliente.
Sem esses valores, a página mostra apenas o campo de código e o contato.

## Arquivo único de demonstração

```bash
node scripts/build-standalone.js http://localhost:8080 SEU-CODIGO
```

Gera `dist/atalaia-demo.html` com CSS, JS e os dados daquele momento embutidos. Abre direto no
navegador, sem servidor, mas não se atualiza e não tem chat.

## Limites conhecidos

- A classificação de manchetes é por palavras-chave e erra às vezes; o marcador fica no centro do país, não no local exato.
- O teste grátis é limitado por cookie e por IP, o que é fácil de contornar.
- O armazenamento em arquivo serve para um servidor só.
