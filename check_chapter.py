"""测试 chapter 页能否在浏览器中正常渲染"""
from playwright.sync_api import sync_playwright
import sys

URLS = [
    "https://jeekeagle.github.io/zero-perspective-hub/pages/system-perspective.html",
    "https://jeekeagle.github.io/zero-perspective-hub/pages/ai-perspective.html",
    "https://jeekeagle.github.io/zero-perspective-hub/pages/ancient-chinese-history-development-perspective.html",
    "https://jeekeagle.github.io/zero-perspective-hub/pages/logic-perspective.html",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    console_logs = []
    page_errors = []

    page.on("console", lambda msg: console_logs.append((msg.type, msg.text)))
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    for url in URLS:
        print(f"\n=== Testing: {url} ===")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            print(f"  ✓ Loaded")

            # 检查关键元素
            title = page.title()
            print(f"  title: {title}")

            # 检查 h1
            h1 = page.locator("h1.cn-chapter__title").first.text_content()
            print(f"  h1: {h1}")

            # 检查 TOC 数量
            toc_items = page.locator(".cn-toc__list li").count()
            print(f"  TOC items: {toc_items}")

            # 截图
            name = url.rsplit('/', 1)[-1].replace('.html', '')
            page.screenshot(path=f"C:/Users/apex/check_{name}.png", full_page=False)
            print(f"  📸 Screenshot saved")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    # 打印 console 错误
    print("\n=== Console Logs ===")
    for t, msg in console_logs:
        print(f"  [{t}] {msg}")
    print("\n=== Page Errors ===")
    for err in page_errors:
        print(f"  ❌ {err}")

    browser.close()
print("\n✓ Done")
