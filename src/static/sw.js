/**
 * UnionCore Service Worker
 * Provides offline support and caching for the PWA
 */

const CACHE_NAME = 'unioncore-v1';
const OFFLINE_URL = '/offline';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
    '/',
    '/offline',
    '/static/css/custom.css',
    '/static/css/mobile.css',
    '/static/js/app.js',
    '/static/manifest.json'
];

// External assets to cache (CDN resources)
const CDN_ASSETS = [
    'https://cdn.jsdelivr.net/npm/daisyui@4.6.0/dist/full.min.css',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/htmx.org@1.9.10',
    'https://unpkg.com/alpinejs@3.13.5/dist/cdn.min.js'
];

/**
 * Install event - cache core assets
 */
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching app shell');
                // Cache local assets
                return cache.addAll(PRECACHE_ASSETS)
                    .then(() => {
                        // Try to cache CDN assets (don't fail if they fail)
                        return Promise.allSettled(
                            CDN_ASSETS.map(url =>
                                fetch(url)
                                    .then(response => {
                                        if (response.ok) {
                                            return cache.put(url, response);
                                        }
                                    })
                                    .catch(() => console.log(`[SW] Failed to cache: ${url}`))
                            )
                        );
                    });
            })
    );
    // Activate immediately
    self.skipWaiting();
});

/**
 * Activate event - clean old caches
 */
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Removing old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    // Take control of all clients immediately
    self.clients.claim();
});

/**
 * Fetch event - network first, fallback to cache
 */
self.addEventListener('fetch', (event) => {
    const request = event.request;

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip API calls (always need fresh data)
    if (request.url.includes('/api/') ||
        request.url.includes('/health') ||
        request.url.includes('/auth/')) {
        return;
    }

    // Skip WebSocket connections
    if (request.url.includes('ws://') || request.url.includes('wss://')) {
        return;
    }

    event.respondWith(
        fetch(request)
            .then((response) => {
                // Clone and cache successful responses
                if (response.ok) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Network failed, try cache
                return caches.match(request)
                    .then((cachedResponse) => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // If no cache and it's a navigation, show offline page
                        if (request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                        // Return a simple offline response for other requests
                        return new Response('Offline', {
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: new Headers({
                                'Content-Type': 'text/plain'
                            })
                        });
                    });
            })
    );
});

/**
 * Background sync for offline actions (future enhancement)
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-offline-actions') {
        console.log('[SW] Syncing offline actions');
        // Future: Sync offline actions when back online
    }
});

/**
 * Push notification handler (future enhancement)
 */
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: '/static/icons/icon-192.png',
            badge: '/static/icons/icon-72.png',
            vibrate: [100, 50, 100],
            data: {
                url: data.url || '/'
            }
        };
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

/**
 * Notification click handler
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data.url;
    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then((clientList) => {
                // Focus existing window or open new one
                for (const client of clientList) {
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

console.log('[SW] Service Worker loaded');
