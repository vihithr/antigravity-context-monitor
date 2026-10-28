#!/usr/bin/env python3
"""
Antigravity Context Monitor & Compaction Threshold Analyzer
Analyzes current conversation context length against model context window limits.
"""

import os
import sys
import json
import glob
import re
import argparse
import urllib.request
import urllib.error

# Built-in fallback limits for known models
MODEL_LIMITS_FALLBACK = {
    "gemini-3.8-flash-high": 1048576,
    "gemini-3.8-flash-medium": 1048576,
    "gemini-3.8-flash-low": 1048576,
    "gemini-3.8-flash-tiered": 1048576,
    "gemini-3.5-flash-lite": 1048576,
    "gemini-3.1-flash-lite": 1048576,
    "gemini-3-flash": 1048576,
    "gemini-2.5-pro": 1048576,
    "gemini-2.5-flash": 1048576,
    "gemini-2.5-flash-thinking": 1048576,
    "gemini-2.5-flash-lite": 1048576,
    "claude-sonnet-4-6": 250000,
    "claude-opus-4-6-thinking": 250000,
    "claude-3-7-sonnet": 200000,
    "claude-3-5-sonnet": 200000,
    "gpt-oss-120b-medium": 131072,
    "default": 1048576
}

def load_config():
    """Load user configuration for thresholds and boundaries."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_dir = os.path.dirname(script_dir)
    config_file = os.path.join(plugin_dir, "context_monitor_config.json")
    default_config = {
        "always_report": False,
        "compaction_boundary_tokens": 262144,
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

def get_ls_models():
    """Query Antigravity Language Server for live model specs."""
    ls_addr = os.environ.get("ANTIGRAVITY_LS_ADDRESS", "")
    csrf = os.environ.get("ANTIGRAVITY_CSRF_TOKEN", "")
    if not ls_addr:
        return {}

    url = f"http://{ls_addr}/exa.language_server_pb.LanguageServerService/GetAvailableModels"
    try:
        req = urllib.request.Request(
            url,
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "x-codeium-csrf-token": csrf
            }
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("response", {}).get("models", {})
            result = {}
            for k, v in models.items():
                max_tokens = v.get("maxTokens", 0)
                if max_tokens > 0:
                    result[k.lower()] = max_tokens
            return result
    except Exception:
        return {}

def resolve_model_limit(model_name, live_models):
    """Resolve maximum tokens supported by model."""
    if not model_name:
        return MODEL_LIMITS_FALLBACK["default"], "Gemini (Default)"

    clean_name = model_name.lower().strip()
    
    # 1. Match from live language server models
    if clean_name in live_models:
        return live_models[clean_name], model_name

    for k, v in live_models.items():
        if k in clean_name or clean_name in k:
            return v, k

    # 2. Match from fallback dictionary
    for k, v in MODEL_LIMITS_FALLBACK.items():
        if k in clean_name or clean_name in k:
            return v, k

    # Normalize common naming variations
    if "flash" in clean_name or "gemini" in clean_name:
        return 1048576, "Gemini Flash / Pro (1M)"
    if "claude" in clean_name or "sonnet" in clean_name or "opus" in clean_name:
        return 250000, "Claude (250k)"
    if "gpt" in clean_name:
        return 131072, "GPT (128k)"

    return MODEL_LIMITS_FALLBACK["default"], model_name

def find_latest_transcript():
    """Locate the most recently updated conversation transcript."""
    home = os.path.expanduser("~")
    base_dir = os.path.join(home, ".gemini", "antigravity", "brain")
    if not os.path.exists(base_dir):
        return None, None

    pattern = os.path.join(base_dir, "*", ".system_generated", "logs", "transcript.jsonl")
    files = glob.glob(pattern)
    if not files:
        # Fallback search
        pattern2 = os.path.join(base_dir, "*", "*.jsonl")
        files = [f for f in glob.glob(pattern2) if "transcript" in f]

    if not files:
        return None, None

    # Pick the newest by mtime
    latest_file = max(files, key=os.path.getmtime)
    conv_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(latest_file))))
    return latest_file, conv_id

def parse_transcript(transcript_path):
    """Extract token counts and model info from transcript."""
    if not transcript_path or not os.path.exists(transcript_path):
        return None

    last_input_tokens = 0
    last_cache_tokens = 0
    last_output_tokens = 0
    detected_model = None
    step_count = 0
    total_turns = 0

    with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            step_count += 1
            try:
                entry = json.loads(line)
            except Exception:
                continue

            content = entry.get("content", "")
            if "Model Selection" in content and isinstance(content, str):
                m = re.search(r"Model Selection`?\s+from\s+[^\n\r]+?\s+to\s+`?([a-zA-Z0-9\.\-_]+)", content)
                if m:
                    cand = m.group(1).strip()
                    if any(v in cand.lower() for v in ["gemini", "claude", "gpt", "flash", "pro"]):
                        detected_model = cand

            if entry.get("type") == "PLANNER_RESPONSE":
                total_turns += 1
                inp = entry.get("input_tokens", 0)
                cache = entry.get("cache_read_tokens", 0)
                out = entry.get("output_tokens", 0)
                if inp or cache:
                    last_input_tokens = inp
                    last_cache_tokens = cache
                    last_output_tokens = out

    current_context = last_input_tokens + last_cache_tokens
    return {
        "current_context_tokens": current_context,
        "input_tokens": last_input_tokens,
        "cache_read_tokens": last_cache_tokens,
        "last_output_tokens": last_output_tokens,
        "detected_model": detected_model,
        "step_count": step_count,
        "total_turns": total_turns
    }

def make_progress_bar(ratio, width=24):
    """Render a visual ASCII progress bar."""
    filled = int(round(ratio * width))
    filled = min(max(filled, 0), width)
    empty = width - filled
    return "█" * filled + "░" * empty

def analyze_context(transcript_path=None, conv_id=None, override_model=None, warn_thresh=None, comp_thresh=None, compaction_ceiling=None):
    """Main analysis routine."""
    cfg = load_config()
    if warn_thresh is None:
        warn_thresh = cfg.get("warning_threshold", 0.75)
    if comp_thresh is None:
        comp_thresh = cfg.get("compaction_threshold", 0.80)
    if compaction_ceiling is None:
        compaction_ceiling = cfg.get("compaction_boundary_tokens", 262144)

    if not transcript_path:
        if conv_id:
            home = os.path.expanduser("~")
            transcript_path = os.path.join(home, ".gemini", "antigravity", "brain", conv_id, ".system_generated", "logs", "transcript.jsonl")
        else:
            transcript_path, conv_id = find_latest_transcript()

    if not transcript_path or not os.path.exists(transcript_path):
        return {
            "error": "No transcript file found. Start a conversation or specify --transcript."
        }

    parsed = parse_transcript(transcript_path)
    if not parsed:
        return {"error": f"Failed to parse transcript at {transcript_path}"}

    live_models = get_ls_models()
    model_name = override_model or parsed.get("detected_model") or "Gemini 3.8 Flash (High)"
    max_tokens, resolved_model = resolve_model_limit(model_name, live_models)

    current_tokens = parsed["current_context_tokens"]
    effective_limit = compaction_ceiling if (compaction_ceiling and compaction_ceiling > 0) else max_tokens
    usage_ratio = current_tokens / effective_limit if effective_limit > 0 else 0.0
    usage_percent = usage_ratio * 100.0

    compaction_line_tokens = int(effective_limit * comp_thresh)
    warning_line_tokens = int(effective_limit * warn_thresh)
    critical_line_tokens = int(effective_limit * 0.90)

    remaining_to_compaction = compaction_line_tokens - current_tokens
    remaining_to_max = effective_limit - current_tokens

    # Status classification
    if usage_ratio >= 0.90:
        status_level = "CRITICAL"
        status_text = "🔴 严重超限 (Exceeded Compaction Limit)"
        recommendation = "会话上下文极度饱和，已突破安全线！强烈建议立即运行 `/compact` 压缩上下文或开启新会话以避免截断或性能下降。"
    elif usage_ratio >= comp_thresh:
        status_level = "COMPACTION_TRIGGERED"
        status_text = "🟠 触发压缩线 (Compaction Threshold Reached)"
        recommendation = "当前上下文已跨越推荐压缩线 (80%)。建议执行 `/compact` 进行上下文提炼与摘要，确保后续交互的准确度。"
    elif usage_ratio >= warn_thresh:
        status_level = "WARNING"
        status_text = "🟡 接近压缩线 (Approaching Compaction Line)"
        recommendation = "当前上下文使用率已进入预警区间 (75%~80%)。如果即将开展大型改动或长流程推理，建议准备运行 `/compact`。"
    elif usage_ratio >= 0.50:
        status_level = "MODERATE"
        status_text = "🟢 正常使用 (Moderate)"
        recommendation = "上下文占用适中，模型认知与响应状态良好，无需压缩。"
    else:
        status_level = "OPTIMAL"
        status_text = "🟢 充裕健康 (Optimal)"
        recommendation = "当前上下文资源非常充裕，无需执行任何压缩操作。"

    return {
        "conversation_id": conv_id,
        "transcript_path": transcript_path,
        "model_name": model_name,
        "resolved_model": resolved_model,
        "current_context_tokens": current_tokens,
        "input_tokens": parsed["input_tokens"],
        "cache_read_tokens": parsed["cache_read_tokens"],
        "last_output_tokens": parsed["last_output_tokens"],
        "max_context_tokens": effective_limit,
        "model_window_tokens": max_tokens,
        "compaction_boundary_tokens": effective_limit,
        "usage_ratio": usage_ratio,
        "usage_percent": usage_percent,
        "warning_threshold_ratio": warn_thresh,
        "warning_line_tokens": warning_line_tokens,
        "compaction_threshold_ratio": comp_thresh,
        "compaction_line_tokens": compaction_line_tokens,
        "critical_line_tokens": critical_line_tokens,
        "remaining_to_compaction": remaining_to_compaction,
        "remaining_to_max": remaining_to_max,
        "status_level": status_level,
        "status_text": status_text,
        "recommendation": recommendation,
        "step_count": parsed["step_count"],
        "total_turns": parsed["total_turns"],
        "progress_bar": make_progress_bar(usage_ratio, 20)
    }

def get_loaded_skills():
    """Retrieve active skills via LanguageServerService RPC or filesystem scan."""
    ls_addr = os.environ.get("ANTIGRAVITY_LS_ADDRESS")
    csrf = os.environ.get("ANTIGRAVITY_CSRF_TOKEN", "")
    if ls_addr:
        try:
            url = f"http://{ls_addr}/exa.language_server_pb.LanguageServerService/GetAllSkills"
            req = urllib.request.Request(url, data=b"{}", headers={
                "Content-Type": "application/json",
                "x-codeium-csrf-token": csrf
            })
            with urllib.request.urlopen(req, timeout=1) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("skills", [])
        except Exception:
            pass

    # Fallback to filesystem scan
    home = os.path.expanduser("~")
    skills = []
    builtin_dir = os.path.join(home, ".gemini", "antigravity", "builtin", "skills")
    if os.path.exists(builtin_dir):
        for sname in os.listdir(builtin_dir):
            sfile = os.path.join(builtin_dir, sname, "SKILL.md")
            if os.path.exists(sfile):
                skills.append({"name": sname, "path": sfile, "description": f"Built-in skill: {sname}"})
    plugins_dir = os.path.join(home, ".gemini", "config", "plugins")
    if os.path.exists(plugins_dir):
        for root, dirs, files in os.walk(plugins_dir):
            if "SKILL.md" in files:
                sname = os.path.basename(root)
                skills.append({"name": sname, "path": os.path.join(root, "SKILL.md"), "description": f"Plugin skill: {sname}"})
    return skills

def get_active_rules():
    """Scan and retrieve active user rules and AGENTS.md files."""
    home = os.path.expanduser("~")
    rules = []
    plugins_dir = os.path.join(home, ".gemini", "config", "plugins")
    if os.path.exists(plugins_dir):
        for root, dirs, files in os.walk(plugins_dir):
            for f in files:
                if f.lower() in ("agents.md", "rules.md") or (f.endswith(".md") and "rules" in root.lower()):
                    rules.append(os.path.join(root, f))
    conf_rules = os.path.join(home, ".gemini", "config", "rules")
    if os.path.exists(conf_rules):
        for f in os.listdir(conf_rules):
            if f.endswith(".md"):
                rules.append(os.path.join(conf_rules, f))
    return rules

def format_markdown(data, lang=None):
    """Format analysis data as a clean, functional, simplified, emoji-free markdown report."""
    if "error" in data:
        return f"Error: Context Monitor failed: {data['error']}"

    cfg = load_config()
    if not lang:
        lang = cfg.get("language", "zh")

    is_zh = (lang == "zh")

    cur = data.get("current_context_tokens", 0)
    bound_t = data.get("compaction_boundary_tokens", data.get("max_context_tokens", 262144))
    model_w = data.get("model_window_tokens", 1048576)
    pct = data.get("usage_percent", 0.0)
    bar = data.get("progress_bar", "")
    comp_line = data.get("compaction_line_tokens", int(bound_t * 0.80))
    warn_line = data.get("warning_line_tokens", int(bound_t * 0.75))
    rem_comp = data.get("remaining_to_compaction", comp_line - cur)
    cache = data.get("cache_read_tokens", 0)
    input_t = data.get("input_tokens", 0)
    model = data.get("resolved_model", "Active Model")
    turns = data.get("total_turns", 0)
    steps = data.get("step_count", 0)
    
    bound_k = "256k" if bound_t in (262144, 256000) else (f"{bound_t//1000}k" if bound_t >= 1000 else str(bound_t))
    model_k = f"{model_w//1000}k" if model_w >= 1000 else str(model_w)

    clean_bar = bar.replace("█", "#").replace("░", "-") if bar else ""
    skills = get_loaded_skills()
    skill_names = [f"`{s.get('name', 'skill')}`" for s in skills] if skills else []
    skills_str = ", ".join(skill_names) if skill_names else ("无" if is_zh else "None")

    level = data.get("status_level", "OPTIMAL")
    if is_zh:
        if level == "OPTIMAL":
            status_lbl = "健康充裕 (Optimal)"
        elif level == "MODERATE":
            status_lbl = "平稳正常 (Normal)"
        elif level == "WARNING":
            status_lbl = "临界预警 (Warning)"
        else:
            status_lbl = "建议压缩 (Action Required)"

        comp_dist_str = f"+{rem_comp:,} tokens (充裕健康)" if rem_comp > 0 else f"-{abs(rem_comp):,} tokens (已超推荐线)"
        
        md = [
            "# 会话上下文与运行监控报告\n",
            "> 由 context-monitor 动态维护 · 每轮交互自动刷新\n",
            "## 1. 上下文指标 (Context Metrics)",
            f"运行状态: {status_lbl}\n",
            f"```text\n[{clean_bar}] {pct:.2f}% ({cur:,} / {bound_t:,} tokens [{bound_k} 压缩上限])\n```\n",
            "| 指标 | 当前数值 | 说明 |",
            "| :--- | :--- | :--- |",
            f"| 活跃模型 | `{model}` | 模型窗口上限: {model_k} |",
            f"| 当前上下文 | **{cur:,}** tokens | 最近一轮发送给模型的总 Prompt 大小 |",
            f"| 缓存命中量 | `{cache:,}` tokens (~{cache*100//max(cur,1)}%) | Context Caching 缓存命中读取量 |",
            f"| 增量输入 | `{input_t:,}` tokens | 本轮新增用户输入与工具执行结果 |",
            f"| 压缩硬限制 | **{bound_t:,}** tokens | 系统自动 Checkpoint 压缩上限 ({bound_k}) |",
            f"| 推荐压缩线 (80%) | `{comp_line:,}` tokens | 达到此阈值建议运行 `/compact` |",
            f"| 预警监控线 (75%) | `{warn_line:,}` tokens | 接近压缩区间的监控阈值 |",
            f"| 距离压缩线 | **{comp_dist_str}** | 距离 80% 推荐线的可用空间余量 |",
            f"| 累计交互轮次 | `{turns}` 轮 ({steps} 步) | 会话总执行轨迹步数 |",
            "\n---\n",
            "## 2. 运行环境与技能组件 (Environment)",
            f"- **已装配技能 (Skills)**: {skills_str} (共 {len(skills)} 个)",
            "- **提示词架构 (Architecture)**: `<identity>`, `<artifacts>`, `<conversation_transcript>`, `<guidelines>`, `<communication_style>`, `<slash_commands>`, `<subagents>`, `<skills>`, `<default_api>`, `<user_information>` (10 个基座块)",
            "\n---\n",
            "## 3. 诊断与行动建议 (Guidance)"
        ]
        if data.get("usage_ratio", 0) >= data.get("warning_threshold_ratio", 0.75):
            md.append(f"- 状态: 已接近或超过压缩建议线 ({pct:.1f}%)。")
            md.append("- 建议: 建议在当前阶段性任务完成后，使用 `/compact` 命令执行会话压缩。")
        else:
            md.append(f"- 状态: 健康良好 (当前使用率 {pct:.1f}%，基准上限 {bound_k})。")
            md.append(f"- 建议: 上下文预算非常充足 ({comp_dist_str})，继续正常编码交互即可，无需压缩。")
    else:
        if level == "OPTIMAL":
            status_lbl = "Optimal (Healthy)"
        elif level == "MODERATE":
            status_lbl = "Normal (Stable)"
        elif level == "WARNING":
            status_lbl = "Warning (Approaching Line)"
        else:
            status_lbl = "Action Required"

        comp_dist_str = f"+{rem_comp:,} tokens (healthy budget)" if rem_comp > 0 else f"-{abs(rem_comp):,} tokens (exceeded threshold)"
        
        md = [
            "# Context & Environment Report\n",
            "> Maintained by context-monitor · Auto-updated per turn\n",
            "## 1. Context Metrics",
            f"Status: {status_lbl}\n",
            f"```text\n[{clean_bar}] {pct:.2f}% ({cur:,} / {bound_t:,} tokens [{bound_k} Compaction Ceiling])\n```\n",
            "| Metric | Value | Details |",
            "| :--- | :--- | :--- |",
            f"| Model | `{model}` | Model Window: {model_k} |",
            f"| Current Context | **{cur:,}** tokens | Total prompt tokens in latest turn |",
            f"| Cache Hits | `{cache:,}` tokens (~{cache*100//max(cur,1)}%) | Context Caching read tokens |",
            f"| Fresh Input | `{input_t:,}` tokens | New user and incremental step tokens |",
            f"| Compaction Ceiling | **{bound_t:,}** tokens | Runtime auto-checkpoint boundary ({bound_k}) |",
            f"| Compaction Line (80%) | `{comp_line:,}` tokens | Recommended compaction trigger |",
            f"| Warning Line (75%) | `{warn_line:,}` tokens | Pre-compaction monitoring threshold |",
            f"| Remaining to Compaction | **{comp_dist_str}** | Space available before 80% line |",
            f"| Turn Counter | `{turns}` turns ({steps} steps) | Trajectory counter |",
            "\n---\n",
            "## 2. Environment & Loaded Components",
            f"- **Loaded Skills**: {skills_str} ({len(skills)} total)",
            "- **Prompt Architecture**: `<identity>`, `<artifacts>`, `<conversation_transcript>`, `<guidelines>`, `<communication_style>`, `<slash_commands>`, `<subagents>`, `<skills>`, `<default_api>`, `<user_information>` (10 base blocks)",
            "\n---\n",
            "## 3. Assessment & Guidance"
        ]
        if data.get("usage_ratio", 0) >= data.get("warning_threshold_ratio", 0.75):
            md.append(f"- Status: Approaching or beyond threshold ({pct:.1f}%).")
            md.append("- Recommendation: Initiate compaction via `/compact` at the next logical task boundary.")
        else:
            md.append(f"- Status: Healthy ({pct:.1f}% of {bound_t:,} tokens utilized [{bound_k} ceiling]).")
            md.append(f"- Recommendation: Context budget is ample ({comp_dist_str}). Continue standard workflow.")

    return "\n".join(md)

def generate_pill_html(data):
    """Generate an ultra-compact single-pill Generative UI HTML widget."""
    cur = data.get("current_context_tokens", 0)
    max_t = data.get("max_context_tokens", 1048576)
    pct = data.get("usage_percent", 0.0)
    rem = data.get("remaining_to_compaction", 0)
    model = data.get("resolved_model", "Active Model")

    # Shorten model name
    model_short = model.split("(")[0].strip()
    if len(model_short) > 16:
        model_short = model_short[:15] + ".."

    cur_str = f"{cur:,}"
    max_str = f"{max_t/1000:.0f}k" if max_t >= 10000 else f"{max_t:,}"
    
    if rem > 0:
        rem_str = f"🟢 距压缩线 {rem/1000:.0f}k" if rem >= 10000 else f"🟢 距压缩线 {rem:,}"
        rem_class = "text-emerald-400"
    else:
        rem_str = f"🔴 超压缩线 {abs(rem)/1000:.0f}k"
        rem_class = "text-rose-400 font-bold"

    capped_pct = min(max(pct, 0.0), 100.0)

    if pct >= 80:
        dot_color = "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]"
        tag_class = "bg-rose-500/10 text-rose-400 border border-rose-500/20"
        bar_class = "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.7)]"
    elif pct >= 75:
        dot_color = "bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.8)]"
        tag_class = "bg-amber-500/10 text-amber-400 border border-amber-500/20"
        bar_class = "bg-amber-500"
    else:
        dot_color = "bg-emerald-400"
        tag_class = "bg-sky-500/10 text-sky-400 border border-sky-500/20"
        bar_class = "bg-gradient-to-r from-emerald-500 via-sky-500 to-indigo-500"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @keyframes pulse-dot {{ 0%, 100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: 0.5; transform: scale(1.15); }} }}
    .pulsing-dot {{ animation: pulse-dot 2s infinite ease-in-out; }}
  </style>
</head>
<body class="bg-transparent text-[var(--foreground,#f8fafc)] antialiased m-0 p-1 select-none font-sans overflow-hidden">
  <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl px-3 py-1.5 shadow-sm flex flex-col justify-center space-y-1">
    
    <!-- Top Row: Info & Stats -->
    <div class="flex items-center justify-between text-xs">
      <div class="flex items-center space-x-2">
        <span class="w-2 h-2 rounded-full {dot_color} pulsing-dot"></span>
        <span class="font-bold text-[var(--foreground,#f8fafc)] font-mono text-[11px] tracking-tight">{model_short}</span>
        <span class="text-[var(--muted-foreground,#94a3b8)]">|</span>
        <span class="font-semibold text-[var(--foreground,#f8fafc)] font-mono text-[11px]">{cur_str} <span class="text-[var(--muted-foreground,#94a3b8)] font-normal">/ {max_str}</span></span>
        <span class="px-1.5 py-0.2 text-[10px] rounded font-mono font-bold {tag_class}">{pct:.1f}%</span>
      </div>

      <div class="flex items-center space-x-2">
        <span class="text-[11px] font-medium {rem_class} font-mono">{rem_str}</span>
        <button onclick="navigator.clipboard.writeText('/compact')" title="点击复制压缩命令" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/60 hover:bg-slate-600 text-slate-200 transition border border-slate-600/50 flex items-center space-x-1 cursor-pointer">
          <span>/compact</span>
        </button>
      </div>
    </div>

    <!-- Bottom Row: Progress Bar with 80% Compaction Line -->
    <div class="relative w-full h-1.5 bg-slate-800/90 rounded-full overflow-hidden border border-slate-700/50">
      <!-- 80% Compaction Line Marker -->
      <div class="absolute top-0 bottom-0 left-[80%] w-[2px] bg-rose-500 z-10 shadow-[0_0_6px_rgba(244,63,94,0.9)]" title="80% 推荐压缩线"></div>
      <!-- 75% Warning Line Marker -->
      <div class="absolute top-0 bottom-0 left-[75%] w-[1px] bg-amber-400/80 z-10" title="75% 警戒线"></div>
      <!-- Progress Bar Fill -->
      <div class="h-full {bar_class} rounded-full transition-all duration-500" style="width: {capped_pct:.1f}%;"></div>
    </div>

  </div>
</body>
</html>"""
    return html

