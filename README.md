# utad-actividades-pdf

Antigravity plugin bundling the `utad-actividades-pdf` skill and `pdfm-mcp` (Parallels Desktop MCP) for generating UTAD *Sistemas Operativos* and *Fundamentos de Hardware* activity PDFs with live VM screenshots.

## Contents

- `plugin.json`: Antigravity plugin manifest.
- `mcp_config.json`: Registers `pdfm-mcp` (`/Users/gefaass/.local/bin/pdfm-mcp`).
- `skills/utad-actividades-pdf/`: Skill instructions (`SKILL.md`), references, cover asset, and capture/QA scripts (`vm_capture.py`, `win_capture.py`, `crop_capture.py`, `check_doc.py`, `check_pdf.py`, `check_numbers.py`, `render_pages.py`, `detect_env.py`).

## Install

```bash
agy plugin install https://github.com/Unnidentified/utad-actividades-pdf
```

Or validate locally:

```bash
agy plugin validate --strict .
```
