# Valen for Dify

[Simplified Chinese](readme/README_zh_Hans.md)

Turn a support ticket into a clear next step, inspect an image, or prioritize an alert. Valen answers concrete questions with probabilities that your workflow can use directly. Keep intermediate Yes/No results on a human-review path and failed requests on a separate error path.

## Setup

Requires Dify 1.18.0 or newer. Install the Valen tool plugin, then authorize its provider:

1. Keep the default Base URL, `https://api.valen-team.workers.dev`.
2. Leave the API key empty for the free hosted API.
3. Save the connection and add a Valen tool to your workflow.

You can also configure `https://llm-proxy.openxxlab.com` with your API key or a trusted self-hosted Valen endpoint. The plugin connects to `/v1/models` and `/v1/decisions`. Keep the key in Dify provider credentials.

The [GitHub release](https://github.com/Valen-Team/valen-integrations/releases/tag/dify-v0.1.1) provides the community package for instances that allow unsigned plugins. In Dify, use **Integrations → Install → Local Package File** (called **Plugins → Install plugin** in older layouts).

## Try a support ticket

Add **Yes/No** and enter:

- **Input:** `I was charged twice. Please refund the duplicate charge.`
- **Question:** `The customer requests a refund.`

The tool returns `probability`, `branch` and `model`. With default thresholds, `branch` is `yes` at 0.7 or above, `no` at 0.3 or below, and `unsure` between them. Connect an IF/ELSE node to these values to choose a refund-review queue, general support or human review. The example returns routing data; your workflow controls business actions.

[Download the starter workflow](https://github.com/Valen-Team/valen-integrations/releases/download/dify-v0.1.1/support-review.yml), install and authorize Valen, then import it in Studio. It includes all three routes and a separate request-failure output.

## Tools

- **Yes/No:** judge one statement and return its probability and routing branch.
- **Choice:** select from your named options and return the full probability distribution. Enter one `value: description` per line, including an outside-scope option when needed.
- **Score:** describe ordered levels from lowest to highest and read the expected index, most likely level and distribution.
- **Evaluate:** ask multiple named questions about the same input in one request.

Each tool accepts text and an optional PNG, JPEG or WebP image. Choose a model ID; the default is `valen-2b`. Probabilities are estimates, so choose review rules for your own application. Request failures raise errors and never become negative answers.

## Privacy and support

Input, questions and optional images go to the configured API. Dify file URLs are downloaded through its plugin SDK. The plugin adds no storage or logs; Dify execution history and endpoint policies still apply. Read [PRIVACY.md](PRIVACY.md) before sending private content.

[Source code](https://github.com/Valen-Team/valen-integrations/tree/main/dify) · [Support and issues](https://github.com/Valen-Team/valen-integrations/issues)

Contact: liuziyu77@sjtu.edu.cn
