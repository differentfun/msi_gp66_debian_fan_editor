#!/usr/bin/env bash
set -euo pipefail

if [[ $(id -u) -ne 0 ]]; then
    echo "Esegui questo script come root (es. sudo $0)" >&2
    exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "${SCRIPT_DIR}"

INSTALL_DIR="/opt/gp66-fancontrol"
CONFIG_DIR="/etc/gp66-fancontrol"
SERVICE_FILE="/etc/systemd/system/gp66-fancontrol.service"
WRAPPER_FILE="/usr/local/bin/gp66-fancontrol-gui"
DESKTOP_FILE="/usr/share/applications/gp66-fancontrol.desktop"
POLKIT_FILE="/usr/share/polkit-1/actions/com.gp66.fancontrol.gui.policy"

install -d -m 0755 "${INSTALL_DIR}"
install -m 0644 "${SCRIPT_DIR}/controller.py" "${INSTALL_DIR}/controller.py"
install -m 0644 "${SCRIPT_DIR}/fan_profile.py" "${INSTALL_DIR}/fan_profile.py"
install -m 0755 "${SCRIPT_DIR}/fan_gui.py" "${INSTALL_DIR}/fan_gui.py"
install -m 0755 "${SCRIPT_DIR}/apply_fan_profile.py" "${INSTALL_DIR}/apply_fan_profile.py"

install -d -m 0755 "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_DIR}/config.json" ]]; then
python3 - <<'PY'
import fan_profile
fan_profile.save_profile(fan_profile.DEFAULT_PROFILE)
PY
fi

cat <<'UNIT' > "${SERVICE_FILE}"
[Unit]
Description=Apply GP66 fan profile on boot
After=multi-user.target
ConditionPathExists=/etc/gp66-fancontrol/config.json

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/gp66-fancontrol/apply_fan_profile.py
WorkingDirectory=/opt/gp66-fancontrol
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT

chmod 0644 "${SERVICE_FILE}"

install -d -m 0755 "$(dirname "${WRAPPER_FILE}")"
cat <<'WRAP' > "${WRAPPER_FILE}"
#!/usr/bin/env bash
set -euo pipefail
exec pkexec env \
    DISPLAY=$DISPLAY \
    WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-} \
    XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority} \
    XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-} \
    DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-} \
    /usr/bin/python3 /opt/gp66-fancontrol/fan_gui.py "$@"
WRAP
chmod 0755 "${WRAPPER_FILE}"

cat <<'POLICY' > "${POLKIT_FILE}"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN" "http://www.freedesktop.org/software/polkit/policyconfig-1.dtd">
<policyconfig>
  <action id="com.gp66.fancontrol.gui">
    <description>Esegui la GUI GP66 Fan Control</description>
    <message>Serve autenticazione per modificare la curva delle ventole GP66</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/bin/python3</annotate>
    <annotate key="org.freedesktop.policykit.exec.argv0">python3</annotate>
    <annotate key="org.freedesktop.policykit.exec.argv1">/opt/gp66-fancontrol/fan_gui.py</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>
</policyconfig>
POLICY
chmod 0644 "${POLKIT_FILE}"

cat <<'DESKTOP' > "${DESKTOP_FILE}"
[Desktop Entry]
Name=GP66 Fan Control
Comment=Configura le curve delle ventole per MSI GP66
Exec=/usr/local/bin/gp66-fancontrol-gui
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=Settings;Utility;
StartupNotify=false
DESKTOP
chmod 0644 "${DESKTOP_FILE}"

systemctl daemon-reload
systemctl enable --now gp66-fancontrol.service

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database >/dev/null 2>&1 || true
fi

echo "Installazione completata."
echo "Trovi la GUI nel menu come 'GP66 Fan Control' oppure esegui: gp66-fancontrol-gui"
