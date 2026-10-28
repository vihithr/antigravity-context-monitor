---
name: context-monitor
description: 监听并查询 Antigravity 会话的实时上下文长度、活跃模型的最大上下文限制，计算距离压缩线（75%~80% 推荐阈值）的剩余空间，并提供上下文压缩操作建议。
---

# Context Monitor & Compaction Alert Skill

本 Skill 允许你或用户随时查询当前 Antigravity 交互会话的上下文 Token 使用情况、活跃模型上限，以及距离会话“压缩线”的余量。

## 使用场景

- 用户询问：“当前上下文用了多少？”、“离压缩线还有多远？”、“模型支持多大上下文？”、“需要压缩了吗？”
- 进行了大量文件读取、长输出生成或复杂多轮代码重构后，主动评估上下文健康状态。
- 在上下文警报触发后，为用户生成详细的上下文消耗与压缩建议报告。

## 执行方式

运行插件自带的分析脚本 `scripts/monitor.py`：

```bash
python ~/.gemini/config/plugins/context-monitor/scripts/monitor.py --format md
```

若在 Windows PowerShell 环境下：
```powershell
python "$env:USERPROFILE\.gemini\config\plugins\context-monitor\scripts\monitor.py" --format md
```

### 可选参数

- `--format md`: 输出格式化 Markdown 表格与 ASCII 进度条（默认推荐，可直接展示给用户）。
- `--format json`: 输出结构化 JSON 格式数据供自动化分析。
- `--warn-threshold 0.75`: 预警阈值比例（默认 0.75，即 75%）。
- `--comp-threshold 0.80`: 推荐压缩线比例（默认 0.80，即 80%）。
- `--conversation-id <id>`: 指定分析特定历史会话。

## 指标解读与行动指导

1. **当前上下文 (Current Context Tokens)**:
   - 由 Prompt 输入 Token 与 Context Caching 缓存命中 Token 组成，反映了当前发送给模型进行推理的上下文体积。
2. **模型窗口上限 (Max Context Tokens)**:
   - 活跃模型支持的最大输入 Token 数量（例如 Gemini Flash/Pro 为 1,048,576，Claude 4.6 系列为 250,000）。
3. **压缩线 (Compaction Line, 默认 80%)**:
   - 当上下文超过此界限，模型的响应延迟可能增加、细节召回率可能下降，应建议用户运行 `/compact`。
4. **状态级别**:
   - 🟢 **充裕健康 (< 60%)**: 空间充裕，无需任何压缩。
   - 🟡 **正常关注 (60% ~ 75%)**: 随着对话进行平稳增长。
   - 🟠 **接近压缩线 (75% ~ 80%)**: 提醒用户已接近安全临界，准备阶段性总结。
   - 🔴 **触发压缩线 (>= 80%)**: 主动向用户推荐运行 `/compact` 压缩当前会话。
