const CACHE = 'jay-parking-v3';
const STATIC = ['/', '/manifest.json', '/icon.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(STATIC)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ),
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const { url } = e.request;
  const isApi = url.includes('/api/') || url.includes('chadstone.com.au/api/');

  if (isApi) {
    e.respondWith(
      caches.open(CACHE).then((cache) =>
        fetch(e.request)
          .then((res) => {
            if (res.ok) cache.put(e.request, res.clone());
            return res;
          })
          .catch(() => cache.match(e.request)),
      ),
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request)),
  );
});
