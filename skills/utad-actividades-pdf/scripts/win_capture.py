#!/usr/bin/env python3
"""Capture the full HiDPI desktop of a running Parallels Windows VM cleanly.

Uses in-guest GDI CopyFromScreen (with SetProcessDPIAware) instead of
`prlctl capture`, avoiding Parallels Metal/DWM partial-black scanline bugs
and display-sleep black frames.

Usage:
    python3 win_capture.py "Windows 11" fig/raw_fig2.png
"""
import base64
import subprocess
import sys

PS_CAPTURE = r"""
$d = Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); [DllImport("user32.dll")] public static extern int GetSystemMetrics(int n);' -Name D -PassThru
$d::SetProcessDPIAware() | Out-Null
$w = $d::GetSystemMetrics(0)
$h = $d::GetSystemMetrics(1)
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen(0, 0, 0, 0, [System.Drawing.Size]::new($w, $h))
$ms = New-Object System.IO.MemoryStream
$bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
[Convert]::ToBase64String($ms.ToArray())
""".strip()


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: win_capture.py <vm-name-or-uuid> <out.png>")
    vm, out_path = sys.argv[1], sys.argv[2]
    b64_cmd = base64.b64encode(PS_CAPTURE.encode("utf-16le")).decode()
    res = subprocess.run(
        [
            "prlctl", "exec", vm, "--current-user",
            "powershell", "-NoProfile", "-WindowStyle", "Hidden",
            "-EncodedCommand", b64_cmd,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if res.returncode != 0:
        sys.stderr.write(res.stderr or res.stdout)
        sys.exit(res.returncode)
    raw = "".join(res.stdout.split())
    png = base64.b64decode(raw)
    if not png.startswith(b"\x89PNG"):
        sys.stderr.write("win_capture.py: unexpected output (not PNG)\n")
        sys.exit(1)
    with open(out_path, "wb") as fh:
        fh.write(png)
    print("Captured %s (%d bytes)" % (out_path, len(png)))


if __name__ == "__main__":
    main()
