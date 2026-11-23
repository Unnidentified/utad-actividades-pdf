# Capture playbook

The evidence is the part that cannot be faked. Everything here is about getting a frame that
shows **the command and its output, legible**, on the machine the statement asks for.

## The one rule

A capture is valid when a reader who does not know the activity can read the command, read the
output, and see that the output belongs to that command. If any of the three fails, recapture.

## Order of preference

1. **MCP Parallels server** (`pdfm-mcp`) if exposed: `parallels_vm_exec`,
   `parallels_vm_capture`, `parallels_vm_snapshot_create`. It handles argv properly and returns
   the image as base64. Note: if `pdfm-mcp` is listed as **Lazy** in `<mcp_servers>`, read
   the tool schemas under `<appDataDir>/mcp/.../parallels_vm_*.json` and invoke via
   `call_mcp_tool` — or go straight to `prlctl` if `detect_env.py` already shows it.
2. **`prlctl` directly**: `prlctl exec`, `prlctl capture --file`, `prlctl snapshot`.
3. **Any hypervisor CLI** (`vmrun`, `VBoxManage`, `virsh screenshot`, `incus exec`, `multipass`).
4. **A real terminal on the host / WSL / a container**, if the statement allows it.
5. **The user's own screenshots**, if there is no machine at all. Then the document ships with
   `[[CAPTURA: …]]` placeholders on purpose.

## Linux guest: the scripted-window trick

Typing into a guest terminal through the hypervisor is unreliable (focus, Wayland, UAC, secure
desktop). Do not build a workflow on it. Instead write a small script inside the guest and open
a terminal that runs it.

Important: plain `prlctl exec "$VM"` runs as **root**, and even `--current-user` starts with
an empty `DISPLAY` / `WAYLAND_DISPLAY` unless you pass them explicitly. Always combine
`--current-user` with `env DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0`:

```bash
# 1. write the script inside the guest (one command per line; stop xtrace before sleep)
prlctl exec "$VM" bash -c 'cat > /home/parallels/s1.sh << "EOF"
export PS4="$ "
set -x
ip -4 a
ip route
ping -c 2 10.211.55.1
{ set +x; } 2>/dev/null
sleep 900
EOF
chown parallels:parallels /home/parallels/s1.sh && chmod 644 /home/parallels/s1.sh'

# 2. open a visible window on the active Wayland/X11 session (never su/nohup)
prlctl exec "$VM" --current-user env DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
  gnome-terminal --geometry=100x26 -- bash /home/parallels/s1.sh

# 3. capture and crop with automatic black-frame / missing-window retry
sleep 4 && python3 scripts/vm_capture.py "$VM" fig/raw_fig1.png fig/fig1.png
```

Why `PS4='$ '` + `set -x`: the trace prints each command as `$ ip route` immediately before
its output, so the frame looks like a normal session and is honest — it *is* the real output.
Put one command per line rather than `cmd1 && cmd2` so each command gets its own `$ ` line.
For piped commands (e.g. `top -b -n 2 -d 1 | awk ... | head -n 14`), `set -x` only prints the
last stage (`$ head -n 14`), so print the pipeline manually before running it:
`{ set +x; } 2>/dev/null; echo '$ top -b -n 2 -d 1 | awk ... | head -n 14'; top ... | head -n 14`
(`{ set +x; } 2>/dev/null` stops tracing cleanly before `sleep 900`.)

Notes:

