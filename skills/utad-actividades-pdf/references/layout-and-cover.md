# Layout and cover — exact geometry

Everything here is measured from the PDFs the user accepted. Do not "improve" it.

## Page

A4, portrait. Margins: **22 mm on all four sides** → text frame 166 × 253 mm.
No header, no footer, no page number, no rule, nothing outside the frame.

Single body font family: Helvetica (reportlab built-in). No serif, no second family, no colour
in the body. Grey only for the cover subtitle and the figure captions.

## Styles (reportlab)

```python
ss   = ParagraphStyle("ss", fontName="Helvetica", fontSize=10, leading=14,
                      alignment=TA_JUSTIFY, spaceAfter=6)
h2   = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                      spaceBefore=10, spaceAfter=5, keepWithNext=1)
cap  = ParagraphStyle("cap", fontName="Helvetica", fontSize=8, leading=10.5,
                      textColor=HexColor("#333333"), spaceBefore=3)  # then italic
cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=11)
cellb= ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.5, leading=11)
```

Notes:

- `keepWithNext=1` on `h2` avoids a heading alone at the bottom. It does **not** protect
  against a heading + one-line paragraph + figure jumping; if that happens, wrap
  `[h2, paragraph, figure]` in a single `KeepTogether`.
- Body is justified. Never justify the cover.
- No bold inside body paragraphs. `cellb` is for table headers only.

## Cover

The user's reference: `assets/cover-reference.png`.

Three elements, nothing else:

1. **Title** `-[ACnn]` (or `-[AEnn]` / `-[EVnn]` when the deliverable is an AE/EV) —
   Helvetica-Bold **78 pt**, centred, baseline at `0.50 × H`. The literal characters: hyphen,
   opening bracket, the code and number, closing bracket (`--tag AE2` in
   `pdf-builder-template.py`).
2. **Subject line** `-    FUNDAMENTOS DE HW` or `-    SISTEMAS OPERATIVOS` — Helvetica
   **13 pt**, colour `#8C8C8C`, `charSpace = 0.7` (this exact value: more looks wrong), centred,
   baseline at `0.455 × H`. Keep the four spaces after the hyphen so the hyphen sits alone to
   the left, as in the reference.
3. **Bottom-right block** — two or three short lines: date, then one line per author.
   Helvetica-Bold 11 pt, black, each on a `#FFF200` rectangle. Right edge of every rectangle
   at `W − 22 mm`; the rectangle of the **last** line ends **19.5 mm above the bottom edge**;
   lines step **8 mm** upwards.

```python
def portada(c, d):
    c.saveState()
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 78)
    c.drawCentredString(W/2, H*0.50, "-[AC8]")

    c.setFillColor(colors.HexColor("#8c8c8c"))
    sub = "-    FUNDAMENTOS DE HW"
    fs, tr = 13, 0.7
    ancho = c.stringWidth(sub, "Helvetica", fs) + (len(sub) - 1) * tr
    t = c.beginText(W/2 - ancho/2, H*0.455)
    t.setFont("Helvetica", fs); t.setCharSpace(tr); t.textOut(sub)
    c.drawText(t)

    c.setFillColor(colors.black)
    filas = ["16.11.2026", "- Iñigo Gefaell"]          # date, then authors
    fs = 11
    y = (21 + 8*(len(filas)-1)) * mm                    # last baseline at 21 mm -> box bottom 19.5 mm
    for fila in filas:
        ancho = c.stringWidth(fila, "Helvetica-Bold", fs)
        x = W - M - ancho
        c.setFillColor(colors.HexColor("#FFF200"))
        c.rect(x - 2.5*mm, y - 1.5*mm, ancho + 5*mm, 6.5*mm, stroke=0, fill=1)
        c.setFillColor(colors.black)
        t2 = c.beginText(x, y)
        t2.setFont("Helvetica-Bold", fs); t2.setCharSpace(0); t2.textOut(fila)
        c.drawText(t2)
        y -= 8*mm
    c.restoreState()
```

Hard-won details, do not regress:

- `setCharSpace` on a canvas text object **persists** into later `drawString` calls in some
  reportlab versions. Draw the date and names through their own `beginText()` objects with
  `setCharSpace(0)`, exactly as above. Otherwise the PDF ends up with `1 0 . 1 1 . 2 0 2 6`.
- The date/name block must use the same right margin as the body (22 mm), not “the corner”.
  The rectangle adds 2.5 mm of padding, so the visible gap is 19.5 mm on the right and 19.5 mm
  at the bottom; both must be equal.
- Date format: `d.m.yyyy` (`16.11.2026`), no leading zeros needed beyond the day/month as
  written.
- Authors: one per line, each prefixed `- `. Surnames first is not used on the cover; the
  order is the one the user states.
- If the AC number is unknown, ask once. Do not ship `-[AC?]`.

## Figures

