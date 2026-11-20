#!/usr/bin/env python3
"""Capture and crop a clean terminal screenshot from a Parallels VM with retries.

Automatically selects `win_capture.py` (in-guest HiDPI CopyFromScreen) for
Windows VMs and `prlctl send-key-event` + `prlctl capture` for Linux VMs, then
validates and crops via `crop_capture.py --window`. Retries automatically if
the frame is black, half-drawn, or missing a terminal window.

Usage:
    python3 vm_capture.py "Ubuntu 26.04 ARM64" fig/raw_fig1.png fig/fig1.png
    python3 vm_capture.py "Windows 11" fig/raw_fig2.png fig/fig2.png --attempts 4
"""
import argparse
import os
import subprocess
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def detect_os(vm):
    res = subprocess.run(["prlctl", "list", "-i", vm], capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if line.startswith("OS:"):
            val = line.split(":", 1)[1].strip().lower()
            return "windows" if val.startswith("win") else "linux"
    return "linux"


def capture_once(vm, raw_path, os_kind, wake=False):
    if os_kind == "windows":
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "win_capture.py"), vm, raw_path],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            sys.stderr.write(r.stderr or r.stdout)
            return False
        return True
    if wake:
        # Only send a wake key on retries after a black capture; sending it
        # unconditionally right before prlctl capture triggers partial redraws.
        for ev in ("press", "release"):
            subprocess.run(
                ["prlctl", "send-key-event", vm, "--scancode", "42", "--event", ev],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        time.sleep(2.5)
    r = subprocess.run(["prlctl", "capture", vm, "--file", raw_path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vm")
    ap.add_argument("raw_out")
    ap.add_argument("crop_out")
    ap.add_argument("--os", choices=("auto", "linux", "windows"), default="auto")
    ap.add_argument("--attempts", type=int, default=5)
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--pad", type=int, default=18)
    args = ap.parse_args()

    os_kind = detect_os(args.vm) if args.os == "auto" else args.os
    os.makedirs(os.path.dirname(os.path.abspath(args.raw_out)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.crop_out)), exist_ok=True)
    crop_py = os.path.join(SCRIPTS_DIR, "crop_capture.py")

    for attempt in range(1, args.attempts + 1):
        if capture_once(args.vm, args.raw_out, os_kind, wake=(attempt > 1)):
            r = subprocess.run(
                [sys.executable, crop_py, args.raw_out, args.crop_out, "--window", "--pad", str(args.pad)],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                sys.stdout.write(r.stdout)
                return 0
            sys.stderr.write("attempt %d/%d rejected: %s" % (attempt, args.attempts, r.stderr or r.stdout))
        if attempt < args.attempts:
            time.sleep(args.delay)

    sys.stderr.write("vm_capture.py: failed to get a clean %s capture after %d attempts\n"
                     % (os_kind, args.attempts))
    return 1


if __name__ == "__main__":
    sys.exit(main())
