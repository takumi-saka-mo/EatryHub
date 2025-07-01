// /static/mobile/service-worker.js
self.addEventListener('install', function (event) {
  console.log('✅ Service Worker installed');
});

self.addEventListener('activate', function (event) {
  console.log('✅ Service Worker activated');
});

self.addEventListener('fetch', function (event) {
  // 通常の通信はそのまま通す（今回はキャッシュなし）
});