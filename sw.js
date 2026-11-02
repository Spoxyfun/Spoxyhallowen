// Spooky Halloween — service worker konservatif (network-first).
// Hanya menangani GET same-origin untuk shell & aset statis; selain itu
// dibiarkan ke jaringan langsung. Tidak pernah menyajikan konten basi:
// cache hanya dipakai sebagai cadangan saat offline.
const CACHE = "spooky-pwa-v1";
const CORE = ["/manifest.webmanifest", "/assets/nft-12.webp", "/collection-master-512/images/10000.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const cacheable =
    url.pathname === "/" ||
    url.pathname === "/index.html" ||
    url.pathname.startsWith("/assets/") ||
    CORE.includes(url.pathname);
  if (!cacheable) return;
  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      })
      .catch(() => caches.match(req, { ignoreSearch: true }))
  );
});
