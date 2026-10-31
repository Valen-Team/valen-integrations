<p align="center"><img src="assets/valen-mark.png" width="96" alt="Valen"></p>

# 把 Valen 接入你的工作流

[English](README.md)

让每条工单、每张图片、每个告警都有明确的下一步。向 Valen 提一个具体问题，获取答案与概率，再连接到你的工作流：把明确结果自动分流，把是否题的中间结果交给人工复核。

## 选择你的平台

| 你正在使用 | 从这里开始 | 安装后可以做什么 |
| --- | --- | --- |
| **n8n，自托管** | [npm 安装](https://www.npmjs.com/package/@valen-team/n8n-nodes-valen) · [上手指南](n8n/README_zh.md) | 添加一个节点，用具名输出口分流，保留原始工单，并导入现成示例 |
| **LangChain / LangGraph** | [PyPI 安装](https://pypi.org/project/langchain-valen/) · [上手指南](langchain/README_zh.md) | 直接接入 Runnable、条件分支和 Agent 工具 |
| **Dify** | [下载插件与示例工作流](https://github.com/Valen-Team/valen-integrations/releases/tag/dify-v0.1.0) · [上手指南](dify/README_zh.md) | 用四个可视化工具搭建判断与分流，无需配置大模型供应商 |
| **扣子 Coze.cn** | [打开插件商店](https://www.coze.cn/store/plugin/7702606163640074283) · [上手指南](coze/README_zh.md) | 把云端工具加入智能体或工作流，无需自行填写 API 密钥 |

默认托管服务无需密钥。Dify 需要 1.18.0+，且实例允许安装未签名社区插件，当前通过 GitHub 公开分发。n8n 包用于自托管实例，尚未获得 n8n Cloud 认证。

## 先试一条工单

1. 安装对应平台的集成。
2. 打开该平台的工单分流示例，保留默认连接。
3. 输入：**“我被重复扣款了，请退还多收的钱。”**

判断问题写成 **“客户要求退款。”** 是否题会返回概率和分支：概率 ≥0.7 为 `yes`，≤0.3 为 `no`，中间为 `unsure`。把三个出口接到退款队列、普通支持和人工复核，再为请求失败保留单独出口。

示例先返回分流数据，便于查看结果，之后再连接实际业务动作。各平台指南提供具体安装步骤与示例。

## 为工作流选择合适的问题

| 工具 | 例如 | 用途 |
| --- | --- | --- |
| **Yes/No 是否** | “客户要求退款。” | 自动处理明确结果，把中间区间交给复核 |
| **Choice 单选** | 账单、技术支持，还是其他请求？ | 从你提供的候选项中选择具名出口 |
| **Score 打分** | 低、中、高紧急程度？ | 获取等级分布，安排处理优先级 |
| **Evaluate 多项评估** | 同时判断意图、处理团队和紧急程度 | 一次读取输入，返回多个有名称的答案 |

支持文本及一张 PNG、JPEG 或 WebP 图片。Choice 和 Score 会保留完整概率分布，你可以按业务需要添加复核规则。概率是模型估计，请根据自己的数据和误判成本调整阈值；调用失败会报错，不会被当成否定答案。

## 接入自己的场景

- [写出清晰的问题](https://valen-team.github.io/docs/valen/question-design/)
- [理解概率与阈值](https://valen-team.github.io/docs/valen/probabilities/)
- [查看应用示例](https://valen-team.github.io/cookbook/)
- [了解数据处理](https://valen-team.github.io/docs/valen/api/data-handling/)

各集成都支持配置服务地址。密钥保存在平台凭据中；扣子云插件由服务器管理连接。

维护者入口：[统一行为](SPEC.md)、[n8n](n8n/RELEASING.md)、[Dify](dify/RELEASING.md)、[LangChain](langchain/RELEASING.md)、[扣子](coze/README_zh.md#维护插件)。

[MIT 许可证](LICENSE)
