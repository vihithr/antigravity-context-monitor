#!/usr/bin/env python3
"""
Antigravity Context Monitor - Cross-Platform Python Installer
Usage:
    python install.py             # Install
    python install.py --uninstall # Uninstall
"""

import os
import sys
import shutil
import argparse
import urllib.request
import zipfile
import tempfile

PLUGIN_NAME = "context-monitor"
REPO_URL = "https://github.com/vihithr/antigravity-context-monitor/archive/refs/heads/main.zip"

def get_target_dir():
    home = os.path.expanduser("~")
    return os.path.join(home, ".gemini", "config", "plugins", PLUGIN_NAME)

def install():
    target = get_target_dir()
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"[*] Installing {PLUGIN_NAME}...")
    if os.path.exists(os.path.join(curr_dir, "plugin.json")):
        print(f"[*] Copying from local files at {curr_dir}")
        os.makedirs(target, exist_ok=True)
        for item in os.listdir(curr_dir):
            if item in (".git", ".gitignore", "__pycache__", "install.py"):
                continue
            s = os.path.join(curr_dir, item)
            d = os.path.join(target, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    else:
        print("[*] Downloading from GitHub...")
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "bundle.zip")
            urllib.request.urlretrieve(REPO_URL, zip_path)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)
            extracted = os.path.join(tmp_dir, "antigravity-context-monitor-main")
            os.makedirs(target, exist_ok=True)
            for item in os.listdir(extracted):
                s = os.path.join(extracted, item)
                d = os.path.join(target, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

    print(f"[+] Successfully installed to: {target}")
    print("[i] Restart Antigravity or Antigravity IDE to activate.")

def uninstall():
    target = get_target_dir()
    if os.path.exists(target):
        shutil.rmtree(target)
        print(f"[+] Successfully removed {PLUGIN_NAME} from: {target}")
        print("[i] Restart Antigravity to finalize.")
    else:
        print(f"[i] Plugin is not installed at {target}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Context Monitor Installer")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall plugin")
    args = parser.parse_args()
    if args.uninstall:
        uninstall()
    else:
        install()
