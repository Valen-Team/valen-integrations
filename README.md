<p align="center"><img src="assets/valen-mark.png" width="96" alt="Valen"></p>

# Valen integrations

[中文](README_zh.md)

Use Valen in workflow and agent platforms. Ask typed questions about text or an image, get probabilities back, and branch on them: route tickets, screen content, triage alerts.

| Platform | Directory | Package | Status |
| --- | --- | --- | --- |
| [Dify](https://dify.ai) | [`dify/`](dify/) | `valen` plugin | In development |
| [Coze](https://www.coze.cn) | [`coze/`](coze/) | Coze plugin store | Planned |
| [n8n](https://n8n.io) | [`n8n/`](n8n/) | `@valen-team/n8n-nodes-valen` | Planned |
| [LangChain](https://www.langchain.com) | [`langchain/`](langchain/) | `langchain-valen` | Planned |

Every integration offers the same two actions:

- **Evaluate**: ask up to 8 Yes/No, Choice or Score questions about one input and read every answer with its probabilities.
- **Route**: ask one question and send the item to the branch its answer picks, with an `unsure` branch for Yes/No answers between the thresholds.

[SPEC.md](SPEC.md) defines the fields, outputs, branches and errors that all of them share. The integrations call the [Valen API](https://valen-team.github.io/docs/valen/api/); the free hosted endpoint needs no key.

## Learn more

- [Write questions that work](https://valen-team.github.io/docs/valen/question-design/)
- [Reading probabilities](https://valen-team.github.io/docs/valen/probabilities/)
- [Cookbook](https://valen-team.github.io/cookbook/)

## License

[MIT](LICENSE).
