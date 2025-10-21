/**
 * Service Worker for PWA functionality
 * 提供离线缓存、后台同步、推送通知等功能
 */

const CACHE_NAME = 'stock-rag-v1.0.0';
const RUNTIME_CACHE = 'stock-rag-runtime';

// 预缓存的静态资源
const STATIC_CACHE_URLS = [
  '/',
  '/chat',
  '/upload',
  '/history',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

// 需要缓存的API请求
const API_CACHE_PATTERNS = [
  /^https?:\/\/localhost:8000\/health/,
  /^https?:\/\/localhost:8000\/companies/,
  /^https?:\/\/localhost:8000\/status/,
];

// 需要网络优先的API请求
const NETWORK_FIRST_PATTERNS = [
  /^https?:\/\/localhost:8000\/ask/,
  /^https?:\/\/localhost:8000\/upload/,
  /^https?:\/\/localhost:8000\/batch_ask/,
];

// ============= 安装事件 =============
self.addEventListener('install', (event) => {
  console.log('[SW] Install event');

  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        console.log('[SW] Caching static resources');

        // 预缓存静态资源
        await cache.addAll(STATIC_CACHE_URLS);

        // 强制激活新的Service Worker
        await self.skipWaiting();

        console.log('[SW] Static resources cached successfully');
      } catch (error) {
        console.error('[SW] Failed to cache static resources:', error);
      }
    })()
  );
});

// ============= 激活事件 =============
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate event');

  event.waitUntil(
    (async () => {
      try {
        // 清理旧缓存
        const cacheNames = await caches.keys();
        const oldCaches = cacheNames.filter(name =>
          name.startsWith('stock-rag-') && name !== CACHE_NAME && name !== RUNTIME_CACHE
        );

        await Promise.all(
          oldCaches.map(cacheName => {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
        );

        // 声明控制所有客户端
        await self.clients.claim();

        console.log('[SW] Service Worker activated successfully');
      } catch (error) {
        console.error('[SW] Failed to activate Service Worker:', error);
      }
    })()
  );
});

// ============= 消息处理 =============
self.addEventListener('message', (event) => {
  const { type, payload } = event.data || {};

  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;

    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_NAME });
      break;

    case 'CLEAR_CACHE':
      clearAllCaches().then(() => {
        event.ports[0].postMessage({ success: true });
      }).catch(error => {
        event.ports[0].postMessage({ success: false, error: error.message });
      });
      break;

    default:
      console.log('[SW] Unknown message type:', type);
  }
});

// ============= 网络请求拦截 =============
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const { url, method } = request;

  // 只处理 GET 请求
  if (method !== 'GET') {
    return;
  }

  // 跳过 chrome-extension:// 等协议
  if (!url.startsWith('http')) {
    return;
  }

  event.respondWith(handleRequest(request));
});

// ============= 请求处理策略 =============
async function handleRequest(request) {
  const { url } = request;

  try {
    // API请求 - 网络优先策略
    if (NETWORK_FIRST_PATTERNS.some(pattern => pattern.test(url))) {
      return await networkFirst(request);
    }

    // API请求 - 缓存优先策略
    if (API_CACHE_PATTERNS.some(pattern => pattern.test(url))) {
      return await cacheFirst(request);
    }

    // 页面请求 - 网络优先，缓存降级
    if (request.mode === 'navigate') {
      return await networkFirstWithCacheFallback(request);
    }

    // 静态资源 - 缓存优先
    if (isStaticAsset(url)) {
      return await cacheFirst(request);
    }

    // 默认策略 - 网络优先
    return await networkFirst(request);

  } catch (error) {
    console.error('[SW] Request handling failed:', error);
    return new Response('Service Unavailable', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// ============= 缓存策略实现 =============

// 网络优先策略
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // 缓存成功的响应
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', error);

    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    throw error;
  }
}

// 缓存优先策略
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    // 后台更新缓存
    updateCache(request);
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] Both cache and network failed:', error);
    throw error;
  }
}

