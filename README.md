# Antigravity Context Monitor

> Real-time Context Window & 256k Compaction Boundary Monitor for Google Antigravity.  
> 实时监听 Google Antigravity 会话上下文 Token 占用，锁定真实 256k 自动压缩硬边界，提供零污染高密度报告。

---

## 核心特性 (Features)

1. **真实 256K 自动压缩边界预警 (256k Compaction Ceiling)**
   - 告别“1M 理论窗口”的认知错觉。Antigravity 底层在会话累积达到 **256k tokens (262,144 tokens)** 时会强制触发自动检查点压缩（Auto-Checkpoint Compaction）。
   - 本插件将 256k 锁定为基准硬上限，精准预警 75% 警戒线（~196k）与 80% 推荐压缩线（~209k）。

2. **零干扰、零 Emoji 高密度工程报告 (Zero-Emoji High-Density Report)**
   - 遵从极简实用哲学（Less is more），去除无意义装饰与煽动性图标。
   - 动态工件直接在右侧 Artifacts 列表命名为 `Context_[{cur_k}_256k].md`，无需点开即可一览用量。
   - 剥离繁琐冗余的 rules/AGENTS.md 赘述，一屏直达核心指标。

3. **中英双语无缝支持 (Bilingual zh/en)**
   - 配置文件支持 `"language": "zh"` 或 `"language": "en"`。
   - 终端支持通过 `--lang zh` / `--lang en` 即时切换。

4. **全局会话一键巡检 (Multi-Session Synchronization)**
   - 支持一键跨会话扫描，自动为本地所有活跃会话生成/更新上下文指标。

5. **原生 PreInvocation 钩子 (Lifecycle Hook)**
   - 依托 Antigravity 原生 PreInvocation 生命周期，在新轮次发起或执行操作前自动更新指标，零额外手动介入。

---

## 快速安装 (Quick Installation)

### Windows (PowerShell 一键安装)
打开 PowerShell 运行：
```powershell
irm https://raw.githubusercontent.com/vihithr/antigravity-context-monitor/main/install.ps1 | iex
```

### macOS / Linux (Shell 一键安装)
打开终端运行：
```bash
curl -fsSL https://raw.githubusercontent.com/vihithr/antigravity-context-monitor/main/install.sh | bash
```

### 跨平台 Python 安装
```bash
git clone https://github.com/vihithr/antigravity-context-monitor.git
cd antigravity-context-monitor
python install.py
```

> **注意**：安装完成后，**重启 Antigravity / Antigravity IDE** 即可完成加载。

---

## 卸载 (Uninstallation)

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/vihithr/antigravity-context-monitor/main/uninstall.ps1 | iex
```

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/vihithr/antigravity-context-monitor/main/uninstall.sh | bash
```

### Python
```bash
python install.py --uninstall
```

---

## 配置说明 (Configuration)

配置文件位于 `~/.gemini/config/plugins/context-monitor/context_monitor_config.json`：

```json
{
  "language": "zh",
  "compaction_boundary_tokens": 262144,
  "warning_threshold": 0.75,
  "compaction_threshold": 0.80,
  "critical_threshold": 0.90,
  "always_report": false
}
```

| 配置项 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `language` | `"zh"` | 报告语言，可选 `"zh"` (中文) 或 `"en"` (英文) |
| `compaction_boundary_tokens` | `262144` | 压缩基准上限（256k tokens） |
| `warning_threshold` | `0.75` | 预警线比例（75% = 196,608 tokens） |
| `compaction_threshold` | `0.80` | 推荐压缩线比例（80% = 209,715 tokens） |
| `critical_threshold` | `0.90` | 严重超限比例（90% = 235,929 tokens） |

---

## 终端使用 (CLI Usage)

```bash
# 查看当前会话格式化 Markdown 报告
python ~/.gemini/config/plugins/context-monitor/scripts/monitor.py --format md

# 英文模式输出
python ~/.gemini/config/plugins/context-monitor/scripts/monitor.py --format md --lang en

# 输出 JSON 结构化数据
python ~/.gemini/config/plugins/context-monitor/scripts/monitor.py --format json
```

---

## 开源协议 (License)

[MIT License](LICENSE) © 2026 vihithr
