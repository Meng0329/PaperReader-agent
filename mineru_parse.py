#!/usr/bin/env python3
"""
MinerU API (VLM+OCR) PDF 解析 — 纯 MinerU 通道

文本提取 → Markdown + JSON(content_list) + 图片
无 PyMuPDF 干扰，确保解析结果准确可控

用法:
    python3 mineru_parse.py <pdf路径> [输出目录]
"""
import json, base64, sys, os
from pathlib import Path
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

SERVER = "http://10.200.37.71:8801"
API_KEY = "lgw-fe4c5edc0f436c40fbf305029e8caa42c9890468b39a1611cd1f80a9e97e0b44"


# ── 通道 A: MinerU API ──────────────────────────────────────────────

def _build_multipart(fields: dict, files: dict) -> tuple:
    boundary = "----MinerUBoundary" + os.urandom(8).hex()
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


def _parse_content_list(cl_raw) -> list:
    if isinstance(cl_raw, list):
        return cl_raw
    if isinstance(cl_raw, str):
        return json.loads(cl_raw)
    return []


def _run_mineru_api(pdf_path: Path, out_path: Path) -> dict:
    print("  ▶ [MinerU API] VLM+OCR 解析 ...")
    pdf_stem = pdf_path.stem

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    boundary, body = _build_multipart(
        fields={
            "backend": "hybrid-auto-engine",
            "return_md": "true",
            "return_content_list": "true",
            "formula_enable": "true",
            "table_enable": "true",
            "return_images": "true",
        },
        files={"files": (pdf_path.name, pdf_data, "application/pdf")},
    )
    req = Request(
        f"{SERVER}/v1/file_parse", data=body,
        headers={"Authorization": f"Bearer {API_KEY}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urlopen(req, timeout=600) as resp:
            raw = json.loads(resp.read())
    except HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get("error", {}).get("message", body)
        except Exception:
            msg = body
        print(f"    ✗ MinerU API 错误 ({e.code}): {msg}")
        return {"md_content": "", "content_list": [], "images": [], "status": "error"}

    # MinerU 在 results.{filename}.{md_content,content_list,images}
    task_status = raw.get("status", "unknown")
    r = raw.get("results", {}).get(pdf_stem, {})
    md_content = r.get("md_content", "")
    cl_raw = r.get("content_list", [])
    images_raw = r.get("images", [])

    # ── 保存 Markdown ──
    (out_path / "mineru_raw.md").write_text(md_content)
    print(f"    ✓ Markdown ({len(md_content):,} chars)")

    # ── 保存 content_list ──
    content_list = _parse_content_list(cl_raw)
    (out_path / "mineru_raw.json").write_text(
        json.dumps({"content_list": content_list}, ensure_ascii=False, indent=2))
    print(f"    ✓ JSON (content_list: {len(content_list)} items)")

    # ── 保存 MinerU 返回的图片 ──
    assets_dir = out_path / "assets"
    img_saved = 0
    if isinstance(images_raw, dict):
        for fname, data_uri in images_raw.items():
            if isinstance(data_uri, str) and data_uri.startswith("data:"):
                out_name = Path(fname).name
                if _data_uri_to_file(data_uri, assets_dir / out_name):
                    img_saved += 1
        print(f"    ✓ MinerU 图片: {img_saved}/{len(images_raw)} 张已保存")
    elif isinstance(images_raw, list):
        for i, entry in enumerate(images_raw):
            if isinstance(entry, str) and entry.startswith("data:"):
                fname = f"mineru_img_{i:02d}.png"
                if _data_uri_to_file(entry, assets_dir / fname):
                    img_saved += 1
        print(f"    ✓ MinerU 图片: {img_saved}/{len(images_raw)} 张已保存")

    # ── 计算耗时 ──
    import datetime
    total_time = 0
    t_start = raw.get("started_at") or raw.get("created_at")
    t_end = raw.get("completed_at") or raw.get("started_at")
    if t_start and t_end:
        try:
            dt_start = datetime.datetime.fromisoformat(t_start.replace("Z", "+00:00"))
            dt_end = datetime.datetime.fromisoformat(t_end.replace("Z", "+00:00"))
            total_time = (dt_end - dt_start).total_seconds()
        except Exception:
            pass

    print(f"    ✓ {task_status} ({total_time:.1f}s)")

    # 统一数据结构（兼容下游代码）
    return {
        "md_content": md_content,
        "content_list": content_list,
        "images": images_raw,
        "status": task_status,
        "timing": {"total": total_time},
        "_raw": raw,
    }


# ── 生成 source_map.json ─────────────────────────────────────────────

def _build_source_map(api_data: dict, pdf_name: str, assets_dir: Path):
    content_list = api_data.get("content_list", [])
    timing = api_data.get("timing", {})

    # 估算页数：从 content_list 中取最大 page_idx
    max_page = 0
    for item in content_list:
        p = item.get("page_idx", 0)
        if isinstance(p, (int, float)):
            max_page = max(max_page, int(p))

    sm = {
        "metadata": {
            "title": pdf_name,
            "source": f"MinerU API @ {SERVER}",
            "pages": max_page + 1 if content_list else 0,
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "confidence": "high",
        },
        "page_index": {}, "blocks": {}, "figures": {}, "tables": {},
    }

    if not content_list:
        return sm

    block_counter = 0
    fig_counter = 0
    tbl_counter = 0

    for item in content_list:
        item_type = item.get("type", "")
        page = item.get("page_idx", 0)
        if isinstance(page, float):
            page = int(page)
        page_key = str(page + 1)  # 1-indexed

        if item_type == "text":
            block_counter += 1
            bid = f"S{block_counter:03d}"
            text = (item.get("text") or "")[:120]
            sm["blocks"][bid] = {
                "page": page + 1,
                "type": "text",
                "description": text,
            }
            sm["page_index"].setdefault(page_key, []).append(bid)

        elif item_type == "image":
            fig_counter += 1
            fid = f"F{fig_counter:02d}"
            img_path = item.get("img_path", "")
            # Try to locate the actual image file in assets
            asset_path = ""
            if img_path:
                # img_path might be a relative path like "images/fig1.png"
                fname = Path(img_path).name
                candidates = list(assets_dir.glob(f"*{fname}*")) + list(assets_dir.glob(f"*{Path(img_path).stem}*"))
                if candidates:
                    asset_path = f"assets/{candidates[0].name}"

            sm["figures"][fid] = {
                "page": page + 1,
                "type": "figure",
                "description": f"Figure {fig_counter} (p{page + 1})",
                "asset": asset_path,
            }
            sm["page_index"].setdefault(page_key, []).append(fid)

        elif item_type == "table":
            tbl_counter += 1
            tid = f"T{tbl_counter:03d}"
            tbl_desc = (item.get("table_body") or "")[:80] if item.get("table_body") else f"Table {tbl_counter}"
            sm["tables"][tid] = {
                "page": page + 1,
                "type": "table",
                "description": tbl_desc,
                "asset": "",
            }
            sm["page_index"].setdefault(page_key, []).append(tid)

    return sm


# ── 主流程 ────────────────────────────────────────────────────────────

def parse_pdf(pdf_path: str, out_dir: str) -> dict:
    pdf_path = Path(pdf_path)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "assets").mkdir(exist_ok=True)

    print(f"▶ 开始解析: {pdf_path.name}")

    api_data = _run_mineru_api(pdf_path, out_path)

    # source_map.json
    sm = _build_source_map(api_data, pdf_path.stem, out_path / "assets")
    (out_path / "source_map.json").write_text(json.dumps(sm, ensure_ascii=False, indent=2))
    print(f"    ✓ source_map.json ({len(sm['blocks'])} 段, {len(sm['figures'])} 图, {len(sm['tables'])} 表)")

    # 报告
    content_list = api_data.get("content_list", [])
    text_items = sum(1 for c in content_list if c.get("type") == "text")
    img_items = sum(1 for c in content_list if c.get("type") == "image")
    tbl_items = sum(1 for c in content_list if c.get("type") == "table")
    timing = api_data.get("timing", {})
    total_time = timing.get("total", 0)

    print(f"\n✅ {pdf_path.name}")
    print(f"   耗时: {total_time:.1f}s (API)")
    print(f"   内容项: {text_items} 文本段, {img_items} 图片, {tbl_items} 表格")

    return api_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 mineru_parse.py <pdf路径> [输出目录]")
        print("示例: python3 mineru_parse.py paper.pdf docs/paper/论文目录")
        sys.exit(1)
    parse_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
