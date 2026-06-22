"""
清空 pages/ 下所有章节文件的样例内容。

保留:HTML 脚手架(nav / sidebar / breadcrumb / footer / 上下一篇 / 编辑链接)
清空:cn-chapter__body(正文)、h1 标题、副标题、tag 元数据、章节卷期、阅读时长
"""

import re
from pathlib import Path

ROOT = Path(r"E:\Zero\Zero-Lab\zero-perspective-hub")
PAGES = ROOT / "pages"

PLACEHOLDER_BODY = '''          <div class="cn-chapter__body">
            <p style="text-align: center; color: var(--cn-ink-faint); font-family: 'STKaiti', 'KaiTi', '楷体', serif; padding: 4rem 0; letter-spacing: 0.1em;">
              〔 本章内容待录入 〕
            </p>
          </div>'''


def clear_one(path: Path) -> None:
    html = path.read_text(encoding="utf-8")

    # 1. 清空 cn-chapter__body 内容
    html = re.sub(
        r'(<div class="cn-chapter__body">)\s*.*?\s*(</div>)',
        lambda m: PLACEHOLDER_BODY,
        html,
        count=1,
        flags=re.DOTALL,
    )

    # 2. 清空标题
    html = re.sub(
        r'<h1 class="cn-chapter__title">[^<]*</h1>',
        '<h1 class="cn-chapter__title">（待定）</h1>',
        html,
        count=1,
    )

    # 3. 清空副标题
    html = re.sub(
        r'<p class="cn-chapter__subtitle">[^<]*</p>',
        '<p class="cn-chapter__subtitle">（章节副标题待录入）</p>',
        html,
        count=1,
    )

    # 4. 清空 tag 列表
    html = re.sub(
        r'(<div class="cn-chapter__meta">)\s*.*?\s*(</div>)',
        r'\1\n            <span class="tag">待定</span>\n          \2',
        html,
        count=1,
        flags=re.DOTALL,
    )

    # 5. 清空章节元信息(卷期 / 时间 / 阅读时长)
    html = re.sub(
        r'<span class="cn-chapter-meta__seal">[^<]*</span>',
        '<span class="cn-chapter-meta__seal">—</span>',
        html,
        count=1,
    )
    html = re.sub(
        r'<span class="cn-chapter-meta__vol">[^<]*</span>',
        '<span class="cn-chapter-meta__vol">第一编 · 视角</span>',
        html,
        count=1,
    )
    html = re.sub(
        r'<time>[^<]*</time>',
        '<time>2026</time>',
        html,
        count=1,
    )
    html = re.sub(
        r'<span>约 [^<]*</span>',
        '<span>待定</span>',
        html,
        count=1,
    )

    # 6. 清空 <title> 中章节名
    html = re.sub(
        r'<title>[^·]+ ·',
        '<title>（待定） ·',
        html,
        count=1,
    )

    # 7. 清空 meta description 中的具体内容(保留站点描述骨架)
    html = re.sub(
        r'<meta name="description" content="[^"]*" />',
        '<meta name="description" content="视角研究中心 · 一本关于视角的小书" />',
        html,
        count=1,
    )

    # 8. 清空面包屑中的章节名
    html = re.sub(
        r'<span class="cn-chapter-meta__current">[^<]*</span>',
        '<span class="cn-chapter-meta__current">（待定）</span>',
        html,
        count=1,
    )
    html = re.sub(
        r'<span class="cn-breadcrumb__current">[^<]*</span>',
        '<span class="cn-breadcrumb__current">（待定）</span>',
        html,
        count=1,
    )

    # 9. 清空"上一篇/下一篇"的 title(标签保留"上一篇/下一篇")
    html = re.sub(
        r'(<span class="title">)[^<]*(</span>)',
        r'\1（待定）\2',
        html,
    )

    # 10. 清空 OG/canonical 中残留的章节名(把 og:title 改通用)
    html = re.sub(
        r'<meta property="og:title" content="[^"]*" />',
        '<meta property="og:title" content="视角研究中心 · Zero-Perspective-Hub" />',
        html,
    )
    html = re.sub(
        r'<link rel="canonical" href="[^"]*" />',
        f'<link rel="canonical" href="https://jeekeagle.github.io/zero-perspective-hub/{path.relative_to(ROOT).as_posix()}" />',
        html,
    )

    path.write_text(html, encoding="utf-8")
    print(f"  [OK] cleared: {path.name}")


def main():
    print("=" * 60)
    print("Clear all sample chapter content under pages/")
    print("=" * 60)
    files = sorted(PAGES.glob("*.html"))
    for f in files:
        clear_one(f)
    print(f"\nTotal processed: {len(files)} chapter files")


if __name__ == "__main__":
    main()