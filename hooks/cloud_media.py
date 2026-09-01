# -*- coding: utf-8 -*-
"""
MkDocs hook: 把清华云盘预览外链自动解析为视频直链并生成播放器。

用法（写在 Markdown 文件里）：
    {{ cloud_video("https://cloud.tsinghua.edu.cn/f/e9a40e45abc34f1386f0/") }}
    {{ cloud_video("https://cloud.tsinghua.edu.cn/f/e9a40e45abc34f1386f0/", "第一讲视频") }}

构建时自动：
  1. 访问云盘预览外链页面
  2. 提取页面里的 seafhttp 视频直链
  3. 替换为 HTML5 <video> 播放器

若抓取失败（无网络等），会退化成普通链接，不影响构建。
"""

import html
import re
import urllib.request


PLACEHOLDER = re.compile(
    r'\{\{\s*cloud_video\s*\(\s*"([^"]+)"\s*'
    r'(?:,\s*"([^"]*)")?\s*\)\s*\}\}'
)

# 每个构建进程只解析一次同一个外链，避免重复请求
_CACHE: dict[str, str | None] = {}


def _unescape_js(text: str) -> str:
    """把 JavaScript 的 \\uXXXX 转义还原成实际字符。"""
    return re.sub(
        r"\\u([0-9a-fA-F]{4})",
        lambda m: chr(int(m.group(1), 16)),
        text,
    )


def _resolve_direct_url(share_url: str) -> str | None:
    """从云盘预览外链页面提取 seafhttp 视频直链。"""
    if share_url in _CACHE:
        return _CACHE[share_url]

    direct_url = None
    try:
        req = urllib.request.Request(
            share_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            page = resp.read().decode("utf-8", errors="replace")

        match = re.search(
            r'https?://[^"\'\s]*seafhttp/files/[^"\'\s]+',
            page,
        )
        if match:
            direct_url = _unescape_js(match.group(0))
    except Exception:
        direct_url = None

    _CACHE[share_url] = direct_url
    return direct_url


def _render_player(direct_url: str, title: str) -> str:
    """生成带控件的 HTML5 视频播放器。"""
    safe_src = html.escape(direct_url, quote=True)
    title_html = f" title=\"{html.escape(title, quote=True)}\"" if title else ""
    caption = f"\n<figcaption>{html.escape(title)}</figcaption>" if title else ""
    return (
        '<figure class="cloud-video">\n'
        f'  <video controls playsinline preload="metadata"{title_html}>\n'
        f'    <source src="{safe_src}" type="video/mp4">\n'
        "    您的浏览器不支持 HTML5 视频播放。\n"
        "  </video>\n"
        f"{caption}\n"
        "</figure>\n\n"
    )


def on_page_markdown(markdown, page, config, files, **kwargs):
    """MkDocs 事件钩子：替换页面里的云盘视频占位符。"""

    def replace(match: re.Match) -> str:
        share_url = match.group(1)
        title = match.group(2) or ""
        direct_url = _resolve_direct_url(share_url)
        if direct_url:
            return _render_player(direct_url, title)
        return f"[{title or '在清华云盘查看视频'}]({share_url})"

    return PLACEHOLDER.sub(replace, markdown)