// 网络优先，缓存降级（用于页面导航）
async function networkFirstWithCacheFallback(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed for navigation, trying cache');

    // 尝试从缓存获取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // 返回离线页面
    const offlineResponse = await caches.match('/');
    if (offlineResponse) {
      return offlineResponse;
    }

    // 最后的降级方案
    return new Response(
      `<!DOCTYPE html>
      <html lang="zh-CN">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>离线状态 - 投研RAG系统</title>
        <style>
          body { font-family: -apple-system, sans-serif; text-align: center; padding: 50px; }
          .offline-message { max-width: 400px; margin: 0 auto; }
          .icon { font-size: 64px; margin-bottom: 20px; }
        </style>
      </head>
      <body>
        <div class="offline-message">
          <div class="icon">📡</div>
          <h1>当前处于离线状态</h1>
          <p>请检查您的网络连接，然后重试。</p>
          <button onclick="location.reload()">重新连接</button>
        </div>
      </body>
      </html>`,
      {
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
        status: 200,
      }
    );
  }
}

// 后台更新缓存
async function updateCache(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, response);
    }
  } catch (error) {
    console.log('[SW] Background cache update failed:', error);
  }
}

// ============= 工具函数 =============

function isStaticAsset(url) {
  const staticExtensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.ico', '.woff', '.woff2'];
  return staticExtensions.some(ext => url.includes(ext));
}

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map(name => caches.delete(name)));
}

// ============= 推送通知处理 =============
self.addEventListener('push', (event) => {
  console.log('[SW] Push event received');

  if (!event.data) {
    console.log('[SW] Push event has no data');
    return;
  }

  try {
    const data = event.data.json();
    const { title, body, icon, badge, tag, url } = data;

    const options = {
      body: body || '您有新的投研分析结果',
      icon: icon || '/icons/icon-192x192.png',
      badge: badge || '/icons/badge-72x72.png',
      tag: tag || 'stock-rag-notification',
      data: { url: url || '/' },
      requireInteraction: true,
      actions: [
        {
          action: 'open',
          title: '查看',
        },
        {
          action: 'close',
          title: '关闭',
        },
      ],
    };

    event.waitUntil(
      self.registration.showNotification(title || '投研RAG系统', options)
    );
  } catch (error) {
    console.error('[SW] Push notification error:', error);

    // 显示默认通知
    event.waitUntil(
      self.registration.showNotification('投研RAG系统', {
        body: '您有新的消息',
        icon: '/icons/icon-192x192.png',
      })
    );
  }
});

// 通知点击处理
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');

  event.notification.close();

  const { action, data } = event;
  const targetUrl = data?.url || '/';

  if (action === 'close') {
    return;
  }

  event.waitUntil(
    (async () => {
      try {
        const windowClients = await self.clients.matchAll({
          type: 'window',
          includeUncontrolled: true,
        });

        // 查找已打开的窗口
        for (const client of windowClients) {
          if (client.url.includes(self.location.origin)) {
            await client.focus();
            client.navigate(targetUrl);
            return;
          }
        }

        // 没有打开的窗口，打开新窗口
        await self.clients.openWindow(targetUrl);
      } catch (error) {
        console.error('[SW] Failed to handle notification click:', error);
      }
    })()
  );
});

// ============= 后台同步 =============
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);

  switch (event.tag) {
    case 'background-sync':
      event.waitUntil(doBackgroundSync());
      break;
    case 'upload-retry':
      event.waitUntil(retryFailedUploads());
      break;
    default:
      console.log('[SW] Unknown sync tag:', event.tag);
  }
});

async function doBackgroundSync() {
  console.log('[SW] Performing background sync');

  try {
    // 同步离线时收集的数据
    // 这里可以实现具体的同步逻辑
    console.log('[SW] Background sync completed');
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
    throw error; // 重新抛出错误以触发重试
  }
}

async function retryFailedUploads() {
  console.log('[SW] Retrying failed uploads');

  try {
    // 重试失败的上传请求
    // 这里可以从 IndexedDB 读取失败的请求并重试
    console.log('[SW] Failed uploads retry completed');
  } catch (error) {
    console.error('[SW] Failed uploads retry failed:', error);
    throw error;
  }
}

// ============= 错误处理 =============
self.addEventListener('error', (event) => {
  console.error('[SW] Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
  console.error('[SW] Unhandled promise rejection:', event.reason);
  event.preventDefault();
});

console.log('[SW] Service Worker script loaded successfully');
