# zero-perspective-hub

> 一个关于视角的小型研究中心 —— 收集镜片、整理方法、检验用法。

不是一本书,不是 newsletter,也不是教程。
是一间镜片铺子:陈列各种视角,介绍它们的诞生,也诚实记录它们在何处失效。

🔗 在线访问:https://<your-username>.github.io/zero-perspective-hub/

## 收什么

- **镜片 (Lens)** —— 一个具体的视角,比如"分类学视角""演化视角""博弈视角"。它有自己的前提、自己的盲区、自己擅长看的对象。
- **锻造法 (Method)** —— 这种视角是怎么造出来的。从什么经验、什么案例、什么对比里抽象出来的。
- **检验录 (Test)** —— 拿这个视角去看某个具体问题,看到了什么、漏掉了什么。

## 项目结构

```
zero-perspective-hub/
├── index.html              # 首页(Hero + 最近镜片 + 视角分类 + 引言)
├── about.html              # 关于:研究中心缘起与原则
├── archive.html            # 索引:所有视角按时间倒序
├── feed.xml                # RSS 订阅
├── assets/
│   ├── css/style.css       # 现代科技风格
│   ├── css/style-cn.css    # 新中式美学风格
│   └── js/main.js          # 主题切换、滚动行为
├── img/
│   ├── logo.svg
│   └── favicon.svg
├── pages/                  # 视角文章(每篇一个 HTML)
│   ├── when-models-think.html
│   ├── skill-economy.html
│   ├── prompt-as-program.html
│   ├── agent-topology.html
│   ├── from-tool-to-colleague.html
│   └── notes-on-rag.html
└── README.md
```

## 两种风格

- **样式 1(现代科技)** —— `index.html`,线条利落,适合技术读者
- **样式 2(新中式美学)** —— `style-2.html`,宣纸 + 朱砂 + 山水,适合喜欢古风的读者

两份首页之间互链,共用 `pages/` 下的文章。

## 本地预览

```bash
# Python 3
python3 -m http.server 8000

# Node.js
npx http-server -p 8000
```

然后访问 http://localhost:8000

## 部署到 GitHub Pages

### 一次性配置

1. 在 GitHub 上创建仓库 `zero-perspective-hub`(公开)
2. 把本目录的所有文件 push 上去

```bash
cd zero-perspective-hub
git init
git add .
git commit -m "init: 视角研究中心初始版本"
git branch -M main
git remote add origin https://github.com/<your-username>/zero-perspective-hub.git
git push -u origin main
```

3. GitHub 仓库 → **Settings** → **Pages**
4. Source 选 **Deploy from a branch**
5. Branch 选 `main`,目录 `/ (root)`,保存
6. 等待 1-2 分钟,访问 `https://<your-username>.github.io/zero-perspective-hub/`

### 新增一个视角

1. 在 `pages/` 下新建 HTML,复制已有文章的 `<article class="article">` 块
2. 在 `index.html` 的「最近收录的视角」区域加一张卡片
3. 在 `archive.html` 加一行
4. `git add . && git commit -m "new: 视角名" && git push`

## 设计原则

- 视觉上参考 [Zero-Skills-Hub](https://jeekeagle.github.io/Zero-Skills-Hub/) 的现代科技感
- 主色:深蓝(`#2563eb` / `#5fa3d8`)+ 暖金(`#c89732`)
- 字体:系统字体栈(中英文皆佳)
- 装饰:六边形 + 网络图

新中式风格则完全独立:

- 主色:宣纸暖白(`#f3ead3`)+ 朱砂红(`#a8321d`)+ 鎏金(`#b89048`)
- 字体:宋体(`Source Han Serif SC`)+ 楷体(`STKaiti`)
- 装饰:山水轮廓 + 卷云纹 + 朱砂印章

## 许可

内容部分采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) —— 署名即可,标不标出处都行。

代码部分采用 MIT License。

—— Zero · 2026