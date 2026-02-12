const CACHE_NAME = "sigpacweather-cache-v1";

const urlsToCache = [
  "/",
  "/static/img/marker-sigpacweather.png",
  "/static/img/marker-parcela.png",
  "/static/img/marker-clima-sol.png",
  "/static/img/marker-clima-nublado.png",
  "/static/img/marker-clima-lluvia.png",
  "/static/img/marker-icon.png",
  "/static/img/marker-icon-2x.png",
  "/static/img/marker-shadow.png",
  "/manifest.json"
];

// INSTALACIÓN DEL SERVICE WORKER
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
});

// ACTIVACIÓN Y LIMPIEZA DE CACHES ANTIGUOS
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      );
    })
  );
});

// INTERCEPTAR PETICIONES Y SERVIR DESDE CACHE
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      // Si está en cache → devolverlo
      if (response) return response;

      // Si no → pedirlo a la red
      return fetch(event.request);
    })
  );
});
