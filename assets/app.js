/* 首页渲染：读 window.SITE，生成卡片。无依赖。 */
(function () {
  var S = window.SITE || { name: "拾遗馆", works: [] };

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function card(w) {
    var a = el("a", "card");
    a.href = w.href || "#";

    a.appendChild(el("div", "kicker", w.kicker || "作品"));

    var h = el("h2", null, w.title || "未命名");
    a.appendChild(h);

    if (w.subtitle) a.appendChild(el("div", "sub", w.subtitle));
    if (w.summary) a.appendChild(el("p", "summary", w.summary));

    var foot = el("div", "foot");
    var tags = el("div", "tags");
    (w.tags || []).forEach(function (t) {
      tags.appendChild(el("span", "tag", t));
    });
    foot.appendChild(tags);
    foot.appendChild(el("span", null, "阅读 →"));
    a.appendChild(foot);

    return a;
  }

  function ghost() {
    var d = el("div", "card ghost");
    d.appendChild(el("h2", null, "下一部"));
    d.appendChild(el("p", null, "在 data/works.js 里加一条，\n再建一个 works/ 下的文件夹。"));
    return d;
  }

  document.addEventListener("DOMContentLoaded", function () {
    // 站点名与文案
    var n = document.getElementById("site-name");
    var t = document.getElementById("site-tagline");
    var i = document.getElementById("site-intro");
    var c = document.getElementById("site-count");
    if (n) n.textContent = S.name || "拾遗馆";
    if (t) t.textContent = S.tagline || "";
    if (i) i.textContent = S.intro || "";
    if (c) c.textContent = String((S.works || []).length).padStart(2, "0") + " 部作品";

    document.title = (S.name || "拾遗馆") + " · " + (S.tagline || "");

    var grid = document.getElementById("works");
    if (!grid) return;
    (S.works || []).forEach(function (w) { grid.appendChild(card(w)); });
    grid.appendChild(ghost());
  });
})();
