# Valen for Dify

[中文](README_zh.md) · [Shared behavior](../SPEC.md)

Turn a support ticket into a clear next step: refund review, general support or human review. Valen reads text or an image and returns an answer with probabilities. Use the included workflow to try the complete routing path, then connect your own actions.

## Install

Requires **Dify 1.18.0+**. In **Integrations → Install → GitHub** (called **Plugins → Install plugin** in older layouts), enter:

```text
https://github.com/Valen-Team/valen-integrations
```

Choose release **dify-v0.1.0** and asset **valen-0.1.0.difypkg**, then install. You can also [download the package and example workflow](https://github.com/Valen-Team/valen-integrations/releases/tag/dify-v0.1.0) and use **Local package file**.

This is a GitHub-distributed community plugin; Dify Marketplace review is separate. The package is unsigned, so your Dify instance must permit unsigned community plugins. If your instance requires marketplace signatures, ask your administrator before installing. See [RELEASING.md](RELEASING.md) for administrator configuration.

Authorize Valen with the default `https://api.valen-team.workers.dev` base URL and an empty
key, or use your keyed/self-hosted endpoint. Saving checks `/v1/models`. Credentials stay
in Dify's provider credential store. Model is editable and defaults to `valen-2b`.

## Use

- **Yes/No:** input and a concrete statement; returns `probability`, `branch`, `model`.
  Defaults: yes at ≥0.7, no at ≤0.3, otherwise `unsure`.
- **Choice:** options, one per line, `value` or `value: description`; returns `choice`,
  `confidence`, `probabilities`, `branch`, `model`.
- **Score:** levels, lowest first, with the same line syntax; returns expected index `score`,
  most likely `level`, `confidence`, `probabilities`, `branch`, `model`.
- **Evaluate:** a Decisions API questions JSON array; returns `answers` and `model` in JSON.
  Use a code step for dynamic answer keys. Single-question tools expose declared variables
  directly to IF/ELSE nodes.

Install and authorize the plugin before importing
[the starter workflow](https://github.com/Valen-Team/valen-integrations/releases/download/dify-v0.1.0/support-review.yml) in Studio. The example sends
a support ticket through Yes/No and explicit refund, normal support and human review paths.
A separate failure path returns the error and original ticket. End outputs use unique
refund_, support_, review_ and failure_ prefixes, as Dify requires across all Output nodes. These are output queues;
the example performs no external business action. The optional image input accepts one file. Self-hosted Dify must configure `FILES_URL`
and `INTERNAL_FILES_URL` so plugin containers can fetch uploaded files.
The example contains no account credential ID or plugin package hash.

Failed requests produce tool errors, never a negative judgment. Configure Dify's tool error
handling and connect its failure branch. Requests retry transient failures twice, with a
120-second timeout per attempt. For persistent 429 errors wait at least a minute.
Inputs, questions and images go to the configured API; see [PRIVACY.md](PRIVACY.md).

## Upgrade

Download the new version from the same release page and install it in Plugins. Export your workflows first and keep the previous package if you need to roll back. After upgrading, run a sample ticket before reconnecting business actions.

[Build and release](RELEASING.md) · [Data handling](PRIVACY.md)
