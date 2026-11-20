#!/usr/bin/env python3
"""
Builder for UTAD activity PDFs.

Usage
-----
    python3 pdf-builder-template.py -o Gefaell_Inigo_UD2_AC89.pdf \
        --ac 89 --subject "FUNDAMENTOS DE HW" --date 17.11.2026 \
        --author "Iñigo Gefaell"

Edit the STORY section (or import the module and build your own list).
Everything above STORY is the house style; do not change it casually.

Dependencies: reportlab, Pillow.
"""
import argparse
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether)

W, H = A4
M = 22 * mm
CW = W - 2 * M

# ---------------------------------------------------------------- styles
ss = ParagraphStyle("ss", fontName="Helvetica", fontSize=10, leading=14,
                    alignment=TA_JUSTIFY, spaceAfter=6)
h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=13, leading=17,
                    spaceBefore=4, spaceAfter=6, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                    spaceBefore=10, spaceAfter=5, keepWithNext=1)
cap = ParagraphStyle("cap", fontName="Helvetica-Oblique", fontSize=8, leading=10.5,
                     textColor=colors.HexColor("#333333"), spaceBefore=3)
cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=11)
cellb = ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.5, leading=11)


# ---------------------------------------------------------------- helpers
def fig(path, w_mm, caption):
    """Image + caption, with 8 mm of air under the block."""
    im = PILImage.open(path)
    w, h = im.size
    ww = w_mm * mm
    t = Table([[Image(path, ww, ww * h / w)], [Paragraph(caption, cap)]], colWidths=[ww])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 8), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    t.hAlign = "CENTER"
    return t


def tabla(rows, widths_mm):
    """Grey header, thin grid, wrapping cells. Add Spacer(1, 4*mm) after it."""
    data = [[Paragraph(str(c), cellb if i == 0 else cell) for c in row]
            for i, row in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths_mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def portada(c, d, ac, subject, date, authors):
    """-[ACnn] / grey subject / yellow date + authors in the bottom-right."""
    c.saveState()
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 78)
    c.drawCentredString(W / 2, H * 0.50, "-[AC%s]" % ac)

    c.setFillColor(colors.HexColor("#8c8c8c"))
    sub = "-    " + subject
    fs, tr = 13, 0.7
    ancho = c.stringWidth(sub, "Helvetica", fs) + (len(sub) - 1) * tr
    t = c.beginText(W / 2 - ancho / 2, H * 0.455)
    t.setFont("Helvetica", fs)
    t.setCharSpace(tr)
    t.textOut(sub)
    c.drawText(t)

    c.setFillColor(colors.black)
    filas = [date] + ["- " + a for a in authors]
    fs = 11
    y = (21 + 8 * (len(filas) - 1)) * mm
    for fila in filas:
        ancho = c.stringWidth(fila, "Helvetica-Bold", fs)
        x = W - M - ancho
        c.setFillColor(colors.HexColor("#FFF200"))
        c.rect(x - 2.5 * mm, y - 1.5 * mm, ancho + 5 * mm, 6.5 * mm, stroke=0, fill=1)
        c.setFillColor(colors.black)
        t2 = c.beginText(x, y)
        t2.setFont("Helvetica-Bold", fs)
        t2.setCharSpace(0)          # never inherit the tracking
        t2.textOut(fila)
        c.drawText(t2)
        y -= 8 * mm
    c.restoreState()


# ---------------------------------------------------------------- STORY
def build_story():
    """Replace this with the real content. Skeleton below."""
    story = [NextPageTemplate("Body"), PageBreak()]

    story += [Paragraph("1. <bloque del enunciado>", h2),
              Paragraph("<una frase: qué haces y qué buscas>.", ss),
              # fig("fig/fig1.png", 145, "Figura 1. <qué se ve y qué demuestra>."),
              # tabla([["Comando", "Resultado", "Conclusión"],
              #        ["ip route", "default via 10.211.55.1", "hay puerta"]],
              #       [46, 60, 56]),
              # Spacer(1, 4 * mm),
              ]

    story += [Paragraph("<respuesta a la primera pregunta>.", ss),
              Spacer(1, 4 * mm),
              Paragraph("<b>Nota:</b> He usado inteligencia artificial agéntica para repasar la ortografía y corregir alguna falta.", ss)]
    return story


# ---------------------------------------------------------------- build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--ac", required=True, help="number, e.g. 89 for -[AC89]")
    ap.add_argument("--subject", default="FUNDAMENTOS DE HW",
                    help="FUNDAMENTOS DE HW | SISTEMAS OPERATIVOS")
    ap.add_argument("--date", required=True, help="d.m.yyyy")
    ap.add_argument("--author", action="append", default=[])
    args = ap.parse_args()

    doc = BaseDocTemplate(args.out, pagesize=A4, leftMargin=M, rightMargin=M,
                          topMargin=M, bottomMargin=M,
                          title="UD2_AC%s" % args.ac,
                          author="; ".join(args.author))
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[Frame(M, M, CW, H - 2 * M, id="c")],
                     onPage=lambda c, d: portada(c, d, args.ac, args.subject,
                                                 args.date, args.author)),
        PageTemplate(id="Body", frames=[Frame(M, M, CW, H - 2 * M, id="b")])])
    doc.build(build_story())
    print("ok:", args.out)


if __name__ == "__main__":
    main()
