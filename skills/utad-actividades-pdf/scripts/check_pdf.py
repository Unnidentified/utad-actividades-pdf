#!/usr/bin/env python3
"""Grade a finished PDF against the house rules, with measurements instead of opinions.

Usage:
    python3 check_pdf.py Apellido_Nombre_UD2_AC12.pdf
    python3 check_pdf.py IMSO_UD2_AE2_Gefaell_Inigo.pdf --max-pages 8

Checks the file name, the cover geometry (yellow boxes measured in the PDF), the absence of
em/en dashes, banned vocabulary, label-colon paragraph starts, bold in body text, headers and
footers, the AI note (present and with "Nota:" in bold), the figures and captions, and the
page count. Every line must read PASS before the file is delivered. Exit 1 on any FAIL.
"""
import argparse
import re
import sys

import pymupdf

ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--max-pages", type=int, default=5,
                help="maximum allowed total pages including cover (default: 5)")
ap.add_argument("--tag", help="expected cover tag inside -[...], e.g. AC12 or AE2")
ap.add_argument("--allow-no-question", action="store_true",
                help="do not fail when body text contains no '?'")
args = ap.parse_args()

PDF = args.pdf
doc = pymupdf.open(PDF)
pages = doc.page_count
W, H = doc[0].rect.width, doc[0].rect.height
MM = 72 / 25.4

text = "\n".join(p.get_text() for p in doc)
cover_text = doc[0].get_text()
P = []          # (ok, label, detail)


def check(ok, label, detail=""):
    P.append((ok, label, detail))


# --- filename (supports Surname_Name_UDx_ACy.pdf, Surname_Name_SUBJECT_UDx_EVy.pdf, and SUBJECT_UDx_AEy_Surname_Name.pdf)
name = PDF.rsplit("/", 1)[-1]
word = r"[A-Za-zÁÉÍÓÚÑáéíóúñ-]+"
subj = r"[A-Z]{2,6}"
ud_tag = r"UD\d+_(?:AC|AE|EV)\d+(?:-\d+)?"
name_ok = re.fullmatch(
    rf"(?:(?:{subj}_)?{word}_{word}(?:_{subj})?_{ud_tag}|{subj}_{ud_tag}_{word}_{word})\.pdf",
    name,
) is not None
check(name_ok, "nombre del archivo", name)

# --- cover geometry: yellow highlight boxes
d = doc[0].get_drawings()
ys = []
for it in d:
    f = it.get("fill")
    if f and f[0] > 0.9 and f[1] > 0.85 and f[2] < 0.25:
        ys.append(it["rect"])
if ys:
    right = W - max(r.x1 for r in ys)
    bottom = H - max(r.y1 for r in ys)
    check(abs(right - bottom) < 1.0 * MM, "portada: margen derecho == margen inferior",
          "derecha %.1f mm / abajo %.1f mm" % (right / MM, bottom / MM))
    check(18 < right / MM < 24, "portada: margen ~22 mm", "%.1f mm" % (right / MM))
else:
    check(False, "portada: no encuentro los recuadros amarillos", "")

# --- cover title present, subtitle not letter-spaced
m_tag = re.search(r"\b(AC|AE|EV)(\d+)\b", args.tag or name.replace("_", " "))
if m_tag:
    kind, num = m_tag.group(1), m_tag.group(2)
    check(re.search(r"\[\s*" + kind + r"\s*" + num + r"\s*\]", cover_text.replace("\n", " ")) is not None,
          "portada: título -[%s%s]" % (kind, num), "")
else:
    check(False, "portada: título -[ACn/AEn]", "sin código AC/AE/EV en el nombre ni --tag")
spaced_date = re.search(r"\d\s+\.\s+\d|\d\s+\d\s*\.\s*\d\s+\d\s*\.\s*2\s+0", cover_text) is not None
check(not spaced_date, "portada: fecha sin interletrado", "")
check("Iñigo Gefaell" in text, "nombre en la portada", "")

# --- forbidden things in the whole document
banned = ["fundamental", "clave", "crucial", "robusto", "óptimo", "garantizar", "cabe destacar",
          "en definitiva", "en conclusión", "en resumen", "asimismo", "adicionalmente",
          "no obstante", "se procede a", "en una frase", "en el mundo actual", "sinergia"]
hits = [w for w in banned
        if re.search(r"(?<![\wáéíóúüñ])" + re.escape(w) + r"(?![\wáéíóúüñ])", text.lower())]
check(not hits, "sin vocabulario de IA", ", ".join(hits) if hits else "limpio")

check("—" not in text and "–" not in text, "sin rayas largas", "")

labels = re.findall(r"^\s*(Políticas|Formación|Conclusión|Resumen|Análisis|Plan|Objetivo):",
                    text, re.M)
check(not labels, "sin párrafos que empiezan por etiqueta", ", ".join(labels) if labels else "")

edge = []
for i, p in enumerate(doc, 1):
    if i == 1:
        continue
    for b in p.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            y0, y1 = ln["bbox"][1], ln["bbox"][3]
            if y0 < 22 * MM - 2 or y1 > H - 20 * MM:
                edge.append("p%d %.0f-%.0f pt" % (i, y0, y1))
check(not edge and "Página " not in text, "sin cabeceras ni pies",
      "; ".join(edge[:3]) if edge else "márgenes limpios")

# --- bold in body: bold spans at body size
bold_body = []
for p in doc:
    for b in p.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                if "Bold" in sp["font"] and 9.8 < sp["size"] < 10.6 and sp["text"].strip():
                    if not sp["text"].strip().startswith("Nota"):
                        bold_body.append(sp["text"][:40])
check(not bold_body, "sin negritas en el cuerpo",
      "; ".join(bold_body[:3]) if bold_body else "limpio")

# --- AI note
check("inteligencia artificial agéntica" in text, "nota de IA presente", "")
note_bold = any("Bold" in sp["font"] and "Nota" in sp["text"]
                for p in doc for b in p.get_text("dict")["blocks"]
                for ln in b.get("lines", []) for sp in ln["spans"])
check(note_bold, "«Nota:» en negrita", "")

# --- evidence: at least two images, captions
imgs = sum(len(p.get_images()) for p in doc)
caps = re.findall(r"Figura \d+(?:\s*\([^)]+\))?\.", text)
check(imgs >= 2, "capturas reales", "%d imágenes" % imgs)
check(len(caps) >= 2, "pie de figura", "%d pies" % len(caps))
check(len(caps) == imgs, "una figura por captura", "%d pies / %d imágenes" % (len(caps), imgs))

# --- answers: the statement's question marks
if not args.allow_no_question:
    check(text.count("?") >= 1, "hay respuesta a la pregunta", "")
check(pages <= args.max_pages, "extensión contenida (<= %d pág.)" % args.max_pages, "%d páginas" % pages)

print("PDF: %s  (%d páginas, %.0f×%.0f mm)" % (name, pages, W / MM, H / MM))
bad = 0
for ok, label, detail in P:
    print("  %s  %-46s %s" % ("PASS" if ok else "FAIL", label, detail))
    bad += 0 if ok else 1
print("\n%d/%d PASS" % (len(P) - bad, len(P)))
sys.exit(1 if bad else 0)
