<p align="center"><img src="assets/valen-mark.png" width="96" alt="Valen"></p>

# Valen for your workflows

[中文](README_zh.md)

Give every ticket, image and alert a clear next step. Ask Valen a concrete question, get an answer with probabilities, and connect it to your workflow. Route clear results automatically and send intermediate Yes/No results to human review.

## Choose your platform

| You use | Start here | What you get |
| --- | --- | --- |
| **n8n, self-hosted** | [Install from npm](https://www.npmjs.com/package/@valen-team/n8n-nodes-valen) · [Guide](n8n/README.md) | One node with named routing outputs, preserved input items and a ready-to-import support workflow |
| **LangChain / LangGraph** | [Install from PyPI](https://pypi.org/project/langchain-valen/) · [Guide](langchain/README.md) | Runnables, conditional routing and an agent tool that fit your existing application |
| **Dify** | [Download plugin and starter workflow](https://github.com/Valen-Team/valen-integrations/releases/tag/dify-v0.1.0) · [Guide](dify/README.md) | Four visual tools and a complete ticket-review workflow; no model-provider setup needed |
| **Coze.cn** | [Open the plugin store](https://www.coze.cn/store/plugin/7702606163640074283) · [Guide](coze/README.md) | Four cloud tools you can add to an agent or workflow without supplying an API key |

The default hosted API needs no key. Dify requires 1.18.0+ and an instance that allows unsigned community plugins; its public package is distributed through GitHub. The n8n package is for self-hosted installations and is not verified for n8n Cloud.

## Try ticket routing

1. Install the integration for your platform.
2. Open its support-routing example and use the default connection.
3. Enter a ticket such as **“I was charged twice. Please refund the duplicate charge.”**

Ask **“The customer requests a refund.”** Yes/No tools return a probability and a branch: `yes` at 0.7 or above, `no` at 0.3 or below, otherwise `unsure`. Connect these outputs to your refund queue, general support and human review. Keep request failures on their own error path.

The examples return routing data so you can inspect the result before connecting business actions. Each platform guide includes the install steps and example.

## Ask the question your workflow needs

| Tool | Example | Use the result to… |
| --- | --- | --- |
| **Yes/No** | “The customer requests a refund.” | Route clear answers and review the middle band |
| **Choice** | Billing, technical support, or another request? | Pick a named destination from your candidates |
| **Score** | Low, medium or high urgency? | Prioritize work using ordered levels and their probabilities |
| **Evaluate** | Check intent, team and urgency together | Get several named answers from one input |

Use text or one PNG, JPEG or WebP image. Choice and Score return the full distribution, so you can add your own review rules. Probabilities are model estimates; set thresholds for your own data and the cost of a wrong decision. API failures are errors, never negative judgments.

## Make it yours

- [Write clear questions](https://valen-team.github.io/docs/valen/question-design/)
- [Understand probabilities and thresholds](https://valen-team.github.io/docs/valen/probabilities/)
- [Explore working recipes](https://valen-team.github.io/cookbook/)
- [Understand data handling](https://valen-team.github.io/docs/valen/api/data-handling/)

Each integration supports a configurable endpoint. Keep credentials in the platform's credential store; the Coze cloud plugin manages its connection on the server.

For maintainers: [shared behavior](SPEC.md), [n8n](n8n/RELEASING.md), [Dify](dify/RELEASING.md), [LangChain](langchain/RELEASING.md), [Coze](coze/README.md#maintain-the-plugin).

[MIT License](LICENSE)
