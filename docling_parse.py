#!/usr/bin/env python3
"""
Docling API + PyMuPDF 双通道 PDF 解析

通道 A — Docling API: 文本提取 → Markdown + JSON(DoclingDocument) + 全页渲染图
通道 B — PyMuPDF:     图片提取 → assets/fig_p{page}_{idx}.{ext} (独立图/表)
                       + 按 Docling 检测顺序生成 alias: fig_{n:02d}_p{page}.png

用法:
    python3 docling_parse.py <pdf路径> [输出目录]

依赖: pip3 install PyMuPDF
"""
import json, base64, sys, os, shutil, re
from pathlib import Path
from datetime import datetime
from urllib.request import Request, urlopen

SERVER = "http://10.200.37.71:8801"
API_KEY = "lgw-b38641ab6c262756e34cb38d15cd2d19088bf30c2099f83bbd646180f0055302"


# ── 通道 A: Docling API ──────────────────────────────────────────────

def _build_multipart(fields: dict, files: dict) -> tuple:
    boundary = "----DoclingBoundary" + os.urandom(8).hex()
    body = b""
    for key, value in fields.items():
        if isinstance(value, list):
            for v in value:
                body += f"--{boundary}\r\n".encode()
                body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                body += f"{v}\r\n".encode()
        else:
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += f"{value}\r\n".encode()
    for field_name, (file_name, file_data, content_type) in files.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'.encode()
        body += f"Content-Type: {content_type}\r\n\r\n".encode()
        body += file_data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return boundary, body


def _data_uri_to_file(uri: str, out_path: Path) -> bool:
    if not uri or not uri.startswith("data:"):
        return False
    try:
        _, b64 = uri.split(",", 1)
        out_path.write_bytes(base64.b64decode(b64))
        return True
    except Exception:
        return False


