#!/usr/bin/env python3
"""Render every page of a PDF to PNG so the layout can be inspected.

Usage: python3 render_pages.py doc.pdf [outdir] [dpi]

Tries PyMuPDF, then pdftoppm, then qlmanage (first page only). Prints the paths.
"""
import os
import shutil
import subprocess
import sys


def with_fitz(pdf, outdir, dpi):
    import fitz
    doc = fitz.open(pdf)
    paths = []
    for i, page in enumerate(doc, 1):
        p = os.path.join(outdir, "page%02d.png" % i)
        page.get_pixmap(dpi=dpi).save(p)
        paths.append(p)
    return paths


def with_poppler(pdf, outdir, dpi):
    base = os.path.join(outdir, "page")
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, base], check=True)
    return sorted(os.path.join(outdir, f) for f in os.listdir(outdir) if f.startswith("page"))


def with_qlmanage(pdf, outdir):
    subprocess.run(["qlmanage", "-t", "-s", "1600", "-o", outdir, pdf],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return [os.path.join(outdir, f) for f in os.listdir(outdir) if f.endswith(".png")]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    pdf = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "pages"
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    os.makedirs(outdir, exist_ok=True)

    paths = None
    try:
        paths = with_fitz(pdf, outdir, dpi)          # multi-page and fast, prefer it
    except Exception:
        paths = None
    if not paths and shutil.which("pdftoppm"):
        paths = with_poppler(pdf, outdir, dpi)
    if not paths and shutil.which("qlmanage"):
        paths = with_qlmanage(pdf, outdir)           # first page only
    if not paths:
        print("no renderer available: install PyMuPDF or poppler, or open the PDF by hand")
        return 1

    for p in paths:
        print(p)
    print("%d page(s) rendered. Look at every one before delivering." % len(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
