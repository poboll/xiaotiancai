/* ===========================================================
   首页渲染：故事摘要 + 首篇 + 画廊 + 筛选
   数据：window.SITE（手写）/ window.LIBRARY（脚本生成）
   =========================================================== */
(function () {
  var S = window.SITE || {};
  var L = window.LIBRARY || { works: [] };
  var works = L.works || [];

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  /* 112020 → 11.2万 */
  function num(n) {
    if (!n) return "0";
    if (n >= 10000) return (n / 10000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, "") + "万";
    return String(n);
  }
  function dur(s) {
    if (!s) return "";
    var m = Math.floor(s / 60), r = s % 60;
    return m + ":" + (r < 10 ? "0" : "") + r;
  }

  /* ── 头部 ── */
  function head() {
    if (S.name) {
      $("hero-name").textContent = S.name;
      $("site-name").textContent = S.name;
      document.title = S.name + " · " + (S.tagline || "");
    }
    if (S.tagline) $("site-tagline").textContent = S.tagline;
    if (S.intro) $("site-intro").textContent = S.intro;

    var imgs = works.reduce(function (a, w) { return a + (w.count || 0); }, 0);
    var vids = works.filter(function (w) { return w.kind === "video"; }).length;
    var bits = [];
    if (works.length) bits.push(works.length + " 部作品");
    if (imgs) bits.push(imgs + " 张影像");
    if (vids) bits.push(vids + " 条视频");
    bits.push("1 封信");
    $("site-count").textContent = bits.join("　·　");
  }

  /* ── 故事摘要 ── */
  function teaser() {
    var box = $("story-teaser");
    if (!box) return;
    (S.storyTeaser || []).forEach(function (t) {
      box.appendChild(el("p", null, t));
    });
  }

  /* ── 首篇 ── */
  function feature() {
    var f = S.featured;
    var card = $("feature");
    if (!f || !card) return;
    card.setAttribute("href", f.href || "#");
    $("feature-kicker").textContent = f.kicker || "";
    $("feature-title").textContent = f.title || "";
    $("feature-sub").textContent = f.subtitle || "";
    $("feature-sum").textContent = f.summary || "";
    $("feature-meta").textContent = f.meta || "";

    var links = $("feature-links");
    (f.downloads || []).forEach(function (d) {
      var a = el("a", "dl", d.label);
      a.href = d.href;
      a.setAttribute("download", "");
      a.addEventListener("click", function (e) { e.stopPropagation(); });
      links.appendChild(a);
    });
  }

  /* ── 置顶两条 ── */
  function pinned() {
    var box = $("pinned");
    if (!box) return;
    var list = S.pinned || [];
    if (!list.length) { box.hidden = true; return; }
    list.forEach(function (p) {
      var a = el("a", "pin");
      a.href = p.href || "#";
      if (p.external) { a.target = "_blank"; a.rel = "noopener"; }

      var l = el("div", "pin-l");
      l.appendChild(el("div", "pin-kicker", p.kicker || "置顶"));
      l.appendChild(el("h3", "pin-title", p.title || ""));
      if (p.sub) l.appendChild(el("div", "pin-sub", p.sub));
      if (p.text) l.appendChild(el("p", "pin-text", p.text));
      a.appendChild(l);

      var r = el("div", "pin-r");
      r.appendChild(el("span", "pin-cta", p.cta || "打开 →"));
      a.appendChild(r);

      box.appendChild(a);
    });
  }

  /* ── 筛选 ── */
  var cur = "all";
  function filters() {
    var box = $("filters");
    var years = {};
    works.forEach(function (w) { if (w.year) years[w.year] = (years[w.year] || 0) + 1; });

    var defs = [
      { k: "all", label: "全部", n: works.length },
      { k: "image", label: "图文", n: works.filter(function (w) { return w.kind === "image"; }).length },
      { k: "video", label: "视频", n: works.filter(function (w) { return w.kind === "video"; }).length }
    ];
    Object.keys(years).sort().reverse().forEach(function (y) {
      defs.push({ k: "y" + y, label: y, n: years[y], sep: true });
    });

    defs.forEach(function (d, i) {
      if (d.sep && i > 0) box.appendChild(el("span", "fsep"));
      var b = el("button", "chip" + (d.k === "all" ? " on" : ""));
      b.type = "button";
      b.dataset.k = d.k;
      b.appendChild(document.createTextNode(d.label));
      b.appendChild(el("span", "chip-n", String(d.n)));
      b.addEventListener("click", function () {
        cur = d.k;
        [].forEach.call(box.querySelectorAll(".chip"), function (c) {
          c.classList.toggle("on", c.dataset.k === cur);
        });
        paint();
      });
      box.appendChild(b);
    });
  }

  /* ── 画廊 ── */
  function tile(w) {
    var a = el("a", "tile");
    a.href = "work.html?w=" + encodeURIComponent(w.id);

    var box = el("div", "tile-img");
    if (w.coverW && w.coverH) {
      box.style.aspectRatio = w.coverW + " / " + w.coverH;
    } else {
      box.style.aspectRatio = "3 / 4";
    }

    if (w.cover) {
      var img = el("img");
      img.src = w.cover;
      img.alt = w.title || "";
      img.loading = "lazy";
      img.decoding = "async";
      box.appendChild(img);
    } else {
      box.classList.add("noimg");
      box.appendChild(el("span", "noimg-t", w.title || ""));
    }

    if (w.kind === "video") {
      box.appendChild(el("span", "badge play", "▶" + (w.duration ? " " + dur(w.duration) : "")));
    } else if (w.images && w.images.some(function (i) { return i.live; })) {
      box.appendChild(el("span", "badge live", "LIVE"));
    }
    a.appendChild(box);

    var cap = el("div", "tile-cap");
    cap.appendChild(el("div", "tile-title", w.title || "未命名"));
    var meta = [w.date || "", w.kind === "video" ? "视频" : (w.count || 0) + " 张"];
    if (w.stats && w.stats.digg) meta.push("♥ " + num(w.stats.digg));
    cap.appendChild(el("div", "tile-meta", meta.filter(Boolean).join("　·　")));
    a.appendChild(cap);

    return a;
  }

  function paint() {
    var box = $("masonry");
    box.innerHTML = "";
    var list = works.filter(function (w) {
      if (cur === "all") return true;
      if (cur === "image" || cur === "video") return w.kind === cur;
      if (cur.charAt(0) === "y") return w.year === cur.slice(1);
      return true;
    });
    var frag = document.createDocumentFragment();
    list.forEach(function (w) { frag.appendChild(tile(w)); });
    box.appendChild(frag);
    $("empty").hidden = list.length > 0;
    $("gallery-note").textContent = L.generated
      ? "共 " + works.length + " 部　·　数据更新于 " + L.generated
      : "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    head();
    teaser();
    feature();
    pinned();
    filters();
    paint();
  });
})();
