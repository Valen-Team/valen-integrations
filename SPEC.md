# Valen integrations: shared specification

Every integration in this repository (n8n, Dify, Coze, LangChain) follows this document, so a workflow
moved from one platform to another asks the same questions and reads the same answers. Platform
directories describe only how these rules map onto their platform.

Valen makes judgments; the workflow makes decisions. An integration asks typed questions about an
input and hands back probabilities. Thresholds, branching and actions stay in the workflow, where
people can see and change them.

## 1. Connection

| Field | Default | Notes |
| --- | --- | --- |
| Base URL | `https://api.valen-team.workers.dev` | The free hosted API. Coze (coze.cn) uses the free endpoint reachable from mainland China instead (see §8). The keyed API is `https://llm-proxy.openxxlab.com`; a self-hosted `valen serve` also works. Entered with or without a trailing `/` or `/v1`; requests go to `{host}/v1/...`. The field stays editable. |
| API key | empty | Sent as `Authorization: Bearer <key>` only when set. The free API needs none. Stored as a secret. |
| Model | `valen-2b` | Free text. The hosted APIs serve `valen-0.8b`, `valen-2b` and `valen-4b`; a self-hosted server serves the name it was started with. Where a platform can load choices, it lists the IDs from `GET {host}/v1/models` that start with `valen`. |

Saving a connection checks it with `GET {host}/v1/models`.

Every request sends `User-Agent: valen-<platform>/<integration version>`, for example
`valen-n8n/0.1.0`, including the connection check, and waits up to 120 seconds for each attempt.

## 2. Request

Every integration calls `POST {host}/v1/decisions`; it is the protocol that carries images.

### 2.1 Input

| Input | Sent as `input` |
| --- | --- |
| Text | The string as given |
| JSON | The object as JSON text |
| Workflow item | The item's data as JSON text |

JSON text uses two-space indentation and keeps non-ASCII characters as they are (Python:
`json.dumps(value, indent=2, ensure_ascii=False)`; JavaScript: `JSON.stringify(value, null, 2)`).

With an image, `input` becomes one user message:

```json
[{"role": "user", "content": [
  {"type": "input_text", "text": "<the input above>"},
  {"type": "input_image", "image_url": "data:image/jpeg;base64,..."}
]}]
```

At most one image, in PNG, JPEG or WebP, sent unchanged as a base64 data URL. The MIME type comes
from the file's metadata (Dify's file object carries `mime_type`) or the `Content-Type` of its download;
another format stops the step with a message naming the three supported ones. The platforms' own image
pickers also accept GIF, SVG, HEIC and more, and the API's error for those does not name the
supported formats, so the integration checks first. The hosted API does not fetch remote image URLs, so an
integration that receives a file URL downloads it first. Coze passes an image as a URL string and an empty
optional image as `""`; an empty value means no image.

### 2.2 Questions

Each question has an **ID**, a **type**, **instructions**, and for Choice and Score its options or
levels.

| Type shown | API `type` | Extra field |
| --- | --- | --- |
| Yes/No | `predicate` | none |
| Choice | `choice` | **Options** → `choices: [{value, description}]`: one per line, `value` or `value: description` |
| Score | `score` | **Levels** → `levels: [{label, description}]`: one per line, lowest first, `label` or `label: description` |

- The ID becomes the question's `name` and the key of its answer. IDs use letters, digits and `_`,
  and are unique within a step.
- A line is split at its first `: ` (colon and space); the value or label is trimmed. Blank lines are
  ignored.
- Descriptions are optional; they help most when two options are easy to confuse. A line without one is
  sent with the value or label as its description, which every server accepts.
- **Raw JSON** mode takes the `questions` array of the Decisions API as is, for questions built by an
  earlier step.

The hosted API accepts per request 8 questions, 16 options or levels per question, 300 characters
per description and 2,000 characters of instructions. Integrations pass requests through and report
the API's `400` message, which names the limit.

## 3. Answers

| Type | Fields |
| --- | --- |
| Yes/No | `probability`: probability that the answer is yes |
| Choice | `choice`: the most likely option; `confidence`; `probabilities` by option value |
| Score | `score`: expected level index from 0; `level`: label of the most likely level, the lower one on a tie; `confidence`; `probabilities` by level label |

The API returns `answers` as a list in request order and `probabilities` as lists of
`{value or label, probability}`; integrations key them by `name`, `value` and `label`, and compute
`level` themselves. Probabilities are numbers from 0 to 1, unrounded. `model` is the response's `model_id`, or its
`model` when `model_id` is absent.

## 4. Evaluate

Evaluate asks several questions about the same input in one request and returns the answers keyed by
ID:

