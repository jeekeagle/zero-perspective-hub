#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
watch-zero-skills.py — 监控 Zero-Skills 文件夹,自动上传新视角到 zero-perspective-hub

工作流:
  1. 扫描 SOURCE_DIR 下所有 .md
  2. 与 STATE_FILE 对比,找出新增
  3. 对每个新文件:
     a. 尝试 utf-8 / gbk 解码
     b. 修复 frontmatter(Get 笔记导出的格式不规范)
     c. 复制到 STAGING_DIR,用 post-to-pers-hub 上传
  4. 把已上传的记入 STATE_FILE

用法:
  python watch-zero-skills.py            # 扫描一次
  python watch-zero-skills.py --watch    # 持续扫描(每 2 分钟)
"""
import sys
import os
import re
import json
import shutil
import hashlib
import argparse
import subprocess
import datetime
import time
from pathlib import Path

# === 配置 ===
SOURCE_DIR = Path(r"C:\Users\apex\Desktop\Zero-Skills")
SITE_DIR = Path(r"E:\Zero\Zero-Lab\zero-perspective-hub")
STAGING_DIR = SITE_DIR / ".incoming-skills"
STATE_FILE = SITE_DIR / ".watch-state.json"
POST_SCRIPT = Path(r"C:/Users/apex/AppData/Local/Temp/codepilot-shadow-claude-MR6VLn/.claude/skills/post-to-pers-hub/scripts/run.py")
LOG_FILE = SITE_DIR / ".watch-log.txt"


# Windows: 强制 stdout 用 utf-8,避免 emoji 报 gbk 错
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def log(msg: str, also_print: bool = True):
    """记一行日志,带时间戳"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    if also_print:
        print(line, flush=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed": {}, "errors": {}}


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8"
    )


def file_fingerprint(path: Path) -> str:
    """文件指纹:大小 + mtime + sha256 前 16 位"""
    st = path.stat()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"{st.st_size}-{int(st.st_mtime)}-{h.hexdigest()[:16]}"


def read_text_smart(path: Path) -> str:
    """智能读文本:try utf-8, then gbk"""
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    # 兜底:utf-8 替换
    return path.read_text(encoding="utf-8", errors="replace")


def fix_frontmatter(text: str) -> tuple[dict, str]:
    r"""
    修复 Get 笔记导出的不规范 frontmatter。

    原格式(坏的):
      ---
      title: "..."
      author: "..."
      date: "..."
      ---

      name: system-dynamics-perspective
      description: "..."
      version: 4.5.1

      ## 真正的正文...

    修复后:
      ---
      name: system-dynamics-perspective
      cn_name: ...
      description: "..."
      version: 4.5.1
      title: "..."
      author: "..."
      date: "..."
      ---

      ## 真正的正文...
    """
    import yaml

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not m:
        raise ValueError("文件没有 frontmatter")

    fm_raw = m.group(1)
    body = m.group(2)

    try:
        fm_top = yaml.safe_load(fm_raw) or {}
    except Exception:
        fm_top = {}

    # 探测 body 头部是不是也有 YAML 字段(name/description/version/user_invocable)
    # 也跳过开头的 # H1 / 段落标题 / ``` 代码块围栏
    body_top = {}
    body_lines = body.split("\n")
    consumed = 0
    in_code_fence = False
    code_fence_buffer = []  # 在代码块内累计内容

    def flush_code_buffer():
        """尝试 parse 累计的代码块内容"""
        nonlocal body_top
        try:
            inner = yaml.safe_load("\n".join(code_fence_buffer)) or {}
            if isinstance(inner, dict):
                body_top.update(inner)
        except Exception:
            pass

    for line in body_lines:
        s = line.strip()
        # 处理 ``` 代码块围栏
        if s.startswith("```"):
            if not in_code_fence:
                in_code_fence = True
                code_fence_buffer = []
                consumed += 1
                continue
            else:
                # 代码块结束 — parse buffer
                in_code_fence = False
                consumed += 1
                flush_code_buffer()
                code_fence_buffer = []
                continue
        if in_code_fence:
            code_fence_buffer.append(line)
            consumed += 1
            # 防御:代码块里出现 ## 标题说明这块不像 metadata,强制 flush 并跳出去
            if s.startswith("##"):
                in_code_fence = False
                flush_code_buffer()
                code_fence_buffer = []
            continue
        if not s:
            consumed += 1
            continue
        # 跳过 # H1 / ## H2 之类的标题
        if s.startswith("#"):
            consumed += 1
            continue
        # 看是不是 YAML 字段
        if re.match(r"^[a-z_][a-z0-9_]*:", s):
            try:
                test_fm = yaml.safe_load(s)
                if isinstance(test_fm, dict):
                    body_top.update(test_fm)
                    consumed += 1
                    continue
            except Exception:
                pass
        # 不是 YAML 也不是 H1,停
        break

    # 防御:文件结束时如果还在代码块内,flush
    if in_code_fence:
        flush_code_buffer()
        code_fence_buffer = []

    # 剩下的 body
    rest_body = "\n".join(body_lines[consumed:]).lstrip("\n")

    # 剩下的 body
    rest_body = "\n".join(body_lines[consumed:]).lstrip("\n")

    # 合并 frontmatter:body 的字段优先(因为它更具体)
    merged = dict(fm_top)
    merged.update(body_top)

    # 推断 lens_family:从 description 或标题里猜
    if "lens_family" not in merged:
        title = str(merged.get("title", ""))
        desc = str(merged.get("description", ""))
        text_blob = title + " " + desc
        # 简单关键词
        keywords = {
            "系统动力学": "系统", "系统论": "系统", "系统视角": "系统", "系统思维": "系统",
            "AI": "AI", "人工智能": "AI",
            "哲学": "哲学", "心理": "心理学", "经济": "经济学", "管理": "管理",
            "博弈": "博弈", "社会": "社会", "教育": "教育", "设计": "设计",
            "科学": "科学", "历史": "历史", "文学": "文学", "美学": "美学",
            "检验": "检验", "审查": "审查", "验证": "验证",
        }
        for kw, fam in keywords.items():
            if kw in text_blob:
                merged["lens_family"] = fam
                break
        if "lens_family" not in merged:
            merged["lens_family"] = "其他"

    # 推断 cn_name
    if "cn_name" not in merged:
        title = str(merged.get("title", ""))
        # 去掉日期/来源后缀
        cn = re.sub(r"提示词$", "视角", title)
        cn = re.sub(r"\d{4}年\d{1,2}月\d{1,2}日.*$", "", cn)
        cn = re.sub(r"来自.*$", "", cn)
        cn = cn.strip(" -·【】[]")
        merged["cn_name"] = cn or "未命名视角"

    # 如果没有 name,从 cn_name 推导一个 ascii slug
    if not merged.get("name"):
        cn = str(merged.get("cn_name", ""))
        slug = re.sub(r"[\s　]+", "-", cn)  # 中文留作 unicode slug
        # 保留中文 unicode,转小写
        slug = slug.lower()
        # 用一个稳定 hash 后缀避免冲突
        import hashlib as _hl
        h = _hl.md5(cn.encode("utf-8")).hexdigest()[:6]
        merged["name"] = f"{slug}-{h}" if slug else f"perspective-{h}"
        # 也加个 en alias
        merged["name_alias"] = merged["name"]

    # 重新 dump
    new_fm = yaml.safe_dump(merged, allow_unicode=True, sort_keys=False)
    new_text = f"---\n{new_fm}---\n\n{rest_body}"
    return merged, new_text


