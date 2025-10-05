#!/usr/bin/env bash
set -euo pipefail

if [[ $(id -u) -ne 0 ]]; then
    echo "Esegui questo script come root (es. sudo $0)" >&2
    exit 1
fi

echo "Aggiorno l'indice dei pacchetti..."
apt-get update -y

echo "Installo dipendenze Python (tkinter, ttkthemes)..."
apt-get install -y python3 python3-tk python3-ttkthemes

echo "Dipendenze installate."
