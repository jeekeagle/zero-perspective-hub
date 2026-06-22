/* ============================================================
   Zero-Perspective-Hub · 交互脚本
   - 浅色/暗黑模式切换(默认跟随系统)
   - 移动端导航切换
   ============================================================ */

(function () {
  'use strict';

  // ---------- 主题切换 ----------
  const THEME_KEY = 'zero-pages-theme';

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
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    const isDark = theme === 'dark';
    btn.setAttribute('aria-label', isDark ? '切换为浅色模式' : '切换为暗黑模式');
    btn.setAttribute('title', isDark ? '切换为浅色模式' : '切换为暗黑模式');
    btn.innerHTML = isDark
      ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>'
      : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }

  // 初始化:存储 > 系统
  let current = getStoredTheme() || systemPrefers();
  applyTheme(current);

  // 监听系统主题变化(仅当用户未手动设置)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!getStoredTheme()) {
      current = e.matches ? 'dark' : 'light';
      applyTheme(current);
    }
  });

  // 切换按钮
  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('themeToggle');
    if (btn) {
      btn.addEventListener('click', () => {
        current = current === 'dark' ? 'light' : 'dark';
        storeTheme(current);
        applyTheme(current);
      });
    }
  });

  // ---------- 平滑滚动锚点 ----------
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
