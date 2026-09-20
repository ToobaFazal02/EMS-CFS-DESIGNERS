/* CFS EMS admin PWA — shell cache only; never cache /api (auth + live data). */
const CACHE = "cfs-ems-shell-v1";
const SHELL = ["/", "/index.html", "/manifest.webmanifest", "/favicon-192.png?v=2"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL).catch(() => undefined))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET") return;
  if (url.pathname.startsWith("/api")) return; // network only
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        if (res.ok && (url.pathname === "/" || url.pathname.endsWith(".js") || url.pathname.endsWith(".css") || url.pathname.endsWith(".png") || url.pathname.endsWith(".ico") || url.pathname.endsWith(".webmanifest"))) {
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => undefined);
        }
        return res;
      })
      .catch(() => caches.match(req).then((hit) => hit || caches.match("/")))
  );
});
