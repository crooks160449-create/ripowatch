# -*- coding: utf-8 -*-
"""
MkDocs hook: 图片画廊。

用法（写在 Markdown 文件里）：
    {{ gallery("assets/gallery") }}

参数是 docs/ 下的图片目录相对路径。构建时自动：
  1. 扫描该目录里的所有图片
  2. 生成响应式缩略图网格
  3. 点击图片弹出大图查看（支持左右切换、键盘、计数）
"""

import itertools
import re
from pathlib import Path


GALLERY_PATTERN = re.compile(r'\{\{\s*gallery\("([^"]+)"\)\s*\}\}')
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

_ids = itertools.count()


def _relative_url(img: Path, docs_dir: Path, md_parent: Path) -> str:
    """生成从 Markdown 页面到图片的相对 URL。"""
    rel = img.relative_to(docs_dir).as_posix()
    depth = len(md_parent.relative_to(docs_dir).parts) + 1
    return "../" * depth + rel


def _render_gallery(images: list[Path], docs_dir: Path,
                    md_parent: Path, gid: int) -> str:
    """渲染缩略图网格 + 点击放大灯箱。"""
    urls = [_relative_url(p, docs_dir, md_parent) for p in images]
    url_json = ",\n".join(f'    "{u}"' for u in urls)

    items = "\n".join(
        f'  <button class="gallery-item" onclick="openGallery({gid}, {i})">'
        f'<img src="{u}" alt="图片 {i + 1}" loading="lazy"></button>'
        for i, u in enumerate(urls)
    )

    return f"""
<div class="gallery-grid" id="gallery-grid-{gid}">
{items}
</div>

<div class="gallery-lightbox" id="gallery-lightbox-{gid}" hidden>
  <button class="gallery-close" onclick="closeGallery({gid})" aria-label="关闭">&#10005;</button>
  <button class="gallery-prev" onclick="galleryNav({gid}, -1)" aria-label="上一张">&#10094;</button>
  <img class="gallery-stage-img" id="gallery-main-{gid}" src="" alt="">
  <button class="gallery-next" onclick="galleryNav({gid}, 1)" aria-label="下一张">&#10095;</button>
  <div class="gallery-counter" id="gallery-counter-{gid}">1 / {len(urls)}</div>
</div>

<style>
.gallery-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
  margin: 16px 0;
}}
.gallery-item {{
  padding: 0; border: 0; border-radius: 8px; overflow: hidden;
  cursor: zoom-in; background: #1f2430; aspect-ratio: 4/3;
}}
.gallery-item img {{
  width: 100%; height: 100%; object-fit: cover; display: block;
  transition: transform .2s ease;
}}
.gallery-item:hover img {{ transform: scale(1.05); }}
.gallery-lightbox {{
  position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,.92);
  display: flex; align-items: center; justify-content: center;
}}
.gallery-lightbox[hidden] {{ display: none; }}
.gallery-stage-img {{
  max-width: 92vw; max-height: 88vh; border-radius: 8px;
}}
.gallery-close, .gallery-prev, .gallery-next {{
  position: fixed; z-index: 1001; border: 0; cursor: pointer;
  background: rgba(255,255,255,.12); color: #fff;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
}}
.gallery-close {{ top: 18px; right: 18px; width: 42px; height: 42px; font-size: 20px; }}
.gallery-prev {{ left: 16px; top: 50%; transform: translateY(-50%); width: 46px; height: 46px; font-size: 20px; }}
.gallery-next {{ right: 16px; top: 50%; transform: translateY(-50%); width: 46px; height: 46px; font-size: 20px; }}
.gallery-close:hover, .gallery-prev:hover, .gallery-next:hover {{ background: rgba(94,108,255,.75); }}
.gallery-counter {{
  position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
  background: rgba(0,0,0,.65); color: #eee; padding: 4px 12px;
  border-radius: 999px; font-size: 13px; z-index: 1001;
}}
</style>

<script>
var galleryImages_{gid} = [
{url_json}
];
var galleryIndex_{gid} = 0;

function openGallery(gid, idx) {{
  galleryIndex_{gid} = idx;
  var box = document.getElementById("gallery-lightbox-" + gid);
  box.hidden = false;
  document.body.style.overflow = "hidden";
  galleryUpdate_{gid}();
}}

function closeGallery(gid) {{
  document.getElementById("gallery-lightbox-" + gid).hidden = true;
  document.body.style.overflow = "";
}}

function galleryNav(gid, delta) {{
  var arr = window["galleryImages_" + gid];
  galleryIndex_{gid} = (galleryIndex_{gid} + delta + arr.length) % arr.length;
  galleryUpdate_{gid}();
}}

function galleryUpdate_{gid}() {{
  var arr = window["galleryImages_" + gid];
  document.getElementById("gallery-main-" + gid).src = arr[galleryIndex_{gid}];
  document.getElementById("gallery-counter-" + gid).textContent =
    (galleryIndex_{gid} + 1) + " / " + arr.length;
}}

document.addEventListener("keydown", function(e) {{
  var box = document.getElementById("gallery-lightbox-{gid}");
  if (box.hidden) return;
  if (e.key === "Escape") closeGallery({gid});
  if (e.key === "ArrowLeft") galleryNav({gid}, -1);
  if (e.key === "ArrowRight") galleryNav({gid}, 1);
}});
</script>
"""


def on_page_markdown(markdown, page, config, files, **kwargs):
    """MkDocs 事件钩子：替换页面里的画廊占位符。"""
    docs_dir = Path(config["docs_dir"])

    def replace(match: re.Match) -> str:
        rel_dir = match.group(1).strip("/")
        gallery_dir = docs_dir / rel_dir
        if not gallery_dir.is_dir():
            return f'<!-- gallery not found: {rel_dir} -->'

        images = sorted(
            p for p in gallery_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS
        )
        if not images:
            return f'<!-- no images in: {rel_dir} -->'

        md_parent = docs_dir / Path(page.file.src_path).parent
        return _render_gallery(images, docs_dir, md_parent, next(_ids))

    return GALLERY_PATTERN.sub(replace, markdown)