def sync_dynamic_artifact(artifact_dir, data):
    """Automatically maintain a dynamic artifact whose title and filename directly reflect current context usage."""
    if not artifact_dir or not os.path.exists(artifact_dir):
        return None
    import datetime
    cur = data.get("current_context_tokens", 0)
    bound_t = data.get("compaction_boundary_tokens", data.get("max_context_tokens", 262144))
    pct = data.get("usage_percent", 0.0)
    cur_k = f"{cur//1000}k" if cur >= 1000 else str(cur)
    bound_k = "256k" if bound_t in (262144, 256000) else (f"{bound_t//1000}k" if bound_t >= 1000 else str(bound_t))
    
    target_name = f"Context_[{cur_k}_{bound_k}].md"
    target_file = os.path.join(artifact_dir, target_name)
    target_meta = os.path.join(artifact_dir, target_name + ".metadata.json")
    
    # Clean up previous context artifacts in this directory
    try:
        for fname in os.listdir(artifact_dir):
            if fname.startswith("Context_") and (fname.endswith(".md") or fname.endswith(".json")):
                if fname != target_name and fname != (target_name + ".metadata.json"):
                    try:
                        os.remove(os.path.join(artifact_dir, fname))
                    except Exception:
                        pass
            elif fname.startswith("context_status.md"):
                try:
                    os.remove(os.path.join(artifact_dir, fname))
                except Exception:
                    pass
    except Exception:
        pass
    
    # Write updated markdown content and metadata
    try:
        cfg = load_config()
        lang = cfg.get("language", "zh")
        md_content = format_markdown(data, lang=lang)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        rem_tok = data.get("remaining_to_compaction", 0)
        if lang == "zh":
            summary_text = f"会话上下文: {cur_k} / {bound_k} ({pct:.1f}%) | 距 80% 压缩线还剩 {rem_tok:,} tokens"
        else:
            summary_text = f"Context: {cur_k} / {bound_k} ({pct:.1f}%) | {rem_tok:,} tokens before 80% line"

        meta = {
            "summary": summary_text,
            "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "userFacing": True
        }
        with open(target_meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        return target_file
    except Exception:
        return None

def sync_all_conversations():
    """Scan all conversations in brain base directory and update their dynamic context artifacts."""
    home = os.path.expanduser("~")
    base_dir = os.path.join(home, ".gemini", "antigravity", "brain")
    if not os.path.exists(base_dir):
        return 0, []
    
    pattern = os.path.join(base_dir, "*", ".system_generated", "logs", "transcript.jsonl")
    files = glob.glob(pattern)
    synced = []
    
    for f in files:
        cid = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(f))))
        artifact_dir = os.path.join(base_dir, cid)
        try:
            data = analyze_context(transcript_path=f, conv_id=cid)
            if "error" not in data and data.get("current_context_tokens", 0) > 0:
                res = sync_dynamic_artifact(artifact_dir, data)
                if res:
                    synced.append({
                        "conversation_id": cid,
                        "tokens": data.get("current_context_tokens", 0),
                        "max_tokens": data.get("max_context_tokens", 0),
                        "percent": round(data.get("usage_percent", 0.0), 1),
                        "artifact": os.path.basename(res)
                    })
        except Exception:
            pass
    return len(synced), synced

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Antigravity Context Monitor")
    parser.add_argument("--transcript", type=str, help="Path to transcript.jsonl")
    parser.add_argument("--conversation-id", type=str, help="Conversation ID")
    parser.add_argument("--model", type=str, help="Override model name")
    parser.add_argument("--warn-threshold", type=float, default=0.75, help="Warning ratio (default: 0.75)")
    parser.add_argument("--comp-threshold", type=float, default=0.80, help="Compaction ratio (default: 0.80)")
    parser.add_argument("--format", type=str, choices=["md", "json", "text"], default="md", help="Output format")
    parser.add_argument("--lang", type=str, choices=["zh", "en"], default=None, help="Language output (zh or en)")

    args = parser.parse_args()
    data = analyze_context(
        transcript_path=args.transcript,
        conv_id=args.conversation_id,
        override_model=args.model,
        warn_thresh=args.warn_threshold,
        comp_thresh=args.comp_threshold
    )

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif args.format == "md":
        # Ensure utf-8 output on Windows
        sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
        print(format_markdown(data, lang=args.lang))
    else:
        sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
        print(f"Context: {data.get('current_context_tokens', 0):,} / {data.get('max_context_tokens', 0):,} tokens ({data.get('usage_percent', 0.0):.2f}%)")
        print(f"Status: {data.get('status_text')}")
        print(f"Recommendation: {data.get('recommendation')}")

if __name__ == "__main__":
    main()
