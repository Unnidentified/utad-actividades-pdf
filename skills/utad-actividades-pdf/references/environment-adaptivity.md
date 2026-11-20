# Environment adaptivity

The artefact never changes: cover, plain Spanish, real evidence, same layout. What changes is
how the evidence is obtained and how the PDF is produced.

## 1. Detect before you promise anything

Run `scripts/detect_env.py`, or check by hand:

```sh
command -v prlctl vmrun VBoxManage multipass incus 2>/dev/null    # VM control
command -v python3 pandoc libreoffice soffice wkhtmltopdf weasyprint \
             pdftoppm qlmanage 2>/dev/null                        # build + QA tooling
python3 - <<'EOF'
for m in ("reportlab","PIL","fitz","docx","pptx"):
    try: __import__(m); print(m, "ok")
    except Exception: print(m, "missing")
EOF
prlctl list -a 2>/dev/null || true                                # VMs present and running
```

Also check for MCP tools in the client (Parallels server exposes `parallels_vm_capture`,
`parallels_vm_exec`, `parallels_vm_snapshot_create`); if they exist, use them over raw CLI.

## 2. The ladder

| Rung | Evidence | Build | QA |
| --- | --- | --- | --- |
| 5 — Mac + Parallels + Python libs | MCP/`prlctl` captures, cropped | reportlab, `references/pdf-builder-template.py` | `scripts/render_pages.py` + look at every page |
| 4 — any hypervisor + reportlab | same, different CLI | same | same |
| 3 — reportlab, no VM | host commands if the statement allows; otherwise user captures | same | same |
| 2 — no reportlab | user captures or host commands | HTML + headless Chrome / `wkhtmltopdf`; or ODT/DOCX + `soffice --convert-to pdf` | open the PDF and look |
| 1 — text only | user captures | Markdown/LaTeX/HTML handed to the user with instructions to print | none |
| 0 — web chat, no tools | placeholders + exact commands | Markdown or HTML in the answer | none |

Never jump up a rung: if the machine has no VM, do not write “he ejecutado en la VM”.

## 3. Fallbacks in detail

### PDF without reportlab

**HTML → PDF (preferred).** Write a single `doc.html` with print CSS that reproduces the
layout: A4, `@page { size: A4; margin: 22mm }`, Helvetica/Arial, 10 pt/14, justified, figures
`max-width:100%`, caption 8 pt italic `#333`, tables with `border-collapse:collapse` and 0.4 pt
`#999` borders, cover as a first page with the big title and the yellow block. Then:

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --print-to-pdf=out.pdf --no-pdf-header-footer file:///abs/path/doc.html
# or
wkhtmltopdf --enable-local-file-access doc.html out.pdf
```

**LibreOffice.** Same HTML, or a DOCX built with `python-docx`, then
`soffice --headless --convert-to pdf doc.docx`.

**LaTeX.** Only if a LaTeX toolchain exists; keep the same geometry (`geometry` 22 mm, Helvetica
through `helvet`, `\pagestyle{empty}`).

**No libraries at all.** A minimal PDF can be written by hand with a Type1 base font:

```python
# tiny, no dependencies, black text, A4, one long page is acceptable
lines = ["..."]  # 60 lines per page
def esc(s): return s.replace("\\","\\\\").replace("(","\\(").replace(")","\\)")
content = "BT /F1 10 Tf 14 TL 62 780 Td\n" + "\n".join(f"({esc(l)}) Tj T*" for l in lines) + "\nET"
objs = [
 "<</Type/Catalog/Pages 2 0 R>>",
 "<</Type/Pages/Kids[3 0 R]/Count 1>>",
 "<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>",
 f"<</Length {len(content)}>>\nstream\n{content}\nendstream",
 "<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>"]
```
Write the xref table correctly or the file will not open. This is the last resort: no images,
no tables, and the cover degrades to plain text. Prefer handing the user HTML and telling them
to print to PDF.

### Images without Pillow

- Cropping: `sips -c H W --cropOffset y x` (macOS) or `convert -crop` (ImageMagick).
- Measuring a PNG: `sips -g pixelWidth -g pixelHeight`.
- If nothing can crop, place the raw capture and reduce its width in the layout; legibility
  suffers, the document still ships.

### Rendering for QA without PyMuPDF

- macOS: `qlmanage -t -s 1600 -o outdir doc.pdf` (first page only) or
  `sips -s format png doc.pdf --out page.png`.
- Poppler: `pdftoppm -png -r 100 doc.pdf page`.
- Ghostscript: `gs -sDEVICE=png16m -r100 -o page-%d.png doc.pdf`.
- If none exist, open the PDF in whatever viewer the environment has and inspect page by page
  before delivering; do not skip the visual check.

### No VM but the statement demands one

Two acceptable paths:

1. Give the user the exact commands, in order, and a numbered list of captures to send back.
   Build the document with placeholders meanwhile; fill them when the images arrive.
2. If the tools exist on the host and the statement does not forbid it (a shell, permissions,
   `free`, `ip` all exist on Linux hosts), run it on the host and say so in one short line in
   the document: “Lo he hecho en mi equipo con Ubuntu, que para el caso es lo mismo.”

Never mix: if half the evidence is real and half is a placeholder, mark clearly which is which.

### No screenshots at all in the environment

Then the deliverable is the text: commands, expected outputs (quoted, and labelled as
expected), and the answers to the questions. The document keeps the same sections and the same
voice. State once, at the end, that the captures have to be pasted by hand and where.

## 4. Environment-specific gotchas

- **Parallels + `prlctl exec`**: `--current-user` for anything graphical on Windows; plain exec
  is session 0. On Linux, plain exec is root.
- **Shared folders**: in Windows they appear as `\\Mac\Home\...` and often as a drive `Z:`; in
  Linux guests usually `/media/psf/...`, but not always mounted. Verify with `ls` before
  relying on them; copying through `prlctl exec ... sh -c 'cat > file'` with stdin always works.
- **Wayland guests**: launching GUI apps needs `XDG_RUNTIME_DIR=/run/user/<uid>`,
  `WAYLAND_DISPLAY=wayland-0` and `DISPLAY=:0` together.
- **Web chat**: no file system. Deliver Markdown/HTML in the message, keep the cover as text,
  and never claim to have opened a PDF.
- **Windows without admin**: hosts, IPs and firewall need elevation; scheduled tasks or an
  elevated child process are the two routes.

## 5. Honesty rules

- A placeholder is always better than an invented capture or an invented number.
- If a step could not be completed, say it in one sentence in the document and say what was
  done instead.
- The AI note stays at the end regardless of the environment.
