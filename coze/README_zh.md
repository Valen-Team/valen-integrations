# 在扣子中使用 Valen

[English](README.md)

把客服工单分给合适的团队，检查图片中的具体内容，或按紧急程度处理告警。添加公开 Valen 插件，写下要判断的问题，就能把答案与概率用在智能体或工作流中。

## 添加插件

1. 打开[扣子插件商店中的 Valen 万澜](https://www.coze.cn/store/plugin/7702606163640074283)。
2. 进入「插件工具」，选择需要的工具，点击「添加到我的智能体」。在工作流里添加插件节点时，也可以搜索 **Valen 万澜**。
3. 先试 `yes_no`：`input` 填入一条工单，`question` 填「客户要求退款。」，其他参数保留默认值。

无需填写 API 密钥。工具返回 `probability`、`branch`（`yes`、`no`、`unsure`）和 `model`。在条件节点中读取 `branch`，就能把明确结果与人工复核分别连接到后续步骤；请求失败使用独立错误出口。

**Choice** 从具名选项中单选，**Score** 判断有序等级，**Evaluate** 一次回答多个问题。可选 `image` 接受可下载的 PNG、JPEG 或 WebP 图片 URL。输入和图片会发送到 Valen 服务，见[数据处理说明](PRIVACY.md)。

需要完整示例时，可按[工单复核配置](examples/support-review/recipe.json)和同目录的代码节点、测试输入搭建。它是手动配置说明，不是可导入的扣子 DSL。示例只返回队列数据，不执行退款或发送消息。

## 维护插件

以下内容供自行创建和维护插件的开发者使用。使用公开商店插件可直接按上面的步骤开始。

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

### 复建工单工作流

创建者的[实际工作流](https://www.coze.cn/work_flow?workflow_id=7702424956361900058&space_id=7702094046076157987)需要对应空间权限。其他用户可按[配置说明](examples/support-review/recipe.json)、同目录中的四个代码节点文件，以及[cases.json](examples/support-review/cases.json)中的测试输入复建。

配置说明**不是可导入的扣子 DSL 导出文件**。当前账号点击原生工作流导出会出现付费套餐提示，本次未购买订阅。

1. 创建工作流，在开始节点添加必填 String `input`。添加可选 String `image`、`question`、`model`，以及 Number `yesAt`、`noAt`。图片默认留空，其余默认值依次为 `The customer requests a refund.`、`valen-2b`、`0.7`、`0.3`；展开参数行可设置默认值。
2. 添加已发布的 Valen `yes_no` 工具，绑定开始节点各字段；工具的 `yes_at` 对应 `yesAt`，`no_at` 对应 `noAt`。整体超时设 420 秒，工作流节点不重试，异常处理选**执行异常流程**。插件内部已对临时请求故障重试。
3. 正常输出连接选择器：`branch == yes` → Refund queue，`branch == no` → Support queue，否则 → Review queue。三个出口都是代码节点，使用对应 `.ts` 文件。`input` 绑定开始节点，`branch`、`probability`、`model` 绑定 `yes_no`。输出只声明一个通用 Object `result`。
4. 插件的独立错误端口连接 Request failure，使用 `failure.ts`，输入绑定开始节点的 `input` 和插件的 **errorBody Object**。失败结果保留原文和扣子错误详情，不含正常答案或概率。
5. 四个出口都连接同一个变量聚合节点。仅建一个 Object 分组 `Group1`，填入四个 `result` 候选值，策略为**返回每个分组中第一个非空的值**。聚合节点连接结束节点，返回 `result = Group1`。
6. 发布前运行全部测试。扣子试运行 JSON 模式使用 `{"_input": {...}}` 包装工作流入参，`cases.json` 已提供实际格式。unsure 测试通过扩大中间阈值区间验证路由，不是准确率测试。图片测试更换了判断问题，但保留示例的出口名。所有出口仅返回数据，不执行退款、通知等业务操作。

修改统一协议后，在仓库根目录先运行 python scripts/build_shared.py，再运行 python coze/build.py。CI 使用 --check 检查两层生成代码。更新 IDE 代码时保留服务器端密钥，不要将密钥放进仓库或导出的示例。