def _run_docling_api(pdf_path: Path, out_path: Path) -> dict:
    print("  ▶ [Docling API] 文本解析 ...")
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    boundary, body = _build_multipart(
        fields={
            "to_formats": ["md", "json"],
            "do_ocr": "true",
            "do_table_structure": "true",
            "do_formula_enrichment": "true",
            "include_images": "true",
            "image_export_mode": "embedded",
        },
        files={"files": (pdf_path.name, pdf_data, "application/pdf")},
    )
    req = Request(
        f"{SERVER}/v1/convert/file", data=body,
        headers={"Authorization": f"Bearer {API_KEY}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())

    doc = data["document"]
    (out_path / "docling_raw.md").write_text(doc.get("md_content", ""))
    print(f"    ✓ Markdown ({len(doc.get('md_content','')):,} chars)")

    json_content = doc.get("json_content")
    if json_content:
        (out_path / "docling_raw.json").write_text(
            json.dumps(json_content, ensure_ascii=False, indent=2))
        print(f"    ✓ JSON (v{json_content.get('version','?')})")

    # 全页渲染图
    if json_content:
        for pno_str, pdata in json_content.get("pages", {}).items():
            img = pdata.get("image", {})
            uri = img.get("uri", "")
            if uri:
                ext = img.get("mimetype", "image/png").split("/")[-1]
                _data_uri_to_file(uri, out_path / "assets" / f"page_{int(pno_str):02d}.{ext}")
        print(f"    ✓ 全页图 ({len(json_content['pages'])} 张)")

    print(f"    ✓ {data['status']} ({data['processing_time']:.1f}s)")
    return data, json_content


# ── 通道 B: PyMuPDF 提图 ──────────────────────────────────────────────

def _run_pymupdf(pdf_path: Path, assets_dir: Path) -> int:
    print("  ▶ [PyMuPDF] 独立图片提取 ...")
    try:
        import fitz
    except ImportError:
        print("    ⚠ 未安装 PyMuPDF (pip3 install PyMuPDF)，跳过")
        return 0

    doc = fitz.open(pdf_path)
    seen = set()
    count = 0

    for pn in range(doc.page_count):
        for idx, img in enumerate(doc[pn].get_images(full=True)):
            base = doc.extract_image(img[0])
            data = base["image"]
            if len(data) < 5000:
                continue
            h = hash(data)
            if h in seen:
                continue
            seen.add(h)
            fname = f"fig_p{pn+1:02d}_{idx+1:02d}.{base['ext']}"
            (assets_dir / fname).write_bytes(data)
            count += 1

    doc.close()
    print(f"    ✓ {count} 张独立图片")
    return count


# ── 生成 source_map.json ─────────────────────────────────────────────

def _build_source_map(json_content: dict, pdf_name: str, assets_dir: Path):
    sm = {
        "metadata": {
            "title": pdf_name,
            "source": f"Docling API @ {SERVER}",
            "pages": len(json_content.get("pages", {})) if json_content else 0,
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "confidence": "high",
        },
        "page_index": {}, "blocks": {}, "figures": {}, "tables": {},
    }

    if not json_content:
        return sm

    # blocks from texts[]
    for t in json_content.get("texts", []):
        prov = (t.get("prov") or [{}])[0]
        pn = str(prov.get("page_no", 1))
        label = t.get("label", "")
        if label in ("section_header", "caption"):
            bid = f"S{len(sm['blocks'])+1:03d}"
            sm["blocks"][bid] = {"page": int(pn), "type": label,
                                 "description": (t.get("text") or "")[:80]}
            sm["page_index"].setdefault(pn, []).append(bid)

    # figures from Docling pictures[] → matched to actual fig_ p{page} files
    pic_page_map = {}  # page_no → list of picture indices
    for i, pic in enumerate(json_content.get("pictures", [])):
        prov = (pic.get("prov") or [{}])[0]
        pn = prov.get("page_no", 0)
        pic_page_map.setdefault(pn, []).append(i)

    # Scan assets for fig_ files
    fig_counter = 0
    for pn in sorted(pic_page_map.keys()):
        for pic_i in pic_page_map[pn]:
            fig_counter += 1
            # Try to find matching fig_p{page} file
            candidates = sorted(assets_dir.glob(f"fig_p{pn:02d}_*"))
            if not candidates:
                continue
            # Use the first candidate for this page (or match by proximity)
            f = candidates[0]
            fid = f"F{fig_counter:02d}"
            sm["figures"][fid] = {
                "page": pn,
                "type": "figure",
                "description": f"Figure {fig_counter} (p{pn})",
                "asset": f"assets/{f.name}",
            }

    # tables
    for i, tbl in enumerate(json_content.get("tables", [])):
        prov = (tbl.get("prov") or [{}])[0]
        sm["tables"][f"T{i+1:03d}"] = {
            "page": prov.get("page_no", 0),
            "type": "table",
            "description": (tbl.get("captions") or [{}])[0].get("text", "")[:80] if tbl.get("captions") else f"Table {i+1}",
            "asset": "",
        }

    return sm


def _create_named_aliases(json_content: dict, assets_dir: Path):
    """按 Docling picture 顺序创建 fig_{n:02d}_p{page}.png alias"""
    if not json_content:
        return
    counter = 0
    for pic in json_content.get("pictures", []):
        prov = (pic.get("prov") or [{}])[0]
        pn = prov.get("page_no", 0)
        if not pn:
            continue
        counter += 1
        candidates = sorted(assets_dir.glob(f"fig_p{pn:02d}_*"))
        if not candidates:
            continue
        # Copy first candidate with sequential name
        src = candidates[0]
        dst = assets_dir / f"fig_{counter:02d}_p{pn}.png"
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"    alias: {dst.name} ← {src.name}")


# ── 主流程 ────────────────────────────────────────────────────────────

def parse_pdf(pdf_path: str, out_dir: str) -> dict:
    pdf_path = Path(pdf_path)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "assets").mkdir(exist_ok=True)

    print(f"▶ 开始解析: {pdf_path.name}")

    # 通道 A: Docling
    data, json_content = _run_docling_api(pdf_path, out_path)

    # 通道 B: PyMuPDF 提图
    fig_count = _run_pymupdf(pdf_path, out_path / "assets")

    # 创建 fig_{n:02d}_p{page}.png 别名
    _create_named_aliases(json_content, out_path / "assets")

    # source_map.json
    sm = _build_source_map(json_content, pdf_path.stem, out_path / "assets")
    (out_path / "source_map.json").write_text(json.dumps(sm, ensure_ascii=False, indent=2))
    print(f"    ✓ source_map.json ({len(sm['blocks'])} 段, {len(sm['figures'])} 图, {len(sm['tables'])} 表)")

    # 报告
    page_render_count = len(list((out_path / "assets").glob("page_*.png")))
    alias_count = len(list((out_path / "assets").glob("fig_??_p*.png")))
    print(f"\n✅ {pdf_path.name}")
    print(f"   耗时: {data['processing_time']:.1f}s (API)")
    print(f"   全页图: {page_render_count} 张")
    print(f"   独立图: {fig_count} 张 (via PyMuPDF)")
    print(f"   别名: {alias_count} 张 (fig_NN_pPAGE.png 格式 — 按 Docling 检测顺序)")
    if json_content:
        print(f"   文本块: {len(json_content.get('texts', []))} | 图元: {len(json_content.get('pictures', []))} | 表格: {len(json_content.get('tables', []))}")

    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 scripts/docling_parse.py <pdf路径> [输出目录]")
        print("示例: python3 scripts/docling_parse.py paper.pdf docs/paper/论文目录")
        sys.exit(1)
    parse_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
