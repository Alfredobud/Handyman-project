/* Service worker do Atalaia: sempre tenta a rede primeiro; se o servidor não responder,
   entrega a última cópia boa guardada neste dispositivo. Chat, login e admin nunca são guardados. */
const CACHE = 'atl-data-1';
const SKIP = /^\/(chat|unlock|trial|logout|admin|health)/;

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || SKIP.test(url.pathname)) return;
  e.respondWith((async () => {
    try {
      const r = await fetch(e.request);
      if (r.ok) { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(url.pathname, copy)); }
      else if (r.status >= 500) { const hit = await caches.match(url.pathname); if (hit) return hit; }
      return r;
    } catch (err) {
      const hit = await caches.match(url.pathname);
      if (hit) return hit;
      throw err;
    }
  })());
});
