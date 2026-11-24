/* ===========================================================
   Service Worker：把重复访问的流量压到接近零
   
   背景：GitHub Pages 对**所有**资源统一发 cache-control: max-age=600，
   而且不能自定义响应头。也就是说十分钟后刷新，128 张图、字体、
   脚本全都要重新发一次条件请求——每个都要一次跨境往返（约 0.37s），
   图片一旦过期还得重新下载。Service Worker 是这上面唯一能
   真正接管缓存的地方。

   策略分工：
   - 页面导航（HTML）  network-first，3.5s 超时降级缓存（内容要新，断网也能看）
   - data/*.js         network-first（作品数据会更新）
   - assets/           cache-first（css/js/字体，URL 带 ?v= 版本号，改了自然失效）
   - 图片              cache-first + 数量上限（只缓存看过的，超了删最旧的）
   - 视频 mp4          不拦截——Range 请求交给浏览器原生处理，
                       硬塞进 Cache Storage 会把 54MB 读进内存，手机上必炸

   发版注意：改完站点如果希望图片也强制刷新，把 VERSION 改一下，
   activate 时会清掉旧版本的所有缓存。
   =========================================================== */

var VERSION = "v1";
var CORE = "core-" + VERSION;
var IMG = "img-" + VERSION;
var MAX_IMG = 300;          // 图片缓存上限（约 60–80MB，Safari 配额内）
var NET_TIMEOUT = 3500;
var IMG_TIMEOUT = 3000;     // 主源超过这个时间就认为抽风，走镜像

/* 故障转移用的备用源。实测主源（GitHub Pages）157ms，这两个镜像 320ms，
   所以只在主源失败/超时时才用——平时一个字节都不多花。
   注意：只兜图片。jsDelivr 单文件上限 20MB，54MB 的视频会被 403 拒掉，
   而且视频是 Range 请求，Service Worker 本来就不拦截。 */
var MIRRORS = [
  "https://gcore.jsdelivr.net/gh/poboll/xiaotiancai@main",
  "https://testingcf.jsdelivr.net/gh/poboll/xiaotiancai@main"
];

/* 站点根路径。挂域名根是 "/"，挂仓库子路径是 "/xiaotiancai/"，
   镜像 URL 要按这个把前缀剥掉才对得上仓库结构。 */
var SCOPE = "/";
try { SCOPE = new URL(self.registration.scope).pathname || "/"; } catch (e) {}

function repoPath(pathname) {
  if (SCOPE !== "/" && pathname.indexOf(SCOPE) === 0) {
    return pathname.slice(SCOPE.length - 1);
  }
  return pathname;
}

var coreP = null;
var imgP = null;
function openCore() { return coreP || (coreP = caches.open(CORE)); }
function openImg() { return imgP || (imgP = caches.open(IMG)); }

var RE_IMG = /\.(webp|jpe?g|png|gif|svg|avif|ico)(\?|$)/i;
var RE_VIDEO = /\.(mp4|webm|mov|m4v)(\?|$)/i;

self.addEventListener("install", function () {
  self.skipWaiting();
});

/* 统计口：排查用。页面里 postMessage({type:"stats"}) 就能拿到计数。 */
var STATS = { img: 0, cacheHit: 0, netFail: 0, mirror: 0, mirrorFail: 0 };
self.addEventListener("message", function (e) {
  var port = e.ports && e.ports[0];
  if (e.data && e.data.type === "stats" && port) port.postMessage(STATS);
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.map(function (k) {
          if (k !== CORE && k !== IMG) return caches.delete(k);
        })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;

  var url;
  try { url = new URL(req.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;   // 只管自己站内的

  // 视频：一律放行，别碰
  if (RE_VIDEO.test(url.pathname)) return;

  // 页面导航
  if (req.mode === "navigate") {
    event.respondWith(networkFirst(req, openCore, NET_TIMEOUT));
    return;
  }

  // 作品数据：cache-first。URL 上带内容 hash（build_library.py 自动写），
  // 数据一变 URL 就变，自然失效；没变就纯吃缓存，一个字节都不下。
  if (url.pathname.indexOf("/data/") >= 0) {
    event.respondWith(cacheFirst(req, openCore, 0));
    return;
  }

  // 图片
  if (RE_IMG.test(url.pathname)) {
    STATS.img++;
    event.respondWith(cacheFirst(req, openImg, MAX_IMG, url.pathname));
    return;
  }

  // 其余静态资源（css/js/字体/头像）
  if (url.pathname.indexOf("/assets/") >= 0) {
    event.respondWith(cacheFirst(req, openCore, 0));
    return;
  }
});

function cacheFirst(req, open, limit, pathname) {
  return open().then(function (cache) {
    return cache.match(req).then(function (hit) {
      if (hit) { STATS.cacheHit++; return hit; }

      function store(res) {
        if (res && res.status === 200) {
          cache.put(req, res.clone()).then(function () {
            if (limit) trim(cache, limit);
          }).catch(function () {});
        }
        return res;
      }

      function fallbackToCache(err) {
        return cache.match(req).then(function (again) {
          if (again) return again;
          throw err;
        });
      }

      return fetchTimeout(req, pathname ? IMG_TIMEOUT : 0).then(function (res) {
        // 源站 5xx 也算抽风，交给镜像
        if (pathname && res && res.status >= 500) {
          return tryMirror(pathname, store).catch(function () { return res; });
        }
        return store(res);
      }).catch(function (err) {
        STATS.netFail++;
        if (!pathname) return fallbackToCache(err);
        return tryMirror(pathname, store).catch(function () {
          return fallbackToCache(err);
        });
      });
    });
  });
}

/* 主源失败时的降级：按顺序试 jsDelivr 的两个镜像，命中就用，命中不了就放弃。
   拿到的响应以原始请求 URL 为 key 存进缓存，下次直接命中，不会再走镜像。 */
function tryMirror(pathname, store) {
  var rel = repoPath(pathname);
  var i = 0;
  function next() {
    if (i >= MIRRORS.length) return Promise.reject(new Error("mirror-failed"));
    var url = MIRRORS[i++] + rel;
    STATS.mirror++;
    return fetch(url).then(function (res) {
      if (res && res.status === 200) return store(res);
      return next();
    }).catch(next);
  }
  return next();
}

function fetchTimeout(req, ms) {
  if (!ms || typeof AbortController === "undefined") return fetch(req);
  var ctrl = new AbortController();
  var timer = setTimeout(function () { ctrl.abort(); }, ms);
  return fetch(req, { signal: ctrl.signal }).then(function (res) {
    clearTimeout(timer);
    return res;
  }, function (err) {
    clearTimeout(timer);
    throw err;
  });
}

function networkFirst(req, open, timeout) {
  return open().then(function (cache) {
    var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, timeout) : null;
    var opts = ctrl ? { signal: ctrl.signal } : {};

    return fetch(req, opts).then(function (res) {
      if (timer) clearTimeout(timer);
      if (res && res.status === 200) {
        cache.put(req, res.clone()).catch(function () {});
      }
      return res;
    }).catch(function (err) {
      if (timer) clearTimeout(timer);
      return cache.match(req).then(function (hit) {
        if (hit) return hit;
        throw err;
      });
    });
  });
}

/* 图片缓存超额：按插入顺序删最早的（keys() 顺序即插入顺序） */
function trim(cache, limit) {
  return cache.keys().then(function (keys) {
    if (keys.length <= limit) return;
    var drop = keys.slice(0, keys.length - limit);
    return Promise.all(drop.map(function (k) { return cache.delete(k); }));
  }).catch(function () {});
}