def process_one(skill_md: Path, state: dict) -> bool:
    """处理一个新文件,返回是否成功"""
    fp = file_fingerprint(skill_md)
    if state["processed"].get(skill_md.name) == fp:
        return True  # 已处理过,跳过

    log(f"📥 发现新文件: {skill_md.name}")
    try:
        text = read_text_smart(skill_md)
        fm, fixed = fix_frontmatter(text)
    except Exception as e:
        log(f"  ❌ 修复 frontmatter 失败: {e}")
        state["errors"][skill_md.name] = str(e)
        return False

    # 写到 staging
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    staged = STAGING_DIR / skill_md.name
    staged.write_text(fixed, encoding="utf-8")
    log(f"  📝 已修复并暂存: {staged.name}")
    log(f"     → name={fm.get('name')}, cn_name={fm.get('cn_name')}, family={fm.get('lens_family')}")

    # 调用 post-to-pers-hub
    # 传 stdin="y\n" 自动确认"覆盖已存在文件"的提示
    try:
        result = subprocess.run(
            [sys.executable, str(POST_SCRIPT), str(staged), "--site-dir", str(SITE_DIR)],
            input="y\n",
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300
        )
        # 输出到日志
        for line in result.stdout.splitlines():
            log(f"  {line}")
        if result.returncode != 0:
            log(f"  ❌ post-to-pers-hub 失败 (rc={result.returncode})")
            log(f"  stderr: {result.stderr[-500:]}")
            state["errors"][skill_md.name] = f"post-to-pers-hub rc={result.returncode}"
            return False
    except subprocess.TimeoutExpired:
        log("  ❌ post-to-pers-hub 超时")
        state["errors"][skill_md.name] = "timeout"
        return False
    except Exception as e:
        log(f"  ❌ 调用 post-to-pers-hub 失败: {e}")
        state["errors"][skill_md.name] = str(e)
        return False

    # 成功
    state["processed"][skill_md.name] = fp
    state["errors"].pop(skill_md.name, None)
    log(f"  ✅ {fm.get('cn_name')} 上传成功")
    return True


def scan_once():
    """扫描一次,处理新文件"""
    state = load_state()
    if not SOURCE_DIR.exists():
        log(f"⚠️ 源目录不存在: {SOURCE_DIR}")
        return 0

    files = sorted(SOURCE_DIR.glob("*.md"))
    log(f"🔍 扫描 {SOURCE_DIR}: 找到 {len(files)} 个 .md")

    success = 0
    for f in files:
        if process_one(f, state):
            success += 1

    save_state(state)
    log(f"📊 本轮: {success}/{len(files)} 成功")
    return success


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="持续监控(每 2 分钟)")
    ap.add_argument("--interval", type=int, default=120, help="监控间隔秒数(默认 120)")
    args = ap.parse_args()

    log("=" * 60)
    log(f"👀 watch-zero-skills 启动 (interval={args.interval}s)")
    log(f"   源目录: {SOURCE_DIR}")
    log(f"   站点: {SITE_DIR}")

    if not args.watch:
        scan_once()
        return

    while True:
        try:
            scan_once()
        except KeyboardInterrupt:
            log("🛑 用户中断")
            break
        except Exception as e:
            log(f"❌ 扫描异常: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
