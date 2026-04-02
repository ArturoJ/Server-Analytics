var CACHE = 'sa-v1';
var SHELL = [
    '/static/css/style.css',
    '/static/css/dashboard.css',
    '/static/js/dashboard.js',
    '/static/icon-192.png',
];

self.addEventListener('install', function (e) {
    e.waitUntil(
        caches.open(CACHE).then(function (cache) { return cache.addAll(SHELL); })
    );
    self.skipWaiting();
});

self.addEventListener('activate', function (e) {
    e.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(
                keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', function (e) {
    if (e.request.url.indexOf('/api/') !== -1) return;
    if (e.request.url.indexOf(self.location.origin) === -1) return;
    e.respondWith(
        fetch(e.request).catch(function () {
            return caches.match(e.request);
        })
    );
});
