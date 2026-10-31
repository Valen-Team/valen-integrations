# LangChain Valen

[中文](README_zh.md)

Add ticket routing, image checks and structured judgments to your LangChain app. Valen returns named answers and probabilities you can use directly in LCEL, agent tools and LangGraph conditional edges. Keep the routing rules and review thresholds in your application.

## Install

```sh
python -m pip install langchain-valen==0.1.0
```

[View on PyPI](https://pypi.org/project/langchain-valen/)

Requires Python 3.10+, `langchain-core` 1.x and `valen-sdk` 0.3.x. The wheel does not include model weights. LangGraph examples additionally need `python -m pip install 'langgraph>=1,<2'`.

## Evaluate

```python
from langchain_valen import ValenEvaluator

evaluate = ValenEvaluator([
    {"name": "refund", "type": "predicate",
     "instructions": "The customer requests a refund."},
])
result = evaluate.invoke("I was charged twice. Please refund the duplicate charge.")
print(result["answers"]["refund"]["probability"])
```

The default free API needs no key. For a keyed server, pass `base_url` and `api_key` or set `VALEN_API_KEY`. A trailing `/v1` is optional. `model` defaults to `valen-2b`; self-hosted names work too. Each call uses the SDK's 120-second timeout per attempt and two retries for supported transient failures; `timeout` and `max_retries` are configurable.

Input can be text, a JSON object/array, or an envelope `{"input": ..., "image": image_bytes}`. Use the envelope for structured evidence containing a field named `input`. Images must be PNG, JPEG or WebP bytes, one per request. Download URLs yourself before invoking; this prevents hidden network fetches in the runnable.

Evaluate returns `{"answers": {question_name: answer}, "model": resolved_model_id}`. Choice answers include `choice`, `confidence`, and candidate probabilities; Score includes expected `score`, most likely `level`, confidence and probabilities. Probabilities are retained without rounding.

## Route once in LCEL

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_valen import ValenRouter

router = ValenRouter({
    "name": "refund", "type": "predicate",
    "instructions": "The customer requests a refund.",
}, yes_at=0.7, no_at=0.3)
chain = RunnablePassthrough.assign(branch=router)
print(chain.invoke({"input": "Please refund my order."}))
```

The router returns `yes`, `no` or `unsure`. Require `0 ≤ no_at < yes_at ≤ 1`. Choice returns the selected candidate value; Score returns the most probable level (earlier level on ties). Choice must have an explicit outside-scope candidate when none may fit. Choice and Score have no automatic uncertainty gate; use an Evaluator and your own rule if you need one.

`invoke`, `batch`, `ainvoke` and runnable composition use LangChain's interfaces. Async calls use its executor bridge around the synchronous SDK client. A supplied `client=` is caller-owned and must support `predict(payload)`; do not share a non-thread-safe local client across concurrent batches.

## LangGraph

[`examples/support_routing.py`](examples/support_routing.py) builds a real graph with billing, technical and review destinations, then runs three synthetic tickets:

```sh
python -m langchain_valen.example
```

Use `router` directly in `builder.add_conditional_edges("judge", router, branch_map)`. The example makes no external business actions. Its predictions are a demonstration, not an accuracy guarantee.

## Agent tool and failures

```python
from langchain_valen import ValenDecisionTool

tool = ValenDecisionTool(evaluator=evaluate)
print(tool.invoke({"input": "Please refund the duplicate charge."}))
```

The tool exposes a text-input schema and returns the same named answers. It raises `ToolException` on failure, so LangChain's `handle_tool_error` policy works. Evaluators and routers raise errors directly; failures never become a branch or a probability. Invalid questions, thresholds, incomplete responses and unsupported image formats fail explicitly.

The integration adds no storage or logs. Evidence and questions go to your configured endpoint; LangChain tracing and endpoint retention settings still apply. See [Valen data handling](https://valen-team.github.io/docs/valen/api/data-handling/).

## Development

Run the root tests with the `test` extras installed. Tests exercise the real SDK against a local fixture server, real LangGraph edges, LCEL composition and tool error handling; fixtures do not measure model accuracy. Run the example separately for live inference. Shared validation is generated from `shared/protocol.py`; update it with `python scripts/build_shared.py` before building.
