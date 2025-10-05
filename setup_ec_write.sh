#!/usr/bin/env bash
set -euo pipefail

MODULE_PARAM="/sys/module/ec_sys/parameters/write_support"
SERVICE_NAME="ec-sys-write-support.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"

if [[ $(id -u) -ne 0 ]]; then
    echo "Questo script deve essere eseguito come root (usa: sudo $0)" >&2
    exit 1
fi

if [[ ! -e "${MODULE_PARAM}" ]]; then
    echo "Parametro write_support non trovato in ${MODULE_PARAM}." >&2
    echo "Controlla che il kernel esponga ec_sys." >&2
    exit 1
fi

# Abilita subito il supporto in scrittura
if ! printf 'Y' > "${MODULE_PARAM}"; then
    echo "Impossibile impostare write_support a Y (serve kernel con opzione enable)." >&2
    exit 1
fi

echo "write_support abilitato immediatamente."

# Crea/aggiorna il servizio systemd
cat <<'UNIT' > "${SERVICE_PATH}"
[Unit]
Description=Enable EC write support for ec_sys
After=systemd-modules-load.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'printf Y > /sys/module/ec_sys/parameters/write_support'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT

chmod 0644 "${SERVICE_PATH}"

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

echo "Servizio ${SERVICE_NAME} installato e attivato."
cat "${MODULE_PARAM}"
