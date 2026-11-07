// Service worker do painel. Só deixa o app instalável e abrir a casca
// quando não há rede. Dados do GitHub nunca são guardados em cache.
const CASCA = "painel-casca-v1";
const ARQUIVOS = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(CASCA).then((c) => c.addAll(ARQUIVOS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((nomes) => Promise.all(nomes.filter((n) => n !== CASCA).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const pedido = evento.request;
  if (pedido.method !== "GET" || new URL(pedido.url).origin !== self.location.origin) return;
  evento.respondWith(
    fetch(pedido)
      .then((resposta) => {
        const copia = resposta.clone();
        caches.open(CASCA).then((c) => c.put(pedido, copia)).catch(() => {});
        return resposta;
      })
      .catch(() => caches.match(pedido).then((r) => r || caches.match("./index.html")))
  );
});
