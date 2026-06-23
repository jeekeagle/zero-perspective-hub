"""
重建侧栏 TOC + 按家族分组,注入所有 pages/*.html、intro.html、about.html、archive.html。
"""
import re, os, glob, sys, json

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# ---------- 1. 清洗章节中文名 ----------
NOISE_PATTERNS = [
    r"分析提示词4?\.?5?\.?1?",
    r"分析视角",
    r"提示词4?\.?5?\.?1?",
    r"\s*-\s*method\s*$",
    r"\s*4\.5\.1\s*$",
]
def clean_title(title):
    t = title.strip()
    for p in NOISE_PATTERNS:
        t = re.sub(p, "", t, flags=re.I)
    t = re.sub(r"\s+", "", t)
    # 兜底:如果不以"视角"结尾,补一个
    if t and "视角" not in t:
        t += "视角"
    return t

# ---------- 2. 家族分组 ----------
# 把 slug 映射到家族。占位章保留它们原本的占位顺序。
PLACEHOLDER_SLUGS = {
    "agent-topology": "拓扑学视角",
    "from-tool-to-colleague": "关系视角",
    "notes-on-rag": "架构视角",
    "prompt-as-program": "程序视角",
    "skill-economy": "经济学初稿",
    "system-perspective": "系统视角(原占位)",
    "when-models-think": "分类学视角",
}

FAMILIES = {
    "系统与复杂": [
        "system-dynamics-perspective",
        "complexity-science-perspective",
        "ecological-niche-perspective",
        "evolution-perspective",
        "cumulative-effect-perspective",
        "network-effects-perspective",
        "inflection-point-perspective",
        "universe-perspective",
    ],
    "思维方法": [
        "bayesian-thinking-perspective",
        "razor-thinking-perspective",
        "marginal-thinking-perspective",
        "construction-thinking-perspective",
        "deconstruction-perspective",
        "control-thinking-perspective",
        "coordination-thinking-perspective",
        "narrative-thinking-perspective",
        "logic-perspective",
    ],
    "经济与管理": [
        "economics-perspective",
        "scarcity-perspective",
        "management-perspective",
        "leadership-perspective-4-5-1",
        "decision-science-perspective",
        "supply-chain-perspective",
        "digital-transformation-perspective",
        "sales-perspective",
        "management-consultant-perspective",
    ],
    "自然与形式科学": [
        "mathematics-perspective-4-5-1",
        "calculus-perspective",
        "mathematical-modeling-perspective",
        "statistics-perspective",
        "ai-perspective",
        "data-scientist-perspective",
    ],
    "人文与社会": [
        "philosophy-perspective",
        "psychology-perspective",
        "religious-studies-perspective",
        "ancient-chinese-history-development-perspective",
        "cross-cultural-perspective",
    ],
    "职业视角": [
        "scientist-perspective",
        "science-writer-perspective",
        "engineer-perspective",
        "architect-perspective",
        "designer-perspective-4-5-1-method",
        "artist-perspective",
        "writer-perspective",
        "screenwriter-perspective",
        "host-perspective",
        "doctor-perspective",
        "lawyer-perspective",
        "historian-perspective",
        "philosopher-perspective",
        "psychologist-perspective",
        "counselor-perspective",
    ],
    # 注:占位篇已删除,不再列出
}

# 中文序号
HANZI = ["一","二","三","四","五","六","七","八","九","十",
         "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
         "二十一","二十二","二十三","二十四","二十五","二十六","二十七","二十八","二十九","三十",
         "三十一","三十二","三十三","三十四","三十五","三十六","三十七","三十八","三十九","四十",
         "四十一","四十二","四十三","四十四","四十五","四十六","四十七","四十八","四十九","五十",
         "五十一","五十二","五十三","五十四","五十五","五十六","五十七","五十八","五十九","六十"]

# ---------- 3. 扫描 pages 拿章节标题 ----------
def scan_pages():
    metas = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "pages", "*.html"))):
        slug = os.path.splitext(os.path.basename(p))[0]
        text = open(p, encoding="utf-8").read()
        m = re.search(r'<h1[^>]*class="cn-chapter__title"[^>]*>(.*?)</h1>', text, re.S)
        raw_title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else slug
        title = clean_title(raw_title)
        if slug in PLACEHOLDER_SLUGS:
            title = PLACEHOLDER_SLUGS[slug]
        metas[slug] = {"slug": slug, "title": title, "raw_title": raw_title}
    return metas

