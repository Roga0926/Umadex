// Umadex: permite instalar el sitio como app y abrirlo sin conexión.
// La página siempre se pide primero a internet (para ver los cambios al instante);
// solo si no hay conexión se usa la copia guardada. Las imágenes se guardan al verlas.
const VERSION = 'umadex-v1';
const BASE = ['/', '/manifest.webmanifest', '/icons/icon-192.png', '/icons/icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(BASE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return; // fuentes, estadísticas, etc.: sin tocar
  // Página: primero internet; sin conexión, la última copia guardada
  if (req.mode === 'navigate' || url.pathname === '/' || url.pathname === '/index.html') {
    e.respondWith(fetch(req).then(r => {
      if (r.ok) { const copia = r.clone(); caches.open(VERSION).then(c => c.put('/', copia)); }
      return r;
    }).catch(() => caches.match('/')));
    return;
  }
  // Imágenes e íconos: la copia guardada al instante y se actualiza en segundo plano
  e.respondWith(caches.open(VERSION).then(c => c.match(req).then(guardada => {
    const red = fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; }).catch(() => guardada);
    return guardada || red;
  })));
});
