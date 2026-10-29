# Valen for Coze

[中文](README_zh.md)

A Coze cloud plugin with four tools that implement [SPEC.md](../SPEC.md): **Yes/No**, **Choice**, **Score** and **Evaluate**. Workflow condition nodes branch on each tool's `branch` output.

coze.cn cannot reach the free endpoint on `*.workers.dev`, so the plugin calls `https://llm-proxy.openxxlab.com/v1` with an API key that lives only in the plugin code on Coze's servers. Users of the plugin need no key.

## Files

| Path | Use |
| --- | --- |
| `tools/<tool>.py` | The code to paste into each Coze IDE tool. Generated; do not edit. |
| `src/` | Sources: `common.py` (requests, retries, images, errors) and one handler per tool. |
| `build.py` | `python build.py` regenerates `tools/` from `src/`. |
| `tests/` | Offline tests: `python -m pytest tests`. |

## Set up the plugin

1. In the Coze workspace, open **Resources** → **+ Resource** → **Plugin**. Choose **Cloud plugin**, **Create in Coze IDE** and runtime **Python3**.
2. For each tool below, **Add tool** with the tool name, then:
   1. On **Metadata**, add the input parameters from the table.
   2. On **Code**, replace everything with `tools/<tool>.py` and set `API_KEY = "..."` to the plugin's Valen API key.
   3. **Test code** with sample input, then **Update output parameters** from the result.
3. **Publish** the plugin. In the personal-information statement, answer **Yes**: the plugin sends user text and images to the Valen API.
4. In a workflow, add the tool from **Resource library tools** and branch on `branch` in a condition node.

## Tools

Every tool also takes `input` (String, required: the text to judge), `image` (String, optional: an image URL; PNG, JPEG or WebP) and `model` (String, optional, default `valen-2b`).

| Tool | Own inputs | Outputs |
| --- | --- | --- |
| `yes_no` | `question` (String, required), `yes_at` (Number, default 0.7), `no_at` (Number, default 0.3) | `probability`, `branch` (`yes` / `no` / `unsure`), `model` |
| `choice` | `question` (String, required), `options` (String, required: one per line, `value` or `value: description`) | `choice`, `confidence`, `probabilities`, `branch` (the choice), `model` |
| `score` | `question` (String, required), `levels` (String, required: one per line, lowest first, `label` or `label: description`) | `score`, `level`, `confidence`, `probabilities`, `branch` (the level), `model` |
| `evaluate` | `questions` (String, required: the Decisions API `questions` array as JSON) | `answers` (keyed by question name), `model` |

Test input for `choice`, for example:

```json
{"input": "I was charged twice and want my money back.", "question": "Which team should handle this?", "options": "billing: Payments and charges\ntech: Software errors\naccount"}
```

## Updating

Edit `src/`, run `python build.py` and the tests, then paste the changed `tools/<tool>.py` into the IDE, keeping the `API_KEY` line, and publish a new version.
