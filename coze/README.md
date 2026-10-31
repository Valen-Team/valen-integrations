# Valen for Coze

[中文](README_zh.md)

Route support tickets, inspect an image, or prioritize an alert with the public Valen plugin. Ask a concrete question and use its answer and probabilities in your agent or workflow.

## Add the plugin

1. Open [Valen in the Coze plugin store](https://www.coze.cn/store/plugin/7702606163640074283).
2. Choose **插件工具**, select a tool, then **添加到我的智能体**. You can also find **Valen 万澜** when adding a plugin node to a workflow.
3. Start with `yes_no`: set `input` to a support ticket and `question` to `The customer requests a refund.` Leave the optional fields at their defaults.

No API key is needed. The tool returns `probability`, `branch` (`yes`, `no`, `unsure`) and `model`. Connect a workflow condition to `branch` to route results. Use a separate error path for failed requests.

**Choice** picks one of your named options; **Score** evaluates ordered levels; **Evaluate** asks several questions together. An optional `image` accepts a downloadable PNG, JPEG or WebP URL. Inputs and images are sent to the Valen service; see [data handling](PRIVACY.md).

[Build the support-review workflow](examples/support-review/recipe.json) with the included code nodes and sample inputs. This is a manual setup recipe; it is not an importable Coze DSL. The example returns queue data and does not issue refunds or send messages.

## Maintain the plugin

The following setup is for maintainers creating their own plugin. Users of the public store plugin can start above.

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

### Rebuild the support workflow

The creator’s [working example](https://www.coze.cn/work_flow?workflow_id=7702424956361900058&space_id=7702094046076157987) requires access to its workspace. Other users can recreate the graph with the [configuration recipe](examples/support-review/recipe.json), four Code-node sources in that directory, and the test inputs in [cases.json](examples/support-review/cases.json).

The recipe is **not an importable Coze DSL export**. On the tested account, native workflow export opens a paid-plan prompt; no subscription was purchased.

1. Create a workflow. Add a required String `input` to Start. Add optional String `image`, `question` and `model`, plus Number `yesAt` and `noAt`. Leave the image empty; set the other defaults to `The customer requests a refund.`, `valen-2b`, `0.7` and `0.3` respectively. Expand each parameter to set its default.
2. Add the published Valen `yes_no` tool. Bind its inputs to Start, mapping `yes_at` to `yesAt` and `no_at` to `noAt`. Set the overall timeout to 420 seconds, workflow retries to none, and error handling to **Execute exception flow**. The plugin already retries transient request failures.
3. Connect the normal output to a Selector: `branch == yes` → Refund queue, `branch == no` → Support queue, otherwise → Review queue. Each destination is a Code node using its matching `.ts` file. Bind `input` to Start and `branch`, `probability`, `model` to `yes_no`. Declare only `result` as a generic Object output.
4. Connect the plugin’s separate error port to Request failure. Use `failure.ts`, binding Start’s `input` and the plugin’s **errorBody Object**. It returns the original input and Coze’s error details without a normal answer or probability.
5. Connect all four destination nodes to one Variable Merge. Use one Object group, `Group1`, with all four `result` values and the strategy **first nonempty value**. Connect the merge to End and return `result = Group1`.
6. Run every case before publishing. In the Coze test panel, JSON mode wraps workflow parameters in `{"_input": {...}}`; `cases.json` contains these exact envelopes. The unsure case widens the middle band to exercise routing; it is not an accuracy benchmark. The image case changes the judgment while retaining the example’s queue names. These nodes return data and perform no refund, notification or other business action.

When changing the shared protocol, run python scripts/build_shared.py from the repository root before python coze/build.py. CI checks both generated layers using --check. Keep the server-side key when updating code in the IDE; do not put it into the repository or exported examples.
