# Antigravity Context Monitor (App Edition)

> Dedicated real-time context & 256k compaction boundary monitor tailored specifically for **Google Antigravity App (Antigravity 2.0)**.  
> 专为 **Google Antigravity 桌面端应用（Antigravity 2.0）** 量身定制的上下文用量与 256k 自动压缩硬边界监控插件。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Antigravity App](https://img.shields.io/badge/Platform-Antigravity%20App%202.0-purple.svg)](https://antigravity.google)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)

---

## 为什么专为 Antigravity App 设计？(Surface Comparison)

Google Antigravity 拥有三种主要交互界面（Surfaces），它们的交互形态与上下文监控痛点截然不同：

| 特性维度 | Antigravity CLI (`agy`) | Antigravity IDE (VS Code Fork) | **Antigravity App (本项目定位)** |
| :--- | :--- | :--- | :--- |
| **界面形态** | 纯终端交互 (Terminal / REPL) | 编辑器工作区 (Editor Canvas) | **独立 Electron 桌面应用** |
| **原有监控手段** | 终端命令行或底部状态输出 | VS Code 底部状态栏 (Status Bar) | **无编辑器状态栏，难以直观感知用量** |
| **痛点** | 依赖 CLI 命令反复查询 | 侧重单文件编辑，非多会话流 | **会话深长且缺乏常驻指示，易突发自动压缩** |
| **本插件解决方案** | 终端 `--format text` 输出 | 暂不作为主要目标表面 | **利用 App 专属【右侧工件抽屉】与【Sidecar HUD】** |
| **呈现方式** | 控制台打印 | 编辑器浮窗 | **`Context_[xxk_256k].md` 标题直显 + 独立侧边栏** |

在 **Antigravity App** 中，既没有传统 IDE 的编辑器底部状态栏，也不像 CLI 频繁打印终端行。当长流程对话不断累积，用户极易在毫无准备的情况下遭遇系统的 **256k 强制压缩（Checkpoint Compaction）**。

本插件专为 Antigravity App 的界面交互哲学设计：**利用 App 右侧原生工件列表（Artifacts Drawer）的文件名，让上下文数值像呼吸灯一样无需点击直接常驻可见，并支持 Sidecar Aux Pane 扩展。**

---

## 核心特性 (Features)

1. **锁定 256K 真实自动压缩边界 (256k Compaction Ceiling)**
   - 破除“1M 物理窗口”的虚假安全感：Antigravity 平台在单会话历史累积达到 **256k tokens ($256 \times 1024 = 262,144$)** 时，系统语言调度器将强制触发自动检查点压缩。
   - 本插件以此真实边界为基准，在 75%（~196k）和 80%（~209k）提供精准预警。

2. **工件面板原生集成 (Native Artifacts Integration)**
   - 动态工件直接在 App 右侧列表中自动以 `Context_[{cur_k}_256k].md` 命名。
   - **无需打开文件**，一眼即知当前会话已消耗多少、离 256k 还剩多少。

3. **零干扰、零 Emoji 极简工程报告 (Zero-Emoji High-Density Report)**
   - 贯彻 Less is More 设计准则，剔除所有无关装饰性图标与大段规则说教。
   - 一屏直达：ASCII 进度条、缓存命中率（~98%）、增量输入量、装配技能与系统基座架构。

4. **中英双语即时切换 (Bilingual zh/en)**
   - 配置文件支持 `"language": "zh"` 或 `"language": "en"`。
   - 终端亦支持 `--lang zh` / `--lang en` 即时换言。

5. **多会话一键全局同步 (Multi-Session Synchronization)**
   - 无论您在 App 中并行运行了多少个会话，一键巡检同步所有会话指标。

6. **原生 Sidecar HUD 侧边栏仪表盘 (Aux Pane Sidecar)**
   - 支持通过 App 的 Sidecar 体系将可视化监控条常驻于 Aux Pane。

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

### 跨平台通用 Python 安装
```bash
git clone https://github.com/vihithr/antigravity-context-monitor.git
cd antigravity-context-monitor
python install.py
```

> **提示**：安装脚本会自动将文件部署至 `~/.gemini/config/plugins/context-monitor/`。安装后请**完全重启 Antigravity App** 以生效。

---

## 快速卸载 (Uninstallation)

* **Windows**: `irm https://raw.githubusercontent.com/vihithr/antigravity-context-monitor/main/uninstall.ps1 | iex`
* **macOS/Linux**: `curl -fsSL https://raw.githubusercontent.com/vihithr/antigravity-context-monitor/main/uninstall.sh | bash`
* **Python**: `python install.py --uninstall`

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
| `compaction_boundary_tokens` | `262144` | 压缩硬基准上限（256k tokens） |
| `warning_threshold` | `0.75` | 预警线比例（75% = 196,608 tokens） |
| `compaction_threshold` | `0.80` | 推荐压缩线比例（80% = 209,715 tokens） |
| `critical_threshold` | `0.90` | 严重超限比例（90% = 235,929 tokens） |

---

## 终端使用 (CLI Usage)

```bash
# 查看当前会话格式化报告（默认跟随配置文件语言）
python ~/.gemini/config/plugins/context-monitor/scripts/monitor.py --format md

# 临时以英文格式输出
python ~/.gemini/config/plugins/context-monitor/scripts/monitor.py --format md --lang en

# 输出 JSON 格式供其他脚本集成
python ~/.gemini/config/plugins/context-monitor/scripts/monitor.py --format json
```

---

## 开源协议 (License)

[MIT License](LICENSE) © 2026 vihithr
