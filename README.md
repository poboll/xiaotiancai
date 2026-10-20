# 拾遗馆

一个用来收故事的静态站点。纯 HTML/CSS/JS，无构建步骤，推上去就自动发布到 GitHub Pages。

线上地址形如：`https://<你的用户名>.github.io/<仓库名>/`

**本仓库建议命名为 `xiaotiancai`**（线上就是 `https://<用户名>.github.io/xiaotiancai/`）。

---

## 目录结构

```
.
├── index.html                 首页（卡片列表，数据由 JS 渲染）
├── assets/
│   ├── site.css               全站样式（浅色纸感，宋体为主）
│   └── app.js                 首页渲染逻辑
├── data/
│   └── works.js               ⭐ 所有作品的数据都在这里
├── works/
│   ├── _template/             新作品的空白模板，复制它开始
│   └── longlong-xiaotiancai/  第一部：致王卓凡
│       ├── index.html
│       └── assets/            PDF / DOCX / 图片放这里
├── .github/workflows/pages.yml  自动发布
└── .nojekyll                  关掉 Jekyll 处理，保证文件夹原样发布
```



---

## 加一部新作品（3 步）

**1. 复制模板**

```bash
cd works
cp -r _template 你的作品id        # 例如 cp -r _template a-jie
```

**2. 把素材丢进去**

```
works/你的作品id/
├── index.html        改标题和正文
└── assets/           视频、图片、PDF、DOCX 都放这
```

> 视频建议用 `.mp4`（H.264），浏览器原生能放；`<video>` 标签见模板里的注释。  
> 文件大了会让仓库变臃肿，超过 100MB 建议传 B 站/YouTube 后嵌入链接。

**3. 在 `data/works.js` 里加一条**

```js
{
  id: "a-jie",
  kicker: "视频 · 2026",
  title: "作品标题",
  subtitle: "作者 / 出处",
  tags: ["标签一", "标签二"],
  summary: "一两句话，卡片上显示这个。",
  href: "works/a-jie/",
  downloads: [
    { label: "PDF", href: "works/a-jie/assets/xxx.pdf" }
  ]
}
```

保存 → `git add . && git commit -m "add: xxx" && git push` → 一两分钟后自动上线。

---

## 首次发布

```bash
cd "/Users/Apple/Downloads/小天才"

git init
git add .
git commit -m "init: 拾遗馆"

# 在 GitHub 上先建一个空仓库（命名为 xiaotiancai，不要勾选 README / .gitignore），然后：
git remote add origin https://github.com/<你的用户名>/xiaotiancai.git
git branch -M main
git push -u origin main
```

推完之后，**还要手动开一次开关**：

> 仓库 → **Settings** → 左侧 **Pages** → **Build and deployment** → **Source** 选 **GitHub Actions**

之后每次 `git push` 都会自动重新发布，不用再管。

---

## 常见问题

**页面 404 / 样式全丢？**  
路径全是相对的（`../../assets/...`），所以仓库名是不是 `<用户名>.github.io` 都无所谓。但**别把 index.html 挪层级**，挪了要同步改相对路径。

**改了 works.js 首页没变？**  
浏览器缓存。强制刷新（`Cmd + Shift + R`）。

**中文文件名能发布吗？**  
能。GitHub Pages 支持 UTF-8 路径。

**想换站名 / 副标题？**  
改 `data/works.js` 顶部的 `name`、`tagline`、`intro`，首页和标题会自动跟着变。

**想换配色？**  
`assets/site.css` 开头的 `:root` 里改 CSS 变量即可，全站生效。

---

## 版权

站内文字、影像的版权归原作者所有。这里只作个人收藏与阅读记录，不用于任何商业用途。
