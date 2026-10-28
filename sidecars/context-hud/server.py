#!/usr/bin/env python3
"""
Antigravity Context HUD Sidecar Web Server.
Serves real-time context length and compaction status API and Web UI.
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add plugins scripts dir to sys.path
sidecar_dir = os.path.dirname(os.path.abspath(__file__))
plugin_dir = os.path.dirname(os.path.dirname(sidecar_dir))
scripts_dir = os.path.join(plugin_dir, "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

import monitor

PORT = int(os.environ.get("ANTIGRAVITY_SIDECAR_WEB_PORT", os.environ.get("PORT", 59388)))
WEB_DIR = os.path.join(sidecar_dir, "web")

class ContextHudHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/status"):
            try:
                data = monitor.analyze_context()
                # Auto-sync active conversation artifact on status poll
                conv_id = data.get("conversation_id")
                if conv_id:
                    home = os.path.expanduser("~")
                    art_dir = os.path.join(home, ".gemini", "antigravity", "brain", conv_id)
                    monitor.sync_dynamic_artifact(art_dir, data)

                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err_body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
            return

        if self.path.startswith("/api/sync-current"):
            try:
                data = monitor.analyze_context()
                conv_id = data.get("conversation_id")
                target_file = None
                if conv_id:
                    home = os.path.expanduser("~")
                    art_dir = os.path.join(home, ".gemini", "antigravity", "brain", conv_id)
                    target_file = monitor.sync_dynamic_artifact(art_dir, data)
                res = {
                    "ok": True,
                    "conversation_id": conv_id,
                    "artifact": os.path.basename(target_file) if target_file else None,
                    "tokens": data.get("current_context_tokens", 0),
                    "max_tokens": data.get("max_context_tokens", 0)
                }
                body = json.dumps(res, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err_body = json.dumps({"ok": False, "error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
            return

        if self.path.startswith("/api/sync-all"):
            try:
                count, synced = monitor.sync_all_conversations()
                res = {"ok": True, "count": count, "synced": synced}
                body = json.dumps(res, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                err_body = json.dumps({"ok": False, "error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
            return

        # Serve static HTML
        file_path = os.path.join(WEB_DIR, "index.html")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silent logs to avoid polluting stdout
        pass

def run():
    server = HTTPServer(("127.0.0.1", PORT), ContextHudHandler)
    print(f"Context HUD Sidecar running on http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run()
