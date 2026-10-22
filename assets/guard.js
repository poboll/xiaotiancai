/* ===========================================================
   容错路由守护（index.html / work.html 最早引入）
   - work.html 没带 ?w= 参数：进去也没有内容，直接去 404 页
   - 老式作品文件夹链接的救援在 404.html 里做——那种路径线上
     本来就会落到 404 页，逻辑放那儿才跑得到
   站点挂在域名根下，跳转一律用根绝对路径。
   =========================================================== */
(function () {
  var path = location.pathname;

  /* 作品详情页缺参数 */
  if (/\/work\.html$/.test(path)) {
    var w = new URLSearchParams(location.search).get("w");
    if (!w) { location.replace("/404.html"); return; }
  }
})();