- **Guard `prlctl exec` against hangs, semicolon splitting, and collisions (macOS has no `timeout(1)`):** wrap uncertain or initial probes with `perl -e 'alarm 10; exec @ARGV' prlctl exec ...`, pass multi-command Linux checks via `prlctl exec "$VM" bash << 'EOF'` instead of `bash -c "a; b"` (Parallels can split semicolons and run truncated commands like bare `id` as `root`), and avoid overlapping `prlctl exec` calls at the same VM (never append `&` after `gnome-terminal` — it already returns via IPC).
- **Ubuntu 24.04/26.04 SSH and config-file hygiene:** `openssh-server` uses systemd socket activation, so stopping SSH requires `systemctl disable --now ssh.socket ssh.service` (not just `ssh.service`). When updating `/etc/security/pwquality.conf` or `login.defs`, edit/comment existing keys in place instead of appending duplicate keys.
- **Use `sudo` inside Linux capture scripts for root-only commands (`cat /etc/netplan/*.yaml`, `resolvectl flush-caches`, `resolvectl statistics`):** running them unprivileged inside `gnome-terminal` pops up a GNOME Polkit password modal that blocks screenshots even after `pkill` or `Escape`. Verify passwordless sudo first (`prlctl exec "$VM" sudo -n true`).
- **Bound network timeouts and wait on a sentinel file for slow/failing commands:** an un-timeouted `ping` on broken DNS waits ~12 s before printing the error, beating a fixed `sleep 3`. Use `ping -c 1 -W 2`, `dig +time=2 +tries=1`, and `curl --max-time 3`, touch `/home/parallels/.cap_done` right before `sleep 900`, and poll `until prlctl exec "$VM" test -f /home/parallels/.cap_done; do sleep 1; done` before running `vm_capture.py`.
- **Ubuntu Netplan + `systemd-networkd` vs `NetworkManager` DNS override:** inspect `ls -la /etc/netplan/` first because Netplan merges every `.yaml` file (a leftover `00-installer-config.yaml` with `enp0s5` or DHCP can override or warn). If `resolvectl status eth0` keeps showing DHCP DNS (`10.211.55.1`) after updating `01-netcfg.yaml`, stop `systemd-networkd` / pick one renderer and clear stale leases using `prlctl exec "$VM" bash << 'EOF'` (heredoc avoids host-shell glob issues such as `rm: missing operand`) before `netplan apply`.
- **After starting or rebooting a VM**, wait until both Parallels Tools and desktop auto-login
  are ready before running `gsettings` or `gnome-terminal`:
  `until prlctl exec "$VM" --current-user whoami >/dev/null 2>&1; do sleep 2; done`
- **Background stress/daemon processes inside Linux VMs:** `prlctl exec` kills `nohup` and
  `setsid` children when it exits. Use `systemd-run --unit=cpu-hog bash -c 'exec yes >/dev/null 2>&1'`
  (redirect inside single quotes so `journald`/`rsyslogd` do not eat 100% CPU logging stdout),
  and stop later with `prlctl exec "$VM" systemctl stop cpu-hog`.
- Adjust `/home/parallels/` if the VM's desktop user is not `parallels` (check `prlctl exec "$VM" --current-user whoami`). Never put the script in `/tmp` (a reboot wipes `/tmp` and the window opens and closes instantly).
- `--geometry=100x26` gives a compact window whose text is big relative to the image. A
  maximised window on a 1568 px screen produces 10 pt text that becomes 3 pt once placed in the
  PDF. **Prefer a smaller window over a bigger capture.**
- Use `prlctl exec "$VM" pkill -u parallels -f '/home/parallels/s[1].sh' || true` (root with bracketed `[1]` pattern avoids matching `pkill` itself or hitting `Operation not permitted`) before launching a new figure; do not kill `gnome-terminal-server` (it can leave the session unable to open windows until reboot).
- Disable idle blanking + enable centered windows once per session:
  `prlctl exec "$VM" --current-user env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus gsettings set org.gnome.desktop.session idle-delay 0`,
  `... gsettings set org.gnome.desktop.screensaver lock-enabled false`, and
  `... gsettings set org.gnome.mutter center-new-windows true`.
- Multiple windows stack. Reuse one window per figure, and close the previous script before
  opening the next, or the capture shows the wrong window in front.

## Windows guest

- `prlctl exec --current-user` lands in the interactive session; plain `prlctl exec` runs in
  session 0 and **nothing you start will be visible**. Always use `--current-user` for anything
  on screen, and pass `-WindowStyle Hidden` on the outer launcher so `prl_tools_service.exe`
  does not flash a second console window over your target window.
- **Always use `scripts/vm_capture.py` (which delegates Windows VMs to `scripts/win_capture.py`)
  instead of `prlctl capture`:** on ARM64 Macs, `prlctl capture` frequently returns solid-black
  frames or partial black bottom scanlines when the VM window is not focused. `vm_capture.py`
  uses in-guest HiDPI `CopyFromScreen`, validates the terminal crop, and retries if needed:
  ```bash
  W_ENC=$(python3 -c 'import base64; print(base64.b64encode("[IO.File]::WriteAllText((Join-Path $env:USERPROFILE \"s2.ps1\"), [Console]::In.ReadToEnd())".encode("utf-16le")).decode())')
  cat << 'PS1' | prlctl exec "$VM" --current-user powershell -NoProfile -WindowStyle Hidden -EncodedCommand "$W_ENC"
  Clear-Host
  Write-Output "PS C:\> hostname"
  hostname
  Write-Output "PS C:\> whoami"
  whoami
  PS1
  L_ENC=$(python3 -c 'import base64; print(base64.b64encode("Remove-Item -Path \"HKCU:\\Console\\%SystemRoot%_System32_WindowsPowerShell_v1.0_powershell.exe\" -Force -ErrorAction SilentlyContinue; Start-Process powershell -ArgumentList \"-NoLogo\",\"-NoExit\",\"-ExecutionPolicy\",\"Bypass\",\"-File\",(Join-Path $env:USERPROFILE \"s2.ps1\")".encode("utf-16le")).decode())')
  prlctl exec "$VM" --current-user powershell -NoProfile -WindowStyle Hidden -EncodedCommand "$L_ENC"
  sleep 3 && python3 scripts/vm_capture.py "$VM" fig/raw_fig2.png fig/fig2.png
  ```
