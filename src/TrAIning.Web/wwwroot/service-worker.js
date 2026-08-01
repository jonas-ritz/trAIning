// A service worker with a `fetch` handler is one of the conditions Chrome/Lighthouse require
// before considering a site installable as a PWA (alongside HTTPS and a valid manifest.json).
// This one pre-caches a small, stable app shell so it's satisfied honestly, not just to pass
// the check.

const CACHE_NAME = "trAIning-shell-v1";
const SHELL_ASSETS = ["/", "/manifest.json", "/icons/icon-192.png", "/icons/icon-512.png"];

// Fires once, when the browser first downloads this service worker: pre-download the shell
// assets into a dedicated cache bucket so they're available even with no network.
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)));
  self.skipWaiting();
});

// Fires when this version takes over (e.g. after an update): delete any older cache buckets
// left behind by a previous version, so caches don't accumulate forever.
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

// Fires on every network request the page makes: serve from cache if present, otherwise fall
// through to the network as normal.
self.addEventListener("fetch", (event) => {
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
});
