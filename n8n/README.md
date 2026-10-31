# Valen for n8n

[中文](README_zh.md)

Route support tickets to the right team, flag images for review, or triage alerts with one Valen node. Ask a concrete question and connect the named outputs to your next steps. Yes/No routing includes an `unsure` output for human review.

Your original fields, binary data and item links stay with each item. Answers and probabilities appear under `valen` (replacing an existing field of that name).

## Install

In **self-hosted n8n**, open **Settings → Community nodes → Install** and enter:

```text
@valen-team/n8n-nodes-valen
```

Install the package, then add a node and search for **Valen**. Requires Node.js 22.16+; compatible with the tested n8n 2.45.6. This community package is not verified for n8n Cloud.

For a manual installation, run as the user that runs n8n:

```sh
mkdir -p ~/.n8n/nodes
cd ~/.n8n/nodes
# Run npm init -y first if this directory has no package.json.
npm install @valen-team/n8n-nodes-valen@0.1.0 --omit=dev --legacy-peer-deps
```

Restart n8n after manual installation. In Docker, use the persistent `/home/node/.n8n/nodes` directory as the `node` user. [npm package](https://www.npmjs.com/package/@valen-team/n8n-nodes-valen) · [n8n installation guide](https://docs.n8n.io/integrations/community-nodes/installation/manual-install/)

## Connection

Create a **Valen API** credential. The default free endpoint needs no API key. Saving/testing the credential checks `/v1/models`. You can also use `https://llm-proxy.openxxlab.com` with your key, or a self-hosted server. A trailing `/v1` is optional. Keep the key in the credential, not in workflow parameters.

Choose **Model Name or ID** from the live model list. For a self-hosted model whose ID doesn't start with `valen`, switch this field to Expression and enter a literal expression such as `{{ "my-model" }}`.

## Try the included workflow

Import [`examples/support-routing.json`](examples/support-routing.json) through n8n's **Import from File** menu. Select your Valen credential on **Route tickets**, then execute the workflow. It creates three synthetic tickets and routes them to Billing, Technical or Human review. Request failures go to the separate Request failure output. No external actions run. Inspect `valen.branch`, `valen.probabilities` and `valen.model` on each output. Predictions can vary by model; the example is not an assertion of accuracy.

The review option describes out-of-scope requests explicitly: Choice always selects one of the supplied options. Use a separate Yes/No or workflow condition when a probability gate is needed; Choice and Score Route have no automatic uncertainty gate.

## Operations

- **Evaluate**: supply a Decisions API JSON array of 1–8 questions. Each needs a unique `name`, `type`, and `instructions`. Choice adds `choices: [{value, description}]`; Score adds `levels: [{label, description}]`. Results appear under `valen.answers.<name>`.
- **Route / Yes/No**: write one statement/question. Outputs are `yes` (probability ≥ 0.7), `no` (≤ 0.3), and `unsure` (between), with editable thresholds. Require `0 ≤ No at < Yes at ≤ 1`.
- **Route / Choice**: enter 2–16 distinct options, one per line, `value` or `value: description`. Each creates a named port. Outputs use the selected choice.
- **Route / Score**: enter ordered levels in the same format. Route uses the most probable level, with the earlier level winning a tie. It does not round the expected score.

Route options and question type are fixed configuration, so ports stay the same for every item. Questions and input can use per-item expressions. Text is sent unchanged; JSON and Input Item use two-space JSON with Unicode preserved.

For **Image Binary Field**, enter the binary property from an earlier node, for example `data`. File bytes are validated as PNG, JPEG or WebP and sent inline with the input. Fetch remote files with an earlier n8n HTTP Request node. This node accepts one image, not a URL or video.

## Errors and data

HTTP 429/502/503/504 and supported network failures retry twice, after 0.25 and 0.5 seconds. Each attempt times out after 120 seconds. Other errors stop immediately, including malformed or incomplete answers. API errors include HTTP status and request ID when supplied.

Use **On Error → Continue (using error output)** to send failures to n8n's separate Error port, as the example does. Failed items carry `error` and `details.input` (the original input), without a normal answer or branch. **Stop Workflow** stops the run instead. The legacy **Continue (using regular output)** option sends failures to `unsure` for Yes/No or the first port otherwise; use the separate Error port for action routing.

Inputs, images and questions are sent to the configured endpoint. The node adds no logs or storage; n8n may retain execution data. See [Valen data handling](https://valen-team.github.io/docs/valen/api/data-handling/).

## Build from source

Use Node.js 22.16+ and run `npm ci --ignore-scripts`, `npm test`, then `npm pack` in this directory. See [RELEASING.md](RELEASING.md) for maintenance and [SPEC.md](../SPEC.md) for shared behavior.
