#!/usr/bin/env bash
set -e
echo "=== Antigravity Context Monitor Uninstaller ==="
TARGET_DIR="${HOME}/.gemini/config/plugins/context-monitor"
if [ -d "${TARGET_DIR}" ]; then
    rm -rf "${TARGET_DIR}"
    echo "[+] Successfully uninstalled context-monitor."
    echo "[i] Restart Antigravity to finalize."
else
    echo "[i] Plugin is not installed at ${TARGET_DIR}."
fi
