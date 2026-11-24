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

  /* ── 她的两个平台（头像共用一张，所以只出现一次） ── */
  function profiles() {
    var box = $("profiles");
    var p = S.profile;
    if (!box || !p) return;

    var card = el("div", "profile-card");

    var img = document.createElement("img");
    img.className = "pc-avatar";
    img.src = p.avatar || "";
    img.alt = (p.nick || "") + " 的头像";
    img.loading = "lazy";
    card.appendChild(img);

    var main = el("div", "pc-main");
    var head = el("div", "pc-head");
    head.appendChild(el("span", "pc-nick", p.nick || ""));
    if (p.uid) head.appendChild(el("span", "pc-uid", p.uid));
    main.appendChild(head);

    (p.platforms || []).forEach(function (pl) {
      /* 整行就是主页链接：不占地方，也不多一行小字。
         链接文字去掉了，但点击行为还在，鼠标放上去徽章会有反应。 */
      var row = el("a", "pc-row");
      row.href = pl.href || "#";
      row.target = "_blank";
      row.rel = "noopener";
      row.setAttribute("aria-label", (pl.name || "") + " 主页");
      row.appendChild(el("span", "pc-platform " + (pl.cls || ""), pl.name || ""));
      row.appendChild(el("span", "pc-sig", pl.signature || ""));
      row.appendChild(el("span", "pc-nums", pl.nums || ""));
      main.appendChild(row);
    });

    card.appendChild(main);
    box.appendChild(card);
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
  var cur = "all";                 // 快选：all / image / video / y2026 …
  var platform = "all";            // 漏斗·平台：all / 抖音 / 小红书 / 双平台
  var sortBy = "new";              // 漏斗·排序：new 倒序 / old 正序 / hot 热度

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

  /* ── 漏斗：平台 + 排序 ── */
  function funnel() {
    var btn = $("funnel-btn"), panel = $("funnel-panel");
    if (!btn || !panel) return;

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      panel.hidden = !panel.hidden;
      btn.setAttribute("aria-expanded", String(!panel.hidden));
    });
    document.addEventListener("click", function (e) {
      if (!panel.hidden && !panel.contains(e.target) && e.target !== btn) {
        panel.hidden = true;
        btn.setAttribute("aria-expanded", "false");
      }
    });

    function bind(groupId, fn) {
      var g = $(groupId);
      if (!g) return;
      [].forEach.call(g.querySelectorAll("button"), function (b) {
        b.addEventListener("click", function () {
          [].forEach.call(g.querySelectorAll("button"), function (x) { x.classList.remove("on"); });
          b.classList.add("on");
          fn(b.dataset.v);
          paint();
        });
      });
    }
    bind("fp-platform", function (v) { platform = v; });
    bind("fp-sort", function (v) { sortBy = v; });

    var reset = $("fp-reset");
    if (reset) reset.addEventListener("click", function () {
      platform = "all"; sortBy = "new";
      ["fp-platform", "fp-sort"].forEach(function (id) {
        [].forEach.call($(id).querySelectorAll("button"), function (b, i) {
          b.classList.toggle("on", i === 0);
        });
      });
      paint();
    });
  }

  /* 有筛选/排序在生效时，漏斗按钮上亮个小点 */
  function funnelState() {
    var dot = $("funnel-dot");
    if (dot) dot.hidden = platform === "all" && sortBy === "new";
    var st = $("funnel-state");
    if (st) {
      var bits = [];
      if (platform !== "all") bits.push(platform);
      if (sortBy === "old") bits.push("时间正序");
      else if (sortBy === "hot") bits.push("按热度");
      st.textContent = bits.join(" · ");
    }
  }

  /* ── 画廊 ── */
  function tile(w) {
    var a = el("a", "tile");
    a.href = "work.html#w=" + encodeURIComponent(w.id);

    var box = el("div", "tile-img");
    // 比例优先用「裁掉填充边后的封面尺寸」，没有才回落到原始封面尺寸。
    // 小红书导出图左右垫白、抖音视频封面上下垫黑，直接用原尺寸会留白框/黑块。
    var tw = w.thumbW || w.coverW, th = w.thumbH || w.coverH;
    if (tw && th) {
      box.style.aspectRatio = tw + " / " + th;
    } else {
      box.style.aspectRatio = "3 / 4";
    }

    if (w.cover) {
      var img = el("img");
      // 瓦片用缩略图（有的话）；详情页才用高清封面
      img.src = w.coverThumb || w.cover;
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
    if (w.pin != null) {
      box.appendChild(el("span", "badge pinmark", "置顶"));
    }
    a.appendChild(box);

    var cap = el("div", "tile-cap");
    // 没写文案的作品不编「未命名」，直接不显示标题行，只留日期和张数
    if (w.title) cap.appendChild(el("div", "tile-title", w.title));
    var meta = [w.date || "", w.kind === "video" ? "视频" : (w.count || 0) + " 张"];
    if (w.stats && w.stats.digg) meta.push("♥ " + num(w.stats.digg));
    cap.appendChild(el("div", "tile-meta", meta.filter(Boolean).join("　·　")));
    a.appendChild(cap);

    return a;
  }

  /* 列数跟断点一致：≥1180 四列，860–1180 三列，≤720 两列 */
  var lastCols = 0;
  function colCount() {
    var w = window.innerWidth;
    if (w <= 720) return 2;
    if (w <= 1180) return 3;
    return 4;
  }

  function paint() {
    var box = $("masonry");
    box.innerHTML = "";
    var list = works.filter(function (w) {
      if (cur === "image" || cur === "video") { if (w.kind !== cur) return false; }
      else if (cur.charAt(0) === "y") { if (w.year !== cur.slice(1)) return false; }
      if (platform !== "all" && (w.channel || "抖音") !== platform) return false;
      return true;
    });
    // 置顶的排最前面（按 build_library.py 里的 PINNED_ORDER），其余按漏斗里选的排序
    var hot = function (w) {
      var s = w.stats || {};
      return (s.digg || 0) + (s.comment || 0) * 3 + (s.collect || 0) * 2;
    };
    list.sort(function (a, b) {
      var pa = a.pin == null ? 999 : a.pin, pb = b.pin == null ? 999 : b.pin;
      if (pa !== pb) return pa - pb;
      if (sortBy === "old") return (a.date || "") < (b.date || "") ? -1 : 1;
      if (sortBy === "hot") return hot(b) - hot(a);
      return (a.date || "") < (b.date || "") ? 1 : -1;   // new：时间倒序
    });
    /* 按行分配 + 末尾配平：
       先轮流放（1→列1, 2→列2, 3→列3, 4→列4, 5→列1…），视觉上第一行就是最新的
       几部，往下也是一行一行，读起来是对的。
       但卡片高矮差得远，轮流放会让各列总高度差到上千像素——页面底部就会出现
       一整列空白（用户看到的那片空白）。所以后面加一步：每次都放进当前最矮的
       那一列。顺序仍然是逐张往下排，只是不再死守 i % n。
       （纯 CSS 多列是「一列到底」，第一行会是第 1、34、67、100 个，顺序全乱；
         Grid 行内高度不齐又会在矮卡片下面留洞，所以交给 JS 分列。） */
    var n = colCount();
    lastCols = n;
    box.className = "masonry";
    box.innerHTML = "";
    var cols = [], colH = [];
    for (var c = 0; c < n; c++) {
      var col = el("div", "mcol");
      cols.push(col);
      colH.push(0);
      box.appendChild(col);
    }
    // 列内竖向间距，配平时要算进去，不然会偏
    var innerGap = cols[0] ? parseFloat(getComputedStyle(cols[0]).gap) || 0 : 0;
    list.forEach(function (w, i) {
      // 第一行强制轮流放，保证首屏顺序规整；之后放最矮的一列
      var k = i < n ? i : 0;
      if (i >= n) {
        for (var j = 1; j < n; j++) if (colH[j] < colH[k]) k = j;
      }
      var t = tile(w);
      cols[k].appendChild(t);
      // 瓦片的画框有 aspect-ratio，图片没加载也能量出高度
      colH[k] += t.getBoundingClientRect().height + innerGap;
    });
    $("empty").hidden = list.length > 0;
    $("gallery-note").textContent = L.generated
      ? "共 " + works.length + " 部　·　数据更新于 " + L.generated
      : "";
    var c = $("fp-count");
    if (c) c.textContent = "当前 " + list.length + " 部";
    funnelState();
  }

  document.addEventListener("DOMContentLoaded", function () {
    head();
    profiles();
    teaser();
    feature();
    pinned();
    filters();
    funnel();
    paint();
    // 列数变了才重排（窗口拖动时避免反复重建 DOM）
    var rt;
    window.addEventListener("resize", function () {
      clearTimeout(rt);
      rt = setTimeout(function () {
        if (colCount() !== lastCols) paint();
      }, 160);
    });
    if (!window.LIBRARY) {
      // 数据脚本没加载上：说清楚，别让首页看着像"没有作品"
      var note = $("gallery-note");
      if (note) note.textContent = "作品数据没加载上，稍后刷新试试。";
    }
  });
})();
