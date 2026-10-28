#!/usr/bin/env bash
set -e
echo "=== Antigravity Context Monitor Installer ==="
TARGET_DIR="${HOME}/.gemini/config/plugins/context-monitor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" >/dev/null 2>&1 && pwd)"

if [ -f "${SCRIPT_DIR}/plugin.json" ]; then
    echo "[*] Installing from local repository: ${SCRIPT_DIR}"
    mkdir -p "${TARGET_DIR}"
    cp -R "${SCRIPT_DIR}"/* "${TARGET_DIR}/"
else
    echo "[*] Downloading latest release from GitHub..."
    TMP_ZIP="/tmp/antigravity-context-monitor.zip"
    TMP_EXTRACT="/tmp/antigravity-context-monitor-extract"
    curl -fsSL -o "${TMP_ZIP}" "https://github.com/vihithr/antigravity-context-monitor/archive/refs/heads/main.zip"
    rm -rf "${TMP_EXTRACT}"
    mkdir -p "${TMP_EXTRACT}"
    unzip -q "${TMP_ZIP}" -d "${TMP_EXTRACT}"
    mkdir -p "${TARGET_DIR}"
    cp -R "${TMP_EXTRACT}/antigravity-context-monitor-main"/* "${TARGET_DIR}/"
    rm -f "${TMP_ZIP}"
    rm -rf "${TMP_EXTRACT}"
fi

echo "[+] Successfully installed context-monitor to:"
echo "    ${TARGET_DIR}"
echo "[i] Restart Antigravity or Antigravity IDE to activate."
