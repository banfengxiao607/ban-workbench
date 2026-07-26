// Service Worker for「班」工作台 PWA
// 策略：HTML/JS/CSS 走 cache-first（稳定资源）；
//      JSON 数据走 network-first（每次拿最新，断网才回退缓存）
const CACHE_NAME = 'ban-workbench-v3';
const ASSETS = [
  './',
  './index.html',
  './tailwind.js',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
];

// 需要走 network-first 的动态数据文件
const DYNAMIC_DATA = ['/data.json', '/shizheng.json', '/study_plan.json'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => k !== CACHE_NAME && caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;

  const pathname = url.pathname;

  // 动态数据：network-first，确保总是拿到最新
  if (DYNAMIC_DATA.some(p => pathname.endsWith(p))) {
    e.respondWith(
      fetch(e.request)
        .then(response => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(e.request).then(c => c || new Response('{"items":[]}', {headers: {'Content-Type': 'application/json'}})))
    );
    return;
  }

  // 其他同源资源：cache-first，回退网络
  e.respondWith(
    caches.match(e.request).then(cached => {
      return cached || fetch(e.request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
        }
        return response;
      }).catch(() => cached);
    })
  );
});