- **Never double-encode big `.ps1` payloads inside `-EncodedCommand`:** base64-in-base64 inflates scripts ~3.55x and exceeds Parallels `PrlVmGuest_RunProgram` length limits. Streaming the `.ps1` file over stdin (`$W_ENC` is always ~244 chars) handles scripts of any length in one command without chunked `cmd /c echo` loops.
- **Never pass nested quotes or `$variables` through inline `powershell -Command '...'`:** `prlctl exec` strips inner double quotes (turning `"Ethernet"` into bareword `Ethernet`). Always use stdin + `-EncodedCommand` (`utf-16le`).
- **Keep Windows capture output ordered and clean:** avoid piping native executables (`ping`, `nslookup`) into `Select-String` when display order matters (PowerShell buffering can print `nslookup` before `ping`); use `ping -n 1 -w 1500` directly and pass `-ErrorAction SilentlyContinue` to `Get-DnsClientCache` (which errors after `ipconfig /flushdns` when empty).
- Never run `Stop-Process -Name powershell` unfiltered (it kills its own session); use
  `prlctl exec "$VM" cmd /c "taskkill /IM powershell.exe /F 2>nul & exit /b 0"` (without `--current-user` so elevated windows do not return `ERROR: Access is denied`). When creating scheduled tasks with `schtasks` / `Register-ScheduledTask` that a regular user capture will inspect, set `/RU` or match privilege context so querying them does not hit `Access is denied`.
- Writing to `C:\Windows\System32\drivers\etc\hosts`, changing IPs or firewall rules needs
  elevation. With UAC prompts disabled an elevated child works silently; with prompts enabled
  the capture of the consent dialog is black (secure desktop), so press *Yes* with
  `send_key` left + enter and capture afterwards. A scheduled task with `/RL HIGHEST` is the
  other route.
- A console window keeps its own history; closing it (`Stop-Process -Name powershell`) is enough.

## Reading a capture before you write about it

Zoom the region that carries the numbers (`sips -Z 1600` on a copy, or crop it) and read the
values one by one. Do not reconstruct them from what a command is supposed to do. The failure
this prevents is real: a sentence claiming a column stayed at 45.872 «en las tres medidas» when
the capture showed 45.772 in the middle, written by an agent that said it had checked.

## Cropping

- Crop to the terminal window, not to the desktop, and trim empty rows below the last output
  line. Use `--window` so `crop_capture.py` finds the foreground terminal window automatically
  (works on both dark and light terminals) in one command without writing ad-hoc box scripts:
  ```bash
  python3 scripts/crop_capture.py fig/raw_fig1.png fig/fig1.png --window --pad 18
  ```
- Keep the window title bar only if it shows something useful (the VM name or the user). If the
  desktop wallpaper or the dock is in frame, it is not cropped enough.
- Do not upscale. If text is small, recapture with a smaller window.
- Save as PNG in a `fig/` folder next to the build script, named `fig1.png`, `fig2.png`, … and
  keep the raw capture too (`raw_fig1.png`), because recrops are common.

## Verification before you trust a capture

After doing an action, verify the state with an independent command before capturing:

- changed `/etc/hosts` → `getent hosts google.com` and `cat /etc/hosts`
- static IP → `ip -4 -o a` and `ip route`
- removed a user → `id usuario` must say *no such user*
- killed a process → `pgrep` returns nothing

If the verification and the capture disagree, the capture is of an older state. Redo.

## No tools at all (web chat)

Do not fake screenshots and do not describe them in past tense. Produce the document with
placeholders and give the reader a numbered list:

```
[[CAPTURA 1 — terminal 1, ventana maximizada]]
Comandos: ip -4 a ; ip route ; ping -c 2 <puerta>
Qué tiene que verse: la IP con su máscara, la línea "default via" y "0 % packet loss".
```

Plus a two-line instruction in the chat: “ejecuta esto en la VM, haz una captura donde se vea
el comando y la salida, y pégala donde dice CAPTURA 1”. That is the graceful degradation, and
it is honest.

## Snapshots

When the statement asks for one (`Haz una instantánea UD2_RED_OK`), create it **after** the
verification passes and mention the name in the last paragraph. Use the VM manager's snapshot
command; never a filesystem copy.
