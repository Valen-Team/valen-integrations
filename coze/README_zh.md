# Valen 扣子（Coze）插件

[English](README.md)

一个扣子云插件，包含四个工具，实现 [SPEC.md](../SPEC.md)：**是否（yes_no）**、**单选（choice）**、**打分（score）**、**评估（evaluate）**。工作流的条件节点直接按各工具输出的 `branch` 分支。

coze.cn 访问不到 `*.workers.dev` 上的免费端点，所以插件改为调用 `https://llm-proxy.openxxlab.com/v1`，所用的 API key 只写在扣子服务器上的插件代码里，插件使用者不需要 key。

## 文件

| 路径 | 用途 |
| --- | --- |
| `tools/<工具名>.py` | 粘贴进扣子 IDE 各工具的代码。由脚本生成，不要直接改。 |
| `src/` | 源码：`common.py`（请求、重试、图片、错误）和每个工具的 handler。 |
| `build.py` | 运行 `python build.py` 由 `src/` 重新生成 `tools/`。 |
| `tests/` | 离线测试：`python -m pytest tests`。 |

## 创建插件

1. 在扣子工作空间打开 **资源库** → **+ 资源** → **插件**，选择 **云端插件**、**在 Coze IDE 中创建**，运行时选 **Python3**。
2. 对下表每个工具，**添加工具**并填写工具名，然后：
   1. 在 **元数据** 中按表添加输入参数。
   2. 在 **代码** 中全部替换为 `tools/<工具名>.py`，并把 `API_KEY = "..."` 改成插件专用的 Valen API key。
   3. 用示例输入 **测试代码**，再点 **更新输出参数**，由测试结果生成输出参数。
3. **发布** 插件。个人信息收集声明选 **是**：插件会把用户的文本和图片发送给 Valen API。
4. 在工作流中从 **资源库工具** 添加工具，在条件节点里按 `branch` 分支。

## 工具

每个工具都还接受 `input`（String，必填：要判断的文本）、`image`（String，可选：图片 URL，支持 PNG、JPEG、WebP）和 `model`（String，可选，默认 `valen-2b`）。

| 工具 | 专有输入 | 输出 |
| --- | --- | --- |
| `yes_no` | `question`（String，必填）、`yes_at`（Number，默认 0.7）、`no_at`（Number，默认 0.3） | `probability`、`branch`（`yes` / `no` / `unsure`）、`model` |
| `choice` | `question`（String，必填）、`options`（String，必填：每行一个，`值` 或 `值: 说明`） | `choice`、`confidence`、`probabilities`、`branch`（即所选项）、`model` |
| `score` | `question`（String，必填）、`levels`（String，必填：每行一级，从低到高，`标签` 或 `标签: 说明`） | `score`、`level`、`confidence`、`probabilities`、`branch`（即最可能的等级）、`model` |
| `evaluate` | `questions`（String，必填：Decisions API 的 `questions` 数组，JSON 格式） | `answers`（按问题名索引）、`model` |

例如 `choice` 的测试输入：

```json
{"input": "I was charged twice and want my money back.", "question": "Which team should handle this?", "options": "billing: Payments and charges\ntech: Software errors\naccount"}
```

## 更新

修改 `src/`，运行 `python build.py` 和测试，再把有变动的 `tools/<工具名>.py` 粘贴进 IDE（保留 `API_KEY` 那一行），发布新版本。
