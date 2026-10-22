/* ===========================================================
   作品详情页：work.html?w=<作品文件夹名>
   =========================================================== */
(function () {
  if (!window.LIBRARY) {
    // 数据脚本没加载上：不是"没有这部作品"，是列表没到
    $("w-title").textContent = "数据没加载上";
    $("w-kicker").textContent = "";
    $("w-src").innerHTML = '作品列表脚本没加载上，<a href="index.html">回到全部作品</a>，或稍后刷新。';
    return;
  }

  var L = window.LIBRARY;
  var works = L.works || [];

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function num(n) {
    if (!n) return "0";
    if (n >= 10000) return (n / 10000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, "") + "万";
    return String(n);
  }

  var raw = new URLSearchParams(location.search).get("w") || "";
  var idx = -1;
  for (var i = 0; i < works.length; i++) {
    // 新链接用短 id；老链接可能是文件夹名，一并兼容
    if (works[i].id === raw || works[i].dir === raw) { idx = i; break; }
  }

  if (idx < 0) {
    $("w-title").textContent = "没有找到这部作品";
    $("w-kicker").textContent = "";
    $("w-src").innerHTML = '链接可能已经失效，<a href="index.html">回到全部作品</a>。';
    return;
  }

  var w = works[idx];

  /* ── 头部 ── */
  document.title = w.title + " · 拾遗馆";
  $("w-kicker").textContent = (w.pin != null ? "置顶 · " : "") +
    (w.kind === "video" ? "影像" : "写真");
  $("w-title").textContent = w.title || "未命名";
  $("w-date").textContent = (w.date || "") +
    (w.count ? "　·　共 " + w.count + " 张" : "");

  var tags = $("w-tags");
  (w.tags || []).forEach(function (t) { tags.appendChild(el("span", "tag", "#" + t)); });

  var stats = $("w-stats");
  [["点赞", w.stats.digg], ["评论", w.stats.comment], ["收藏", w.stats.collect],
   ["推荐", w.stats.recommend], ["分享", w.stats.share]].forEach(function (p) {
    if (!p[1]) return;
    var s = el("span");
    s.appendChild(el("b", null, num(p[1])));
    s.appendChild(document.createTextNode(p[0]));
    stats.appendChild(s);
  });
  if (!stats.children.length) stats.style.display = "none";

  /* ── 正文 ── */
  if (w.kind === "video" && w.video) {
    var v = el("video");
    v.controls = true;
    v.playsInline = true;
    v.preload = "metadata";
    if (w.cover) v.poster = w.cover;
    v.src = w.video;
    $("w-video").appendChild(v);
    $("w-video").hidden = false;

    /* ── 全片文稿：就放在视频下面的空白处，纯文字，不加任何修饰 ── */
    var sc = (window.SCRIPTS || {})[w.id];
    if (sc) {
      var box = el("div", "w-script");
      (sc.sections || []).forEach(function (sec) {
        // 〔〕（）开头的是画面、声音、语种注解——视频里都有，不重复
        var lines = (sec.lines || []).filter(function (line) {
          return !/^[〔（]/.test(line);
        });
        if (!lines.length) return;
        // 同一章的字幕连成一段，读起来才是文稿
        var text = lines.map(function (l) {
          return /^[A-Za-z0-9]/.test(l) ? " " + l : l;
        }).join("");
        box.appendChild(el("p", null, text));
      });
      $("w-video").appendChild(box);
    }
  } else {
    var body = $("w-body");
    (w.images || []).forEach(function (im, n) {
      var box = el("div", "shot");
      var img = el("img");
      img.src = im.src;
      img.alt = w.title + " 第 " + (n + 1) + " 张";
      img.loading = n < 2 ? "eager" : "lazy";
      img.decoding = "async";
      box.appendChild(img);

      if (im.live) {
        var tag = el("span", "live-tag", "LIVE");
        var vid = el("video");
        vid.src = im.live;
        vid.muted = true;
        vid.loop = true;
        vid.playsInline = true;
        vid.preload = "none";
        box.appendChild(vid);
        box.appendChild(tag);
        var start = function (e) {
          e.preventDefault();
          e.stopPropagation();
          box.classList.add("playing");
          vid.play();
        };
        tag.addEventListener("click", start);
        vid.addEventListener("click", function () {
          box.classList.remove("playing");
          vid.pause();
        });
      }

      img.addEventListener("click", function () { openLB(n); });
      body.appendChild(box);
    });
    if (!(w.images || []).length) {
      body.appendChild(el("p", "empty", "这部作品没有可显示的图片。"));
    }
  }

  /* ── 上下篇 ── */
  var nav = $("w-nav");
  var prev = works[idx + 1];   // 列表是新的在前，所以 +1 是更早的一篇
  var next = works[idx - 1];
  if (prev) {
    var a = el("a");
    a.href = "work.html?w=" + encodeURIComponent(prev.id);
    a.appendChild(el("span", "dir", "← 更早"));
    a.appendChild(document.createTextNode(prev.title));
    nav.appendChild(a);
  }
  if (next) {
    var b = el("a", "to-r");
    b.href = "work.html?w=" + encodeURIComponent(next.id);
    b.appendChild(el("span", "dir", "更新 →"));
    b.appendChild(document.createTextNode(next.title));
    nav.appendChild(b);
  }
  if (!prev && !next) nav.style.display = "none";

  /* ── 出处 ── */
  var src = $("w-src");
  if (w.link) {
    var l = el("a", null, "在抖音看原片 ↗");
    l.href = w.link;
    l.target = "_blank";
    l.rel = "noopener";
    src.appendChild(l);
  } else {
    src.textContent = "原作：小天才.（余乐彤）";
  }

  /* ── 灯箱 ── */
  var lb = $("lightbox"), lbImg = $("lb-img"), lbCap = $("lb-cap");
  var cur = 0;

  function show(n) {
    var ims = w.images || [];
    if (!ims.length) return;
    cur = (n + ims.length) % ims.length;
    lbImg.src = ims[cur].full || ims[cur].src;
    lbCap.textContent = (cur + 1) + " / " + ims.length;
  }
  function openLB(n) {
    show(n);
    lb.hidden = false;
    document.body.style.overflow = "hidden";
  }
  function closeLB() {
    lb.hidden = true;
    document.body.style.overflow = "";
  }

  /* ── 返回按钮：同站进来就后退，别处进来就回首页 ── */
  var fab = $("back-fab");
  if (fab) {
    fab.addEventListener("click", function (e) {
      var ref = document.referrer || "";
      if (ref.indexOf(location.origin) === 0 && history.length > 1) {
        e.preventDefault();
        history.back();
      }
    });
  }

  $("lb-close").addEventListener("click", closeLB);
  $("lb-prev").addEventListener("click", function () { show(cur - 1); });
  $("lb-next").addEventListener("click", function () { show(cur + 1); });
  lb.addEventListener("click", function (e) { if (e.target === lb) closeLB(); });
  document.addEventListener("keydown", function (e) {
    if (lb.hidden) return;
    if (e.key === "Escape") closeLB();
    if (e.key === "ArrowLeft") show(cur - 1);
    if (e.key === "ArrowRight") show(cur + 1);
  });
})();
