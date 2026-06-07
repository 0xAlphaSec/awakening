const CACHE = "awakening-v2";
const ASSETS = ["/", "/habitos", "/entrenamiento", "/finanzas"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener("fetch", e => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});