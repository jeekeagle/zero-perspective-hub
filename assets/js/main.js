/* ============================================================
   Zero-Perspective-Hub · 站点交互脚本
   - 浅色/深色主题切换
   - 移动端目录抽屉
   - 阅读进度条
   - 章内小目录(自动生成 + 滚动高亮)
   - 客户端全文搜索(打开 / 上下选择 / Enter 跳转)
   ============================================================ */
(function () {
  'use strict';

  // ============================================================
  // 1. 主题切换(宣纸/墨韵)
  // ============================================================
  const THEME_KEY = 'zero-pages-cn-theme';
  function getStoredTheme() {
    try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
  }
  function storeTheme(t) {
    try { localStorage.setItem(THEME_KEY, t); } catch (e) {}
  }
  function systemPrefers() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
  }
  function updateThemeIcon(theme) {
    document.querySelectorAll('#cnThemeToggle').forEach((btn) => {
      const isDark = theme === 'ink';
      btn.textContent = isDark ? '宣' : '墨';
      btn.setAttribute('aria-label', isDark ? '切换为宣纸模式' : '切换为墨韵模式');
      btn.setAttribute('title', isDark ? '切换为宣纸模式' : '切换为墨韵模式');
    });
  }

  let current = getStoredTheme() || systemPrefers();
  applyTheme(current);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!getStoredTheme()) {
      current = e.matches ? 'dark' : 'light';
      applyTheme(current);
    }
  });

  // ============================================================
  // 2. 通用 DOM Ready
  // ============================================================
  document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initDrawer();
    initProgressBar();
    initChapterAside();
    initSearch();
  });

  // ============================================================
  // 3. 主题切换按钮
  // ============================================================
  function initThemeToggle() {
    document.querySelectorAll('#cnThemeToggle').forEach((btn) => {
      btn.addEventListener('click', () => {
        current = current === 'ink' ? 'paper' : 'ink';
        storeTheme(current);
        applyTheme(current);
      });
    });
  }

  // ============================================================
  // 4. 移动端目录抽屉
  // ============================================================
  function initDrawer() {
    const toggle = document.querySelector('.cn-nav__drawer-toggle');
    const links = document.querySelector('.cn-nav__links');
    const overlay = document.querySelector('.cn-drawer-overlay');
    if (!toggle || !links) return;
    const close = () => {
      links.classList.remove('is-open');
      if (overlay) overlay.classList.remove('is-open');
      document.body.style.overflow = '';
    };
    const open = () => {
      links.classList.add('is-open');
      if (overlay) overlay.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    };
    toggle.addEventListener('click', () => {
      if (links.classList.contains('is-open')) close();
      else open();
    });
    if (overlay) overlay.addEventListener('click', close);
    links.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', close);
    });
  }

  // ============================================================
  // 5. 阅读进度条(顶部细线)
  // ============================================================
  function initProgressBar() {
    const article = document.querySelector('article');
    if (!article) return;
    const bar = document.createElement('div');
    bar.className = 'cn-progress';
    document.body.appendChild(bar);

    const update = () => {
      const rect = article.getBoundingClientRect();
      const total = article.offsetHeight - window.innerHeight;
      const scrolled = -rect.top;
      const pct = total > 0 ? Math.min(100, Math.max(0, (scrolled / total) * 100)) : 0;
      bar.style.width = pct + '%';
    };
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  // ============================================================
  // 6. 章内小目录(自动从 h2/h3 生成,滚动时高亮)
  // ============================================================
  function initChapterAside() {
    const body = document.querySelector('.cn-chapter__body');
    if (!body) return;
    const headings = body.querySelectorAll('h2, h3');
    if (headings.length < 2) return;  // 少于 2 个标题就不显示

    // 给标题加 id
    headings.forEach((h, i) => {
      if (!h.id) h.id = 'sec-' + i;
    });

    // 创建浮动目录
    const aside = document.createElement('aside');
    aside.className = 'cn-chapter__aside';
    aside.innerHTML = '<div class="cn-chapter__aside__title">本节目录</div><ul>' +
      Array.from(headings).map((h) =>
        `<li><a href="#${h.id}" class="${h.tagName === 'H3' ? 'is-h3' : ''}">${h.textContent}</a></li>`
      ).join('') + '</ul>';
    document.body.appendChild(aside);

    // 滚动时高亮当前节
    const links = aside.querySelectorAll('a');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          links.forEach((l) => l.classList.remove('is-active'));
          const active = aside.querySelector(`a[href="#${entry.target.id}"]`);
          if (active) active.classList.add('is-active');
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    headings.forEach((h) => observer.observe(h));

    // 滚到一定程度才显示
    const showAt = 400;
    const check = () => {
      if (window.scrollY > showAt) aside.classList.add('is-visible');
      else aside.classList.remove('is-visible');
    };
    window.addEventListener('scroll', check, { passive: true });
    check();

    // 点击平滑滚动
    aside.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById(a.getAttribute('href').slice(1));
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  // ============================================================
  // 7. 全文搜索(轻量级,自建索引)
  // ============================================================
  let searchIndex = null;
  async function loadSearchIndex() {
    if (searchIndex) return searchIndex;
    try {
      const res = await fetch('search-index.json');
      searchIndex = await res.json();
    } catch (e) {
      console.warn('搜索索引加载失败', e);
      searchIndex = [];
    }
    return searchIndex;
  }

  function initSearch() {
    const trigger = document.querySelector('.cn-search-trigger');
    if (!trigger) return;
    let modal = null;

    const open = () => {
      modal = document.querySelector('.cn-search-modal');
      if (!modal) {
        modal = document.createElement('div');
        modal.className = 'cn-search-modal';
        modal.innerHTML = `
          <div class="cn-search-modal__inner">
            <input type="search" class="cn-search-input" placeholder="搜索 视角 / 章节 / 段落..." autocomplete="off" />
            <div class="cn-search-results"></div>
          </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
          if (e.target === modal) close();
        });
        const input = modal.querySelector('.cn-search-input');
        input.addEventListener('input', (e) => doSearch(e.target.value));
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Escape') close();
          if (e.key === 'Enter') {
            const first = modal.querySelector('.cn-search-result');
            if (first) first.click();
          }
        });
      }
      modal.classList.add('is-open');
      const input = modal.querySelector('.cn-search-input');
      input.value = '';
      doSearch('');
      setTimeout(() => input.focus(), 50);
      document.body.style.overflow = 'hidden';
    };
    const close = () => {
      if (modal) modal.classList.remove('is-open');
      document.body.style.overflow = '';
    };

    trigger.addEventListener('click', open);

    // 全局快捷键:Ctrl/Cmd + K 或 /
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        open();
      }
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
        e.preventDefault();
        open();
      }
      if (e.key === 'Escape') close();
    });
  }

  async function doSearch(q) {
    if (!searchIndex) await loadSearchIndex();
    const results = document.querySelector('.cn-search-results');
    if (!results) return;

    q = (q || '').trim();
    if (!q) {
      // 没输入时,显示所有章节(列表)
      const all = (searchIndex || []).slice(0, 8);
      results.innerHTML = all.length ? all.map(r => renderResult(r, q)).join('') :
        '<div class="cn-search-empty">输入关键词开始搜索</div>';
      return;
    }

    // 简单匹配:标题命中 3 分,正文命中 1 分
    const lower = q.toLowerCase();
    const scored = (searchIndex || [])
      .map(r => {
        let score = 0;
        if (r.title.toLowerCase().includes(lower)) score += 3;
        if (r.body.toLowerCase().includes(lower)) score += 1;
        // 模糊匹配
        const chars = lower.split('');
        let hits = 0;
        chars.forEach(c => { if (r.body.toLowerCase().includes(c)) hits++; });
        if (hits === chars.length) score += 1;
        return { ...r, score };
      })
      .filter(r => r.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 20);

    if (scored.length === 0) {
      results.innerHTML = `<div class="cn-search-empty">未找到「${escapeHtml(q)}」相关结果</div>`;
      return;
    }
    results.innerHTML = scored.map(r => renderResult(r, q)).join('');
  }

  function renderResult(r, q) {
    const excerpt = highlight(r.excerpt || r.body.slice(0, 120), q);
    const title = highlight(r.title, q);
    return `<a class="cn-search-result" href="${r.url}">
      <div class="cn-search-result__title">${title}</div>
      <div class="cn-search-result__excerpt">${excerpt}…</div>
    </a>`;
  }

  function highlight(text, q) {
    if (!q || !text) return escapeHtml(text);
    const safe = escapeHtml(text);
    const safeQ = escapeHtml(q).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return safe.replace(new RegExp(safeQ, 'gi'), (m) => `<mark>${m}</mark>`);
  }
  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  // ============================================================
  // 8. 平滑滚动到锚点
  // ============================================================
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;
    const id = a.getAttribute('href');
    if (id === '#' || id.length < 2) return;
    const target = document.querySelector(id);
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
})();