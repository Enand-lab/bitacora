const CACHE_NAME = 'logbook-v1';
const urlsToCache = [
  '/',
  '/static/css/pico.min.css',
  '/api/entry/new',
  '/setup'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  // No cachear ni interceptar peticiones a /uploads o /api (excepto GET estáticos)
  if (event.request.url.includes('/uploads/') || 
      (event.request.url.includes('/api/') && event.request.method !== 'GET')) {
    return; // deja que pase directamente a la red
  }

  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
