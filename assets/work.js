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
    (w.count ? "　·　共 " + w.count + " 张" : "") +
    (w.channel ? "　·　" + w.channel : "");

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
    /* 封面 + 播放按钮：点了才加载视频。
       不用 <video poster> 直接显示——纪录片封面是竖版设计图，视频是横屏，
       poster 会被塞进横屏画面里两边留黑边。封面自己占一个竖版画框，点一下再播。 */
    var box = $("w-video");
    if (w.cover) {
      var cv = el("div", "vid-cover");
      var ci = el("img");
      ci.src = w.cover;
      ci.alt = w.title || "";
      ci.decoding = "async";
      var pb = el("button", "vid-play");
      pb.type = "button";
      pb.setAttribute("aria-label", "播放");
      pb.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';
      cv.appendChild(ci);
      cv.appendChild(pb);
      box.appendChild(cv);
      cv.addEventListener("click", function () {
        var v = el("video");
        v.controls = true;
        v.playsInline = true;
        v.preload = "none";
        v.src = w.video;
        v.poster = w.cover;
        box.innerHTML = "";
        box.appendChild(v);
        v.play().catch(function () {});
      });
    } else {
      var v = el("video");
      v.controls = true;
      v.playsInline = true;
      v.preload = "none";
      v.src = w.video;
      box.appendChild(v);
    }
    box.hidden = false;

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

        // 章标题 + 时间码
        var head = el("div", "w-sc-sec");
        head.appendChild(el("span", "w-sc-name", sec.name || ""));
        if (sec.time) head.appendChild(el("span", "w-sc-time", sec.time));
        box.appendChild(head);

        // 按句号/问号/叹号/省略号断段。字幕是一行一句断开的，
        // 不合并会把一句话拆得七零八落，全合并又会糊成一大团——
        // 遇到句末标点就收一段，剩下的在章末兜底吐完。
        var para = [];
        var flush = function () {
          if (!para.length) return;
          var text = para.map(function (l) {
            return /^[A-Za-z0-9]/.test(l) ? " " + l : l;
          }).join("");
          box.appendChild(el("p", null, text));
          para = [];
        };
        lines.forEach(function (l) {
          para.push(l);
          if (/[。？！…?!]$/.test(l.trim())) flush();
        });
        flush();
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

  /* ── 出处：按渠道给原文链接，双平台两个都给 ── */
  var src = $("w-src");
  var chan = w.channel || "抖音";
  var links = [];
  if (chan === "双平台") {
    links.push([w.link, "在抖音看原片 ↗"], [w.xhsLink, "在小红书看原笔记 ↗"]);
  } else if (chan === "小红书") {
    links.push([w.link, "在小红书看原笔记 ↗"]);
  } else if (w.link) {
    links.push([w.link, "在抖音看原片 ↗"]);
  }
  links.forEach(function (p) {
    if (!p[0]) return;
    var l = el("a", null, p[1]);
    l.href = p[0];
    l.target = "_blank";
    l.rel = "noopener";
    l.style.marginRight = "18px";
    src.appendChild(l);
  });
  if (!src.children.length) src.textContent = "原作：小天才.（余乐彤）";

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
