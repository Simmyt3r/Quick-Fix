/* QuickFix Nearby — service worker
   Strategy: cache-first for static assets, network-first for HTML pages.
   Offline fallback shows a friendly "You're offline" screen. */

const CACHE = 'qf-v1';
const STATIC = [
  '/static/css/style.css',
  '/static/logo.png',
  '/static/manifest.webmanifest',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const { request } = e;
  const url = new URL(request.url);

  // Static assets — cache first, update in background
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(request).then(cached => {
        const fresh = fetch(request).then(resp => {
          caches.open(CACHE).then(c => c.put(request, resp.clone()));
          return resp;
        });
        return cached || fresh;
      })
    );
    return;
  }

  // HTML navigation — network first, fall back to cache
  if (request.mode === 'navigate') {
    e.respondWith(
      fetch(request).catch(() =>
        caches.match(request).then(r => r || offlinePage())
      )
    );
    return;
  }
});

function offlinePage() {
  return new Response(
    `<!DOCTYPE html><html lang="en"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Offline — QuickFix Nearby</title>
    <style>
      body{margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh;
           font-family:Barlow,sans-serif;background:#F2F4F5;text-align:center;padding:24px;}
      h1{font-size:28px;color:#0068B7;margin:0 0 12px;}
      p{color:#5C6B73;margin:0 0 24px;}
      a{display:inline-block;padding:12px 28px;background:#0068B7;color:#fff;
        border-radius:10px;text-decoration:none;font-weight:600;}
    </style></head>
    <body>
      <div>
        <h1>You're offline</h1>
        <p>Check your connection and try again.</p>
        <a href="/dashboard">Retry</a>
      </div>
    </body></html>`,
    { headers: { 'Content-Type': 'text/html' } }
  );
}
