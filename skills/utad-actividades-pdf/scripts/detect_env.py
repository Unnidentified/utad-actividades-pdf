#!/usr/bin/env python3
"""Print what this environment can do for a UTAD activity document.

Usage: python3 detect_env.py
Exit code is always 0; read the report.
"""
import json
import os
import shutil
import subprocess
import sys


def which(*names):
    return [n for n in names if shutil.which(n)]


def py_mods():
    out = {}
    for m in ("reportlab", "PIL", "fitz", "docx", "pptx", "yaml"):
        try:
            __import__(m)
            out[m] = True
        except Exception:
            out[m] = False
    return out


def vms():
    report = {}
    if shutil.which("prlctl"):
        try:
            r = subprocess.run(["prlctl", "list", "-a"], capture_output=True, text=True, timeout=20)
            lines = [l.strip() for l in r.stdout.splitlines() if "{" in l]
            report["parallels"] = lines[:10]
            report["parallels_header"] = r.stdout.splitlines()[:1]
        except Exception as e:
            report["parallels"] = "error: %r" % e
    for cli, args in (("vmrun", ["list"]), ("VBoxManage", ["list", "vms"]),
                      ("multipass", ["list"]), ("incus", ["list"])):
        if shutil.which(cli):
            try:
                r = subprocess.run([cli] + args, capture_output=True, text=True, timeout=20)
                report[cli] = (r.stdout or r.stderr).strip().splitlines()[:6]
            except Exception as e:
                report[cli] = "error: %r" % e
    return report


def main():
    print("== python ==")
    print(sys.version.split()[0], sys.executable)
    print(json.dumps(py_mods(), indent=2))

    print("== build and QA tools ==")
    print("pandoc:", which("pandoc"))
    print("libreoffice/soffice:", which("libreoffice", "soffice"))
    print("wkhtmltopdf/weasyprint:", which("wkhtmltopdf", "weasyprint"))
    print("pdf->png:", which("pdftoppm", "qlmanage", "sips", "gs"))
    print("image tooling:", which("sips", "magick", "convert"))
    print("chrome:", which("google-chrome", "chromium") or
          ("/Applications/Google Chrome.app" if os.path.exists(
              "/Applications/Google Chrome.app") else []))

    print("== virtual machines ==")
    v = vms()
    print(json.dumps(v, indent=2, ensure_ascii=False) if v else "no hypervisor CLI found")

    print("== verdict ==")
    mods = py_mods()
    if mods.get("reportlab") and mods.get("PIL"):
        print("build: reportlab (preferred)")
    elif shutil.which("wkhtmltopdf") or os.path.exists("/Applications/Google Chrome.app"):
        print("build: HTML -> PDF")
    elif which("libreoffice", "soffice"):
        print("build: HTML/DOCX -> LibreOffice")
    else:
        print("build: hand-rolled PDF or Markdown to the user")

    if v.get("parallels") and isinstance(v["parallels"], list) and v["parallels"]:
        print("evidence: live VM captures available")
    elif any(k for k in v if k != "parallels_raw"):
        print("evidence: hypervisor present, adapt the commands")
    else:
        print("evidence: none here, use user captures or placeholders")

    if mods.get("fitz") or which("pdftoppm", "qlmanage", "sips", "gs"):
        print("QA: can render pages to PNG")
    else:
        print("QA: open the PDF manually before delivering")


if __name__ == "__main__":
    main()
