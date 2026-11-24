/* ===========================================================
   Service Worker 注册
   站点既可能挂在域名根（xtc.caiths.com/），也可能挂在仓库子路径
   （xxx.github.io/xiaotiancai/），所以根路径从本脚本自己的 URL 反推，
   不写死 "/"。
   =========================================================== */
(function () {
  if (!("serviceWorker" in navigator)) return;
  if (location.protocol !== "https:" && location.hostname !== "localhost" &&
      location.hostname !== "127.0.0.1") return;

  /* 自救入口：万一缓存把人坑了（页面卡在旧版本），
     访问任意页面加 ?nosw=1 即可注销 SW 并清空缓存。
     本次标签页会话内不再注册（关掉重开自动恢复）。 */
  if (/[?&]nosw=1/.test(location.search)) {
    try { sessionStorage.setItem("sw-off", "1"); } catch (e) {}
    navigator.serviceWorker.getRegistrations().then(function (rs) {
      return Promise.all(rs.map(function (r) { return r.unregister(); }));
    }).then(function () {
      return caches.keys();
    }).then(function (keys) {
      return Promise.all(keys.map(function (k) { return caches.delete(k); }));
    }).then(function () {
      // 去掉 nosw 参数后重载，其它查询参数要留着（work.html 也可能带 ?w= 老链接）
      var q = location.search.replace(/[?&]nosw=1/, "").replace(/^&/, "?");
      location.replace(location.pathname + (q && q !== "?" ? q : ""));
    }).catch(function () {});
    return;
  }
  try { if (sessionStorage.getItem("sw-off") === "1") return; } catch (e) {}

  var s = document.currentScript;
  var src = s ? s.src : "";
  var at = src.indexOf("/assets/sw-register.js");
  var root = at >= 0 ? src.slice(0, at + 1) : "/";

  var hadController = !!navigator.serviceWorker.controller;
  var reloading = false;

  navigator.serviceWorker.addEventListener("controllerchange", function () {
    // 首次安装不刷新（那时还没有旧页面要换），只有更新时才刷一次
    if (!hadController || reloading) return;
    reloading = true;
    location.reload();
  });

  navigator.serviceWorker.register(root + "sw.js", { scope: root })
    .catch(function () { /* 注册失败就当没这回事，页面照常用 */ });
})();
