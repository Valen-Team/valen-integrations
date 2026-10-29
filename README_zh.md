<p align="center"><img src="assets/valen-mark.png" width="96" alt="Valen"></p>

# Valen 生态集成

[English](README.md)

在工作流和智能体平台中使用 Valen：对文本或图片提出有类型的问题，拿回概率，再按答案分支，用于工单分流、内容审核、告警分级等场景。

| 平台 | 目录 | 包 | 状态 |
| --- | --- | --- | --- |
| [Dify](https://dify.ai) | [`dify/`](dify/) | `valen` 插件 | 开发中 |
| [扣子 Coze](https://www.coze.cn) | [`coze/`](coze/) | 扣子插件商店 | 开发中 |
| [n8n](https://n8n.io) | [`n8n/`](n8n/) | `@valen-team/n8n-nodes-valen` | 计划中 |
| [LangChain](https://www.langchain.com) | [`langchain/`](langchain/) | `langchain-valen` | 计划中 |

每个集成都提供同样两种操作：

- **Evaluate（评估）**：对同一输入提出最多 8 个是否、单选或打分问题，读取每个答案及其概率。
- **Route（分流）**：提一个问题，按答案把数据送到对应分支；是否题的概率落在两个阈值之间时进入 `unsure` 分支。

[SPEC.md](SPEC.md) 规定了所有集成共用的字段、输出、分支和错误处理。集成调用 [Valen API](https://valen-team.github.io/zh-Hans/docs/valen/api/)；免费托管端点无需 key。

## 了解更多

- [写出有效的问题](https://valen-team.github.io/zh-Hans/docs/valen/question-design/)
- [读懂概率](https://valen-team.github.io/zh-Hans/docs/valen/probabilities/)
- [Cookbook](https://valen-team.github.io/zh-Hans/cookbook/)

## 许可证

[MIT](LICENSE)。
