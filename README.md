# MSI GP66 Fan Curve Editor (Debian/Ubuntu)

A small Python tool to edit and apply custom fan curves on MSI GP66 laptops by writing directly to the embedded controller (EC) via Linux debugfs. It includes a simple Tk GUI and a boot-time service to apply the saved curve automatically.

Warning: This writes to the EC. You can damage hardware, void warranties, or cause instability. Use at your own risk and only if you understand the implications. Root privileges are required to apply settings.


## Features

- Tkinter GUI to set CPU/GPU fan curves at fixed temperature thresholds (40–100 °C).
- Live readout of CPU/GPU temperatures and fan RPM (updates every 2s).
- Saves configuration to `/etc/gp66-fancontrol/config.json`.
- Systemd unit applies the saved profile at boot.
- CLI helper to apply the profile on demand.


## Requirements

- Hardware: MSI GP66 series (other MSI models may not work; addresses are hardcoded).
- OS: Debian/Ubuntu (or derivatives).
- Kernel access: `debugfs` mounted and the `ec_sys` module with write support enabled.
- Root privileges to write to EC and to save `/etc/gp66-fancontrol/config.json`.
- Python 3 with Tkinter.

The tool talks to the EC via `/sys/kernel/debug/ec/ec0/io`. If this path does not exist, ensure debugfs is mounted and `ec_sys` is available with write support enabled (see below).


## Quick Start (from source)

1) Install dependencies (as root):

```bash
sudo ./install_dependencies.sh
```

2) Enable EC write support (as root):

```bash
sudo ./setup_ec_write.sh
```

3) Run the GUI (as root):

```bash
sudo python3 fan_gui.py
```

- Move the CPU/GPU sliders to set the PWM value used at each temperature threshold.
- Click “Apply & Save” to write to the EC immediately and persist to `/etc/gp66-fancontrol/config.json`.
- You can also click “Save only” or “Reset defaults”.

To apply the last saved profile without opening the GUI:

```bash
sudo python3 apply_fan_profile.py
```


## System-wide Install (recommended)

This sets up a systemd unit to apply your profile at boot and a launcher that runs the GUI via `pkexec`.

```bash
sudo ./install_fancurve.sh
```

What it installs:

- App files under: `/opt/gp66-fancontrol/`
- Config directory: `/etc/gp66-fancontrol/`
- Systemd service: `gp66-fancontrol.service` (enabled immediately)
- GUI launcher: `/usr/local/bin/gp66-fancontrol-gui` (runs GUI with `pkexec`)
- Desktop entry: `GP66 Fan Control` in your applications menu
- Polkit policy: allows authenticated admin to start the GUI

After installing, launch the GUI from your menu (search: “GP66 Fan Control”) or run:

```bash
gp66-fancontrol-gui
```

Check boot-apply status:

```bash
systemctl status gp66-fancontrol.service
```


## How It Works

- The GUI produces a 15-byte “VR” table: one flag + 7 CPU values + 7 GPU values.
- The tool writes these bytes to the EC via `/sys/kernel/debug/ec/ec0/io` in an “Advanced” mode.
- Temperature thresholds are fixed at: 40, 50, 60, 70, 80, 90, 100 °C.
- Each slider sets the PWM used when the temperature is at or above its threshold.

Files of interest:

- `fan_gui.py`: Tkinter GUI to edit/apply the curve and view stats.
- `fan_profile.py`: Loads/saves `/etc/gp66-fancontrol/config.json` and converts it to EC VR values.
- `controller.py`: Low-level EC read/write and mode handling.
- `apply_fan_profile.py`: Applies the saved profile without opening the GUI.


## Configuration

- Location: `/etc/gp66-fancontrol/config.json`
- Created automatically on first run or install.

Example:

```json
{
  "flag": 13,
  "cpu": [45, 50, 60, 72, 80, 85, 100],
  "gpu": [0, 50, 60, 72, 80, 85, 100]
}
```

Notes:

- `flag` is a raw byte (0–255). If unsure, keep `13`.
- `cpu` and `gpu` each contain exactly 7 integers. The code accepts 0–255, but values in the 0–100 range are typically meaningful as a “percent-like” PWM on these machines.
- The GUI enforces the correct shape and will normalize values on save.


## EC Write Support

This project requires write access to the EC via debugfs. On many Debian-based distros you must:

- Ensure `debugfs` is mounted (usually `/sys/kernel/debug`).
- Load `ec_sys` with write support enabled. The helper script does this and installs a oneshot systemd unit so it persists across reboots:

```bash
sudo ./setup_ec_write.sh
```

Troubleshooting this step:

- If `/sys/kernel/debug/ec/ec0/io` is missing, verify: `ls /sys/kernel/debug/ec/`.
- If `write_support` cannot be set, your kernel may lack that option; you may need a kernel that exposes `ec_sys.write_support=Y`.


## Troubleshooting

- Permission denied when saving/applying: run the GUI with `gp66-fancontrol-gui` (polkit prompt) or as root (`sudo python3 fan_gui.py`).
- “Error reading EC”: ensure EC write support is enabled and the path `/sys/kernel/debug/ec/ec0/io` exists, and that you’re running as root.
- No effect on fans: only tested on MSI GP66; other models may not share the same EC layout.
- Wayland/X authentication issues: the launcher exports common display env vars; if the GUI fails to start via `pkexec`, try running it with `sudo` for diagnosis.


## Uninstall

Disable the boot service and remove installed files:

```bash
sudo systemctl disable --now gp66-fancontrol.service
sudo rm -rf /opt/gp66-fancontrol /etc/gp66-fancontrol \
    /etc/systemd/system/gp66-fancontrol.service \
    /usr/local/bin/gp66-fancontrol-gui \
    /usr/share/polkit-1/actions/com.gp66.fancontrol.gui.policy \
    /usr/share/applications/gp66-fancontrol.desktop
sudo systemctl daemon-reload
```

If you used `setup_ec_write.sh` and want to undo it, also:

```bash
sudo systemctl disable --now ec-sys-write-support.service
sudo rm -f /etc/systemd/system/ec-sys-write-support.service
sudo systemctl daemon-reload
```


## Safety Notice

- Fan curves that are too low can overheat your system. Watch temperatures and ensure adequate cooling for your workload.
- The EC interface is undocumented and model-specific. Incorrect writes can cause unexpected behavior.
- You are responsible for any damage resulting from using this tool.


## License

MIT — see `LICENSE.md`.