```json
{
  "answers": {
    "refund":  {"probability": 0.161},
    "team":    {"choice": "billing", "confidence": 0.998, "probabilities": {"billing": 0.999, "tech": 0.001}},
    "urgency": {"score": 0.9998, "level": "high", "confidence": 0.9995, "probabilities": {"low": 0.0002, "high": 0.9998}}
  },
  "model": "valen-2b"
}
```

Values are shortened here. Where a platform keeps the incoming data, the object is added to it under
`valen`; otherwise it is the step's output. Platforms whose step outputs must be declared in advance
(Dify, Coze) return it as one JSON output, for code steps and agents; their condition nodes use the
single-question tools in §5.

## 5. Single question and Route

A single-question step asks one question and returns its answer's fields from §3 at the top level,
plus `model` and `branch`:

| Type | `branch` |
| --- | --- |
| Yes/No | `yes` when `probability` ≥ **Yes at** (default 0.7); otherwise `no` when ≤ **No at** (default 0.3); otherwise `unsure` |
| Choice | The `choice` value |
| Score | The `level` label |

On Dify and Coze these are the Yes/No, Choice and Score tools, and condition nodes read `branch` or
the numbers directly. Route on n8n sends the item down the output named by `branch`, with the answer
added under `valen`; Route takes its question from form fields, so the set of outputs is fixed when the
step is set up. The LangChain router returns `branch` as the route key: LangGraph uses it in
`add_conditional_edges`, and LCEL assigns it first with `RunnablePassthrough.assign(branch=router)` so
the question is asked once.

The `unsure` branch is where review, a second question or a stronger model belongs.

## 6. Errors and retries

- `429`, `502`, `503`, `504`, connection failures and timeouts are retried twice, waiting 0.25 s then
  0.5 s, as the Valen SDKs do. A `429` that remains asks the user to wait at least a minute.
- Any other failure stops the step with the HTTP status, the API's message and the request ID when
  present: `x-request-id` from self-hosted servers, `x-llm-proxy-request-id` from the hosted APIs. The message is `error.message` (self-hosted servers) or `detail` (hosted
  APIs); a `detail` list of field errors is joined into one line.
- A failed call never produces an answer: it is never read as `no`, as the first option or as level 0.
  A platform's "continue on error" setting decides whether the run goes on; in LangChain the tool
  raises `ToolException`, and `handle_tool_error` plays that role.

## 7. Data

The integration sends the input, the image and the questions to the configured base URL, and
downloads image URLs it is given. It keeps no copy and writes no logs beyond what the platform
records for each run. How the hosted API handles requests is described in
[data handling](https://valen-team.github.io/docs/valen/api/data-handling/).

## 8. Platforms

| | n8n | Dify | Coze | LangChain |
| --- | --- | --- | --- | --- |
| Package | `@valen-team/n8n-nodes-valen` (npm) | `valen` plugin (`.difypkg`) | Coze plugin store | `langchain-valen` (PyPI) |
| Evaluate | Evaluate operation | Evaluate tool (JSON output) | Evaluate tool (JSON output) | `ValenEvaluator` runnable |
| Single question | Route operation, one output per branch | Yes/No, Choice and Score tools | Yes/No, Choice and Score tools | `ValenDecisionTool`, `ValenRouter` for `RunnableBranch` and LangGraph edges |
| Language | TypeScript, no runtime dependencies | Python 3.12, `valen-sdk` | Python in the Coze IDE | Python, `valen-sdk` |
| Release | GitHub Actions with npm provenance from `n8n/` (`repository.directory: "n8n"`), tag `n8n-v*` | PR to `langgenius/dify-plugins` | Coze store review | GitHub Actions to PyPI, tag `langchain-v*` |

Platform notes:

- **n8n**: Evaluate is the default operation and Route is an operation of the same Valen node, which
  keeps the package a single-service node under n8n's verification rules.
- **Dify**: tool outputs are declared in `output_schema` and returned with `create_variable_message`;
  IF/ELSE nodes then list `branch`, `probability` and `model`. Every tool parameter needs
  `human_description` (and `llm_description` for `llm` parameters), which the plugin SDK checks at
  start-up and `dify plugin package` does not. Provider credential defaults prefill the connection form.
- **Coze**: plugin parameters have no file type, so images arrive as URL strings. coze.cn cannot reach
  `*.workers.dev`, and image URLs hosted outside mainland China may time out, so the Coze plugin calls
  the China endpoint. A plugin is published to its space before workflows can use it, and its
  personal-information statement is "yes", since it sends user input to the Valen API.

Integrations built on `valen-sdk` pass `Valen.remote(f"{host}/v1", headers={"User-Agent": ...})`.

Each platform directory has its own README, tests and release workflow. A behaviour change starts in
this file.