# ---------- 4. 构建 TOC HTML ----------
def build_toc(metas, prefix="", current_slug=None):
    """prefix: 当前页相对 pages/ 的前缀。
       根目录页(index/intro/about/archive) prefix='pages/'。
       章节页 prefix=''。
    """
    lines = []
    lines.append('<aside class="cn-toc" aria-label="目录">')
    lines.append('  <div class="cn-toc__title">本书目录</div>')

    intro_href = "intro.html" if prefix else "../intro.html"
    archive_href = "archive.html" if prefix else "../archive.html"
    about_href = "about.html" if prefix else "../about.html"
    index_href = "index.html" if prefix else "../index.html"

    # 序章
    lines.append('  <div class="cn-toc__group">')
    lines.append('    <div class="cn-toc__group-label">序章</div>')
    lines.append('    <ul class="cn-toc__list">')
    lines.append(f'      <li><a href="{index_href}">封面</a></li>')
    lines.append(f'      <li><a href="{intro_href}">序言</a></li>')
    lines.append('    </ul>')
    lines.append('  </div>')

    # 各家族
    chapter_num = 0
    for family_name, slugs in FAMILIES.items():
        # 过滤掉不存在的 slug
        valid = [s for s in slugs if s in metas]
        if not valid:
            continue
        lines.append('  <div class="cn-toc__group">')
        lines.append(f'    <div class="cn-toc__group-label">{family_name}</div>')
        lines.append('    <ul class="cn-toc__list">')
        for slug in valid:
            chapter_num += 1
            hz = HANZI[chapter_num - 1] if chapter_num <= len(HANZI) else str(chapter_num)
            title = metas[slug]["title"]
            href = f"{slug}.html" if not prefix else f"{prefix}{slug}.html"
            active_cls = ' class="is-active"' if slug == current_slug else ""
            lines.append(f'      <li{active_cls}><a href="{href}">{hz} · {title}</a></li>')
        lines.append('    </ul>')
        lines.append('  </div>')

    # 附录
    lines.append('  <div class="cn-toc__group">')
    lines.append('    <div class="cn-toc__group-label">附录</div>')
    lines.append('    <ul class="cn-toc__list">')
    lines.append(f'      <li><a href="{archive_href}">索引</a></li>')
    lines.append(f'      <li><a href="{about_href}">关于</a></li>')
    lines.append('    </ul>')
    lines.append('  </div>')

    lines.append('</aside>')
    return "\n      ".join(lines)  # 加缩进

# ---------- 5. 替换文件里的 cn-toc 块 ----------
TOC_RE = re.compile(r'<aside class="cn-toc"[^>]*>.*?</aside>', re.S)

def inject(file_path, toc_html):
    text = open(file_path, encoding="utf-8").read()
    new_text, n = TOC_RE.subn(toc_html, text, count=1)
    if n == 0:
        return False, "未找到 cn-toc"
    if new_text == text:
        return True, "无变更"
    open(file_path, "w", encoding="utf-8").write(new_text)
    return True, "已更新"

# ---------- main ----------
def main():
    metas = scan_pages()
    print(f"扫描 pages: {len(metas)} 个")

    # 检查缺失/孤儿
    all_in_families = set()
    for slugs in FAMILIES.values():
        all_in_families.update(slugs)
    orphans = set(metas.keys()) - all_in_families
    missing = all_in_families - set(metas.keys())
    if orphans:
        print(f"⚠ 不在分类里的孤儿章: {sorted(orphans)}")
    if missing:
        print(f"⚠ 分类里写了但文件不存在: {sorted(missing)}")

    # 注入到章节页
    pages_updated = 0
    for slug, meta in metas.items():
        page_path = os.path.join(ROOT, "pages", f"{slug}.html")
        toc_html = build_toc(metas, prefix="", current_slug=slug)
        ok, msg = inject(page_path, toc_html)
        if ok and msg == "已更新":
            pages_updated += 1
    print(f"章节页注入: {pages_updated} 个")

    # 注入到根目录页
    root_pages = ["intro.html", "about.html", "archive.html"]
    root_updated = 0
    for fn in root_pages:
        fp = os.path.join(ROOT, fn)
        if not os.path.exists(fp):
            print(f"跳过 {fn}(不存在)")
            continue
        toc_html = build_toc(metas, prefix="pages/", current_slug=None)
        ok, msg = inject(fp, toc_html)
        if ok and msg == "已更新":
            root_updated += 1
            print(f"  根页 {fn}: {msg}")
    print(f"根页注入: {root_updated} 个")

if __name__ == "__main__":
    main()
