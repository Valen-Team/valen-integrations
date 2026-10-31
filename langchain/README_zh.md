# 在 LangChain 与 LangGraph 中使用 Valen

[English](README.md)

为 LangChain 应用增加工单分流、图片检查和告警分级。写下要判断的问题，即可得到有名称的答案与概率，直接用于 LCEL、LangGraph 分支或 Agent 工具。人工复核阈值和后续动作由你的应用控制。

## 安装与首次运行

```sh
python -m pip install langchain-valen==0.1.0
```

需要 Python 3.10+，安装时会自动获取 LangChain Core 和 Valen SDK。[PyPI 包](https://pypi.org/project/langchain-valen/)

```python
from langchain_valen import ValenEvaluator

client = ValenEvaluator([
    {"name": "refund", "type": "predicate", "instructions": "客户要求退款。"}
])
print(client.invoke("我被重复扣款了，请退还多收的钱。"))
```

默认调用免费 API，无需密钥。带密钥的服务可传 `base_url`、`api_key`，也可设置 `VALEN_API_KEY` 环境变量。不要把密钥写入示例或提交到仓库。

输入支持文本、JSON，以及 `{"input": 内容, "image": 图片字节}`；一次最多一张 PNG、JPEG 或 WebP，最多 8 个问题。

## 分流与实际工作流

`ValenRouter(question, yes_at=0.7, no_at=0.3)` 对是否题返回 `yes`、`no`、`unsure`。Choice 返回选项值，Score 返回概率最高的等级（平局取靠前等级），不是对期望分数四舍五入。

安装 `langgraph` 后运行 `python -m langchain_valen.example`，即可在实际 LangGraph 中把三条合成工单分到账单、技术和人工复核。示例不执行外部业务动作。

失败会抛出异常，不会伪装为正常分支。`ValenDecisionTool` 抛出标准 `ToolException`，可使用 LangChain 的 `handle_tool_error`。Choice 必须按需要提供范围外选项，低置信度规则留在工作流中。

完整接口、异步行为和开发说明见[英文说明](README.md)。
