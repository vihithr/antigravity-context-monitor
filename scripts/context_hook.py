#!/usr/bin/env python3
"""
Antigravity PreInvocation Hook for Context Monitoring & Compaction Alert.
Receives hook payload via stdin and injects ephemeral context warnings when approaching the compaction line.
"""

import os
import sys
import json

# Ensure monitor module can be imported from same directory
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import monitor

def sync_dynamic_artifact(artifact_dir, data):
    return monitor.sync_dynamic_artifact(artifact_dir, data)

def load_config():
    """Load optional user-defined configuration for thresholds and behavior."""
    plugin_dir = os.path.dirname(script_dir)
    config_file = os.path.join(plugin_dir, "context_monitor_config.json")
    default_config = {
        "always_report": False,
        "warning_threshold": 0.75,
        "compaction_threshold": 0.80,
        "critical_threshold": 0.90
    }
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_config.update(cfg)
        except Exception:
            pass
    return default_config

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    # Read stdin payload from Antigravity lifecycle hook
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    transcript_path = payload.get("transcriptPath")
    conv_id = payload.get("conversationId")
    artifact_dir = payload.get("artifactDirectoryPath")
    model_name = payload.get("modelName")
    if model_name == "auto":
        model_name = None

    cfg = load_config()
    warn_thresh = cfg.get("warning_threshold", 0.75)
    comp_thresh = cfg.get("compaction_threshold", 0.80)
    always_report = cfg.get("always_report", False)

    data = monitor.analyze_context(
        transcript_path=transcript_path,
        conv_id=conv_id,
        override_model=model_name,
        warn_thresh=warn_thresh,
        comp_thresh=comp_thresh
    )

    inject_steps = []

    if "error" not in data:
        usage_ratio = data["usage_ratio"]
        cur = data["current_context_tokens"]
        bound_t = data.get("compaction_boundary_tokens", data["max_context_tokens"])
        pct = data["usage_percent"]
        model = data["resolved_model"]
        comp_tokens = data["compaction_line_tokens"]
        rem = data["remaining_to_compaction"]

        cur_k = f"{cur//1000}k" if cur >= 1000 else str(cur)
        bound_k = "256k" if bound_t in (262144, 256000) else (f"{bound_t//1000}k" if bound_t >= 1000 else str(bound_t))

        # Automatically generate / update the compact context pill HTML
        pill_html = monitor.generate_pill_html(data)
        saved_paths = []

        # 1. Save to session artifact directory if available
        if not artifact_dir and conv_id:
            home = os.path.expanduser("~")
            candidate = os.path.join(home, ".gemini", "antigravity", "brain", conv_id)
            if os.path.exists(candidate):
                artifact_dir = candidate

        if artifact_dir and os.path.exists(artifact_dir):
            # Sync dynamic context artifact named e.g. Context_[70k_256k].md
            sync_dynamic_artifact(artifact_dir, data)

        # 2. Save to plugin global web directory as universal fallback
        global_web_dir = os.path.join(os.path.dirname(script_dir), "web")
        os.makedirs(global_web_dir, exist_ok=True)
        global_pill_file = os.path.join(global_web_dir, "context_pill.html")
        try:
            with open(global_pill_file, "w", encoding="utf-8") as f:
                f.write(pill_html)
            saved_paths.append(global_pill_file)
        except Exception:
            pass

        pill_target_uri = (
            saved_paths[0].replace("\\", "/") if saved_paths else ""
        )

        if usage_ratio >= 0.90:
            msg = (
                f"🚨 [Context Monitor 紧急警报] 当前会话上下文已达 {cur:,} / {bound_t:,} tokens ({pct:.1f}%)，"
                f"严重逼近 {bound_k} 自动压缩硬限制！"
                f"请在回复中提示用户并建议立即执行 `/compact` 进行上下文总结与压缩。"
                f" (GUI Pill: file:///{pill_target_uri})"
            )
            inject_steps.append({"ephemeralMessage": msg})
        elif usage_ratio >= comp_thresh:
            msg = (
                f"⚠️ [Context Monitor 压缩线预警] 当前会话上下文已达 {cur:,} / {bound_t:,} tokens ({pct:.1f}%)，"
                f"已跨越 {bound_k} 边界的推荐压缩线 ({comp_tokens:,} tokens，阈值 {comp_thresh*100:.0f}%)。"
                f"建议提醒用户可以使用 `/compact` 命令压缩会话。"
                f" (GUI Pill: file:///{pill_target_uri})"
            )
            inject_steps.append({"ephemeralMessage": msg})
        elif usage_ratio >= warn_thresh:
            msg = (
                f"ℹ️ [Context Monitor 提示] 当前会话上下文: {cur:,} / {bound_t:,} tokens ({pct:.1f}%)，"
                f"正在接近 {bound_k} 压缩线 ({comp_tokens:,} tokens，还剩 {rem:,} tokens 空间)。"
                f" (GUI Pill: file:///{pill_target_uri})"
            )
            inject_steps.append({"ephemeralMessage": msg})
        elif always_report and cur > 0:
            comp_k = f"{comp_tokens//1000}k"
            msg = f"[Context Monitor] {cur_k}/{bound_k} (80%: {comp_k})"
            inject_steps.append({"ephemeralMessage": msg})

    output = {"injectSteps": inject_steps}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
