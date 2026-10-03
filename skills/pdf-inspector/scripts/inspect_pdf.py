#!/usr/bin/env python3
"""Inspect a PDF using the pdf-inspector library.

Classifies the PDF (text/scanned/image/mixed), reports pages needing OCR,
encoding/table/column issues, and can extract plain text, Markdown, or
positioned text with font info.

Usage:
  python inspect_pdf.py <pdf> --mode inspect [--json]
  python inspect_pdf.py <pdf> --mode text [--out file.txt]
  python inspect_pdf.py <pdf> --mode markdown [--out file.md]
  python inspect_pdf.py <pdf> --mode positions [--pages 1,3,5]
"""

import argparse
import json
import sys


def main() -> None:
    p = argparse.ArgumentParser(description="Inspect a PDF with pdf-inspector")
    p.add_argument("pdf", help="Path to the PDF file")
    p.add_argument("--mode", choices=["inspect", "text", "markdown", "positions"], default="inspect")
    p.add_argument("--pages", help="Comma-separated 1-indexed page list, e.g. 1,3,5")
    p.add_argument("--out", help="Write extracted content to this file")
    p.add_argument("--json", action="store_true", help="Output inspect report as JSON")
    args = p.parse_args()

    import pdf_inspector

    pages = [int(x.strip()) for x in args.pages.split(",")] if args.pages else None

    if args.mode == "text":
        text = pdf_inspector.extract_text(args.pdf)
        if not text:
            print("提示：extract_text 返回空（该版式可能不受纯文本提取支持），建议改用 --mode markdown", file=sys.stderr)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text or "")
            print(f"文本已写入 {args.out}（{len(text or '')} 字符）")
        else:
            sys.stdout.write(text or "")
        return

    if args.mode == "markdown":
        result = pdf_inspector.process_pdf(args.pdf, pages=pages)
        md = result.markdown or ""
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Markdown 已写入 {args.out}（{len(md)} 字符）")
        else:
            sys.stdout.write(md)
        return

    if args.mode == "positions":
        items = pdf_inspector.extract_text_with_positions(args.pdf, pages=pages)
        for it in items:
            print(f"({it.x:.0f},{it.y:.0f}) size={it.font_size:.1f}  {it.text}")
        print(f"\n共 {len(items)} 个文本项")
        return

    # inspect (default)
    result = pdf_inspector.process_pdf(args.pdf, pages=pages)
    report = {
        "pdf": args.pdf,
        "pdf_type": result.pdf_type,
        "confidence": round(result.confidence, 2),
        "page_count": result.page_count,
        "processing_time_ms": result.processing_time_ms,
        "pages_needing_ocr": result.pages_needing_ocr,
        "ocr_reasons": {str(k): [r for r in v] for k, v in zip(result.pages_needing_ocr, result.ocr_reasons_by_page)},
        "pages_with_tables": result.pages_with_tables,
        "pages_with_columns": result.pages_with_columns,
        "is_complex_layout": result.is_complex_layout,
        "markdown_chars": len(result.markdown or ""),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    kind_label = {"text_based": "文本型", "scanned": "扫描件", "image_based": "图片型", "mixed": "混合型"}
    print("===== PDF 检查报告 =====")
    print(f"文件      : {args.pdf}")
    print(f"类型      : {kind_label.get(result.pdf_type, result.pdf_type)}（置信度 {result.confidence:.0%}）")
    print(f"页数      : {result.page_count}")
    print(f"耗时      : {result.processing_time_ms} ms")
    if result.pages_needing_ocr:
        print(f"需OCR页   : {result.pages_needing_ocr}（原因见上）")
    else:
        print("需OCR页   : 无")
    print(f"含表格页  : {result.pages_with_tables if result.pages_with_tables else '无'}")
    print(f"含分栏页  : {result.pages_with_columns if result.pages_with_columns else '无'}")
    print(f"复杂版式  : {'是' if result.is_complex_layout else '否'}")
    print(f"Markdown  : {len(result.markdown or '')} 字符")
    print("=========================")


if __name__ == "__main__":
    main()
