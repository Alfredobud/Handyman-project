'use strict';
// Lógica compartilhada entre o servidor e o arquivo HTML ao vivo: monta as camadas do mapa
// e calcula o nível de ameaça a partir do que os coletores trouxeram.

function shortId(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(36);
}

function buildMap(state) {
  const news = state.news || [];
  const located = news.filter((n) => n.country);
  const pick = (cat) => located.filter((n) => n.cat === cat).map((n) => ({
    id: shortId(n.link), title: n.title, country: n.country, flag: n.flag, at: n.at, link: n.link, source: n.source, lat: n.lat, lng: n.lng,
  }));
  // notícias gerais: um marcador por país, com a lista de manchetes
  const byCountry = {};
  for (const n of located) {
    const g = (byCountry[n.iso] ||= { id: n.iso, country: n.country, flag: n.flag, lat: n.clat, lng: n.clng, n: 0, articles: [] });
    g.n++;
    if (g.articles.length < 8) g.articles.push({ title: n.title, link: n.link, source: n.source, at: n.at, cat: n.cat });
  }
  return {
    quakes: state.quakes || [], hazards: state.hazards || [], events: state.events || [], aircraft: state.aircraft || [],
    attacks: pick('attack'), unrest: pick('unrest'), cyber: pick('cyber'), infra: pick('infra'),
    outbreaks: state.outbreaks || [],
    news: Object.values(byCountry).sort((a, b) => b.n - a.n),
  };
}

function threatLevel(m, space, weather) {
  let score = 0;
  const reasons = [];
  const add = (pts, why) => { score += pts; reasons.push(why); };
  const att24 = m.attacks.filter((a) => Date.now() - new Date(a.at) < 864e5).length;
  if (att24 >= 3) add(Math.min(4, 1 + Math.floor(att24 / 6)), `${att24} relatos de ataques/conflito em 24h`);
  const red = m.hazards.filter((h) => h.level === 'Red').length;
  const orange = m.hazards.filter((h) => h.level === 'Orange').length;
  if (red) add(Math.min(3, red + 1), `${red} desastre(s) em alerta vermelho (GDACS)`);
  else if (orange >= 3) add(1, `${orange} desastres em alerta laranja (GDACS)`);
  const big = m.quakes.filter((q) => q.mag >= 6.5);
  if (big.length) add(big.some((q) => q.mag >= 7.5) ? 2 : 1, `terremoto M${Math.max(...big.map((q) => q.mag)).toFixed(1)} nas últimas 24h`);
  if (space && space.kp_max_24h >= 7) add(2, `tempestade geomagnética forte (Kp ${space.kp_max_24h})`);
  else if (space && space.kp_max_24h >= 5) add(1, `tempestade geomagnética (Kp ${space.kp_max_24h})`);
  if (m.outbreaks.length >= 4) add(1, `${m.outbreaks.length} surtos reportados pela OMS`);
  if (m.unrest.length >= 6) add(1, `${m.unrest.length} focos de protesto/instabilidade`);
  const recon = m.aircraft.filter((a) => a.role === 'recon' || a.role === 'bomber').length;
  if (recon >= 12) add(1, `${recon} aeronaves estratégicas no ar`);
  if (weather && weather.extreme >= 5) add(1, `${weather.extreme} alertas climáticos extremos nos EUA`);
  const level = score >= 9 ? 5 : score >= 6 ? 4 : score >= 3 ? 3 : score >= 1 ? 2 : 1;
  return { level, label: ['', 'BAIXO', 'MODERADO', 'ELEVADO', 'ALTO', 'SEVERO'][level], score, reasons: reasons.length ? reasons : ['Nenhum sinal fora do normal nas fontes monitoradas'] };
}

const headlinesOf = (state) => (state.news || []).map((n) => ({ title: n.title, link: n.link, source: n.source, at: n.at, cat: n.cat, country: n.country || '', flag: n.flag || '' }));

module.exports = { buildMap, threatLevel, headlinesOf };