```python
def fig(path, w_mm, txt):
    im = Image.open(path); w, h = im.size
    ww = w_mm * mm
    t = Table([[Image(path, ww, ww*h/w)], [Paragraph(txt, cap)]], colWidths=[ww])
    t.setStyle(TableStyle([
        ("NOSPLIT", (0, 0), (-1, -1)),
        ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,1),(0,1),8), ("BOTTOMPADDING",(0,0),(0,0),0),
        ("VALIGN",(0,0),(-1,-1),"TOP")]))
    t.hAlign = "CENTER"
    return t
```

- Width: **130–170 mm**. Terminal captures: 130–150 mm when they are dense, 160–170 when
  they are sparse. Never exceed 166 mm (the frame width).
- The 8 mm bottom padding is the breathing room under the caption; without it the next heading
  sticks to the caption.
- Caption text: `Figura N. <what the reader sees and why it matters>.` One or two lines,
  italic grey. Count figures sequentially across the whole document.
- One figure per `fig()` call. Two screenshots side by side only when both are wide and short;
  by default stack them.
- For ReportLab `Drawing()` topology diagrams, offset text labels away from bus/connector lines
  and verify in rendered page PNGs that no stroke crosses text.

## Page budget (the arithmetic that decides pagination)

Usable text box: **253 mm tall** (297 − 22 − 22) by 166 mm wide. What each block costs:

| Element | Height |
| --- | --- |
| `h2` heading | 10 mm (8 if it is a single line) |
| body paragraph | 6 mm per line + 6 mm spaceAfter |
| figure | `width_mm / aspect_ratio` (see table) |
| caption | 9 mm for two lines, 5 mm for one, plus 8 mm gap after the block |
| table | ~9 mm header + 6 mm per row + 4 mm spacer after |

Height of a figure at a given width, `h = w / ratio`, where the ratio is `pixels_wide / pixels_tall`:

| Ratio | 150 mm | 160 mm | 166 mm |
| --- | --- | --- | --- |
| 2,0 (tall, wide terminal) | 75 | 80 | 83 |
| 2,3 (typical `prlctl capture` crop) | 65 | 70 | 72 |
| 2,6 | 58 | 62 | 64 |
| 3,0 (one command, few lines) | 50 | 53 | 55 |

So two captures of ratio 2,3 at 160 mm plus their captions are 158 mm: with two headings and
three short paragraphs a page holds exactly two blocks. Three figures of that size never fit on
one page, and that is the usual cause of the half-empty page.

## The short activity (three blocks and a question)

The most common shape, and it fits in cover + 2 pages:

```
page 1   block 1: heading, one line of intro, figure (160 mm), one paragraph with the numbers
         block 2: heading, one line of intro, figure (150 mm), one paragraph
page 2   block 3: heading, one line of intro, figure (150 mm), one paragraph, optional small table
         question: heading with the question, two short paragraphs, AI note
```

If block 3 lands at the foot of page 1 with its figure pushed to page 2, put `CondPageBreak(75 * mm)`
before its heading. If page 2 ends past the halfway mark, the document is fine as it is: a short
last page is normal, a half-empty page in the middle is not.

## Tables

```python
def tabla(rows, widths):
    data = [[Paragraph(c, cellb if i == 0 else cell) for c, ...]]
    t = Table(data, colWidths=[x*mm for x in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.4, HexColor("#999999")),
        ("BACKGROUND",(0,0),(-1,0), HexColor("#eeeeee")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),3), ("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t
```

- Header row light grey `#EEEEEE`, grid 0.4 pt `#999999`, cells as `Paragraph` so they wrap.
- Widths in mm and must sum to ≤ 166.
- **Always** leave 4 mm between a table and whatever comes next:
  `Spacer(1, 4*mm)` before the following paragraph. A table glued to a paragraph was an actual
  correction the user asked for.
- `repeatRows=1` so a table that breaks across pages repeats its header.
- Never let a table break with only its header on one page: if the first row cannot fit, push
  the whole table to the next page.

## Pagination rules

The failure modes seen in real reviews, and the fix for each:

| Symptom | Fix |
| --- | --- |
| Big blank at the bottom of a page | the next block is a `KeepTogether` that does not fit. Shrink the figure 10–15 mm or let the block split |
| Heading alone at the page bottom | `keepWithNext` on the heading, and wrap heading + first paragraph + figure in `KeepTogether` |
| Two-line paragraph split across pages | let reportlab keep it whole by wrapping the paragraph + figure in `KeepTogether`, or shorten the paragraph |
| Table separated from its heading | `keepWithNext` on the heading |
| Caption of figure N printed above figure N+1 | the figure block lost its image (missing file) — check the path |
| Last page with only three lines | acceptable, but try shrinking one figure so it joins the previous page |
| Text overlapping a figure's edge | the figure is wider than 166 mm or the table cell padding is negative |

## Fonts and glyphs

- Use `Helvetica`; the Spanish characters (`á é í ó ú ñ ü ¿ ¡`) work as-is.
- Superscripts (`2<super>24</super>`) for powers in calculations.
- `&mdash;` and `&ndash;` are **forbidden**; also forbidden in the visible text.
- `&middot;` is fine for separating short items in a cover or a header, but the body should
  not need it.
