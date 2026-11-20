#!/usr/bin/env python3
"""Lint a draft for the things that get rejected in review.

Usage:
    python3 check_doc.py build.py            # scans a reportlab builder
    python3 check_doc.py documento.md        # scans plain text / markdown
    python3 check_doc.py --text "una frase"  # scans a literal string

Checks: banned vocabulary, em/en dashes, label-colon paragraph starts, filler phrases,
bold inside body paragraphs, presence of the AI note, and cover numbers spaced out.
Exit code 1 when it finds something.
"""
import argparse
import re
import sys

BANNED = [
    "fundamental", "clave", "crucial", "robusto", "óptimo", "idóneo", "garantizar",
    "cabe mencionar", "cabe destacar", "en definitiva", "en conclusión", "en resumen",
    "por otro lado", "asimismo", "adicionalmente", "no obstante", "a nivel de",
    "de cara a", "en base a", "se procede a", "resulta que", "sin duda", "ciertamente",
    "aprovechar al máximo", "potenciar", "sinergia", "ecosistema", "solución integral",
    "en el mundo actual", "es importante destacar", "en una frase",
]

LABEL_START = re.compile(
    r'(["\'](?:Políticas|Formación|Conclusión|Conclusión final|Resumen|Importante|'
    r'Objetivo|Análisis|Plan|Prevención|Recuperación|Interpretación|Nota final):\s)'
)

DASHES = ["\u2014", "\u2013"]
BOLD_BODY = re.compile(r"<b>")
AI_NOTE = "inteligencia artificial agéntica"


def scan(text, label="input"):
    problems = []
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        low = line.lower()
        for w in BANNED:
            if re.search(r"(?<![\wáéíóúüñ])" + re.escape(w) + r"(?![\wáéíóúüñ])", low):
                problems.append((i, "palabra prohibida: %r" % w, line.strip()[:90]))
        for d in DASHES:
            if d in line:
                problems.append((i, "raya prohibida", line.strip()[:90]))
        if LABEL_START.search(line):
            problems.append((i, "párrafo empieza con etiqueta y dos puntos",
                             line.strip()[:90]))
        if BOLD_BODY.search(line) and "Nota:" not in line:
            problems.append((i, "negrita en el cuerpo (solo se permite en 'Nota:')",
                             line.strip()[:90]))

    if AI_NOTE not in text:
        problems.append((0, "falta la nota de IA al final", ""))

    # cover sanity: characters spaced out by a leaked charSpace
    if re.search(r"1 ?0 ?\. ?1 ?1", text):
        problems.append((0, "posible fecha con interletrado (charSpace heredado)", ""))

    print("== %s: %d problema(s)" % (label, len(problems)))
    for ln, what, ctx in problems:
        if ln:
            print("  L%-4d %s\n        %s" % (ln, what, ctx))
        else:
            print("  %s" % what)
    return len(problems)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--text")
    a = ap.parse_args()

    if a.text:
        return 1 if scan(a.text, "--text") else 0
    if not a.path:
        print(__doc__)
        return 2
    with open(a.path, encoding="utf-8") as fh:
        return 1 if scan(fh.read(), a.path) else 0


if __name__ == "__main__":
    sys.exit(main())
