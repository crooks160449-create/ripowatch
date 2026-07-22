"""
MkDocs build hook: auto-convert .pptx files in docs/ to browsable Markdown pages.

Usage:
  1. Drop .pptx files anywhere under docs/
  2. Run mkdocs build or mkdocs serve
  3. Each .pptx gets a same-named .md with extracted text, tables, and images
  4. The .md is auto-rendered by MkDocs with Material theme styling

Dependencies: python-pptx, Pillow (already installed)
"""

import shutil
import uuid
from pathlib import Path


# ---------------------------------------------------------------------------
# PPTX content extraction
# ---------------------------------------------------------------------------

def _extract_pptx_slides(pptx_path: str, img_output_dir: Path):
    """Extract text, tables, and images from each slide. Images saved to img_output_dir."""
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    prs = Presentation(pptx_path)
    slides = []

    for slide_num, slide in enumerate(prs.slides, 1):
        slide_data = {"number": slide_num, "title": "", "elements": []}
        _first_text = None

        # Extract title from title placeholder
        if slide.shapes.title and slide.shapes.title.has_text_frame:
            t = slide.shapes.title.text.strip()
            if t:
                slide_data["title"] = t

        for shape in slide.shapes:
            if shape == slide.shapes.title:
                continue

            elem = None

            # --- Text ---
            if shape.has_text_frame and not shape.has_table:
                paragraphs = []
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        p = {"text": text, "level": para.level or 0}
                        try:
                            p["bold"] = bool(para.runs[0].font.bold) if para.runs else False
                        except Exception:
                            p["bold"] = False
                        paragraphs.append(p)
                if paragraphs:
                    if _first_text is None:
                        _first_text = paragraphs[0]["text"]
                    elem = {"type": "text", "paragraphs": paragraphs}

            # --- Table ---
            if shape.has_table:
                table = shape.table
                rows_data = []
                for row in table.rows:
                    rows_data.append([cell.text.strip() for cell in row.cells])
                if rows_data:
                    elem = {"type": "table", "rows": rows_data}

            # --- Image ---
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    image = shape.image
                    ext_map = {
                        "image/png": "png", "image/jpeg": "jpg",
                        "image/gif": "gif", "image/bmp": "bmp",
                    }
                    ext = ext_map.get(image.content_type, "png")
                    img_id = f"s{slide_num}_{uuid.uuid4().hex[:8]}"
                    img_path = img_output_dir / f"{img_id}.{ext}"
                    img_path.parent.mkdir(parents=True, exist_ok=True)
                    img_path.write_bytes(image.blob)
                    elem = {
                        "type": "image",
                        "src": f"../assets/pptx/{img_id}.{ext}",
                        "alt": f"Slide {slide_num} image",
                    }
                except Exception:
                    pass

            if elem:
                slide_data["elements"].append(elem)

        # Fallback: if no title placeholder, use first text found
        if not slide_data["title"] and _first_text:
            slide_data["title"] = _first_text

        slides.append(slide_data)

    return slides


# ---------------------------------------------------------------------------
# Render slides to Markdown
# ---------------------------------------------------------------------------

def _render_slides_to_markdown(slides: list, title: str) -> str:
    """Render extracted slides as a Material-theme-friendly Markdown string."""
    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"!!! info \"共 {len(slides)} 页幻灯片\"")
    lines.append("    本页面由 PPTX 课件自动转换生成。每页的文本、表格、图片均在下方展示，无需下载。")
    lines.append("")

    for s in slides:
        slide_title = s["title"] or f"第 {s['number']} 页"
        lines.append(f"## {slide_title}")
        lines.append("")

        if not s["elements"]:
            lines.append("*（此页无可提取的文本内容）*")
            lines.append("")
            continue

        for elem in s["elements"]:
            if elem["type"] == "text":
                for p in elem["paragraphs"]:
                    indent = "    " * p.get("level", 0)
                    text = p["text"].replace("\n", " ")
                    if p.get("bold"):
                        text = f"**{text}**"
                    lines.append(f"{indent}- {text}")
                lines.append("")

            elif elem["type"] == "table":
                rows = elem["rows"]
                if not rows:
                    continue
                lines.append("| " + " | ".join(str(c) for c in rows[0]) + " |")
                lines.append("| " + " | ".join("---" for _ in rows[0]) + " |")
                for row in rows[1:]:
                    padded = list(row) + [""] * (len(rows[0]) - len(row))
                    cells = [str(c) for c in padded[:len(rows[0])]]
                    lines.append("| " + " | ".join(cells) + " |")
                lines.append("")

            elif elem["type"] == "image":
                lines.append(f'<figure markdown="span">')
                lines.append(f"  ![{elem.get('alt', 'image')}]({elem['src']})")
                lines.append(f"</figure>")
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MkDocs hook entry point
# ---------------------------------------------------------------------------

def on_pre_build(*, config, **kwargs):
    """MkDocs pre-build hook: scan docs/ for .pptx files and generate .md pages."""
    docs_dir = Path(config["docs_dir"])
    assets_img_dir = docs_dir / "assets" / "pptx"

    # Clean old extracted images
    if assets_img_dir.exists():
        shutil.rmtree(assets_img_dir)
    assets_img_dir.mkdir(parents=True, exist_ok=True)

    pptx_files = list(docs_dir.rglob("*.pptx"))
    if not pptx_files:
        print("[pptx-hook] No PPTX files found, skipping.")
        return

    print(f"[pptx-hook] Found {len(pptx_files)} PPTX file(s), converting...")

    for pptx_path in pptx_files:
        rel = pptx_path.relative_to(docs_dir)
        md_path = pptx_path.with_suffix(".md")
        title = pptx_path.stem

        print(f"  -> {rel}")

        slides = _extract_pptx_slides(str(pptx_path), assets_img_dir)
        if not slides:
            print(f"     [WARN] No content extracted")
            continue

        markdown = _render_slides_to_markdown(slides, title)
        md_path.write_text(markdown, encoding="utf-8")

        print(f"     [OK] Generated {md_path.relative_to(docs_dir)} ({len(slides)} slides)")

    print("[pptx-hook] Done.")
