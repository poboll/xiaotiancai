/* ===========================================================
   容错路由守护（index.html / work.html 最早引入）
   - work.html 没带作品 id：进去也没有内容，直接去 404 页
   - 老式作品文件夹链接的救援在 404.html 里做——那种路径线上
     本来就会落到 404 页，逻辑放那儿才跑得到
   跳转用相对路径：站点既可能挂在域名根（xtc.caiths.com/），
   也可能挂在仓库子路径（xxx.github.io/xiaotiancai/），写死 "/404.html" 会跑偏。
   =========================================================== */
(function () {
  var path = location.pathname;

  /* 作品详情页缺参数。作品 id 现在走 #w=，老链接还是 ?w=，两个都认——
     只认 ?w= 的话，链接一旦变成 hash 形式就会被这里直接踢去 404。 */
  if (/\/work\.html$/.test(path)) {
    var hm = /(?:^#|&)w=([^&]*)/.exec(location.hash || "");
    var w = hm ? hm[1] : new URLSearchParams(location.search).get("w");
    if (!w) { location.replace("404.html"); return; }
  }
})();
