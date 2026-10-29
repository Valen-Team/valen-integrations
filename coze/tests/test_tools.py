"""Offline checks of the generated Coze tools against SPEC.md; Coze's runtime and typings modules are stubbed."""
import base64
import importlib.util
import io
import json
import sys
import types
import urllib.error
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 16
GIF = b"GIF89a" + b"\0" * 16


def load(tool):
    runtime = types.ModuleType("runtime")
    runtime.Args = type("Args", (), {"__class_getitem__": classmethod(lambda cls, _: cls)})
    typing = types.ModuleType(f"typings.{tool}.{tool}")
    typing.Input = typing.Output = dict
    sys.modules.update({"runtime": runtime, "typings": types.ModuleType("typings"),
                        f"typings.{tool}": types.ModuleType(f"typings.{tool}"), f"typings.{tool}.{tool}": typing})
    spec = importlib.util.spec_from_file_location(f"coze_{tool}", TOOLS / f"{tool}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(module, answers, monkeypatch, image_bytes=b"", **fields):
    sent = []

    def fetch(url, data=None, headers=None, timeout=120, what="Valen API"):
        if data is None:
            return "application/octet-stream", image_bytes
        sent.append(json.loads(data))
        return "application/json", json.dumps({"answers": answers, "model": "Valen-2B", "model_id": "valen-2b"}).encode()

    monkeypatch.setattr(module, "_fetch", fetch)
    args = types.SimpleNamespace(input=types.SimpleNamespace(input="I was charged twice.", **fields))
    return module.handler(args), sent


@pytest.mark.parametrize("probability,branch", [(0.7, "yes"), (0.5, "unsure"), (0.3, "no")])
def test_yes_no_branches_on_default_thresholds(probability, branch, monkeypatch):
    result, sent = run(load("yes_no"), [{"type": "predicate", "name": "q", "probability": probability}],
                       monkeypatch, question="Refund?", image="")
    assert result == {"probability": probability, "branch": branch, "model": "valen-2b"}
    assert sent[0]["input"] == "I was charged twice." and sent[0]["model"] == "valen-2b"


def test_yes_no_custom_thresholds_include_zero(monkeypatch):
    result, _ = run(load("yes_no"), [{"type": "predicate", "name": "q", "probability": 0.05}],
                    monkeypatch, question="Refund?", yes_at=0.9, no_at=0)
    assert result["branch"] == "unsure"


def test_choice_lines_probabilities_and_branch(monkeypatch):
    answer = {"type": "choice", "name": "q", "choice": "billing", "confidence": 0.9,
              "probabilities": [{"value": "billing", "probability": 0.95}, {"value": "tech", "probability": 0.05}]}
    result, sent = run(load("choice"), [answer], monkeypatch, question="Which team?",
                       options="billing: Payments and charges\n\ntech")
    assert sent[0]["questions"][0]["choices"] == [{"value": "billing", "description": "Payments and charges"},
                                                   {"value": "tech", "description": "tech"}]
    assert result == {"choice": "billing", "confidence": 0.9, "probabilities": {"billing": 0.95, "tech": 0.05},
                      "branch": "billing", "model": "valen-2b"}


def test_score_level_is_most_likely_and_lower_on_tie(monkeypatch):
    answer = {"type": "score", "name": "q", "score": 0.5, "confidence": 0.2,
              "probabilities": [{"value": 0, "label": "low", "probability": 0.5},
                                {"value": 1, "label": "high", "probability": 0.5}]}
    result, sent = run(load("score"), [answer], monkeypatch, question="How urgent?", levels="low\nhigh: Today")
    assert sent[0]["questions"][0]["levels"][1] == {"label": "high", "description": "Today"}
    assert (result["level"], result["branch"], result["probabilities"]) == ("low", "low", {"low": 0.5, "high": 0.5})


def test_evaluate_keys_answers_by_name(monkeypatch):
    answers = [{"type": "predicate", "name": "refund", "probability": 0.16}]
    result, sent = run(load("evaluate"), answers, monkeypatch,
                       questions=json.dumps([{"name": "refund", "type": "predicate", "instructions": "Refund?"}]))
    assert result == {"answers": {"refund": {"probability": 0.16}}, "model": "valen-2b"}
    assert sent[0]["questions"][0]["name"] == "refund"


def test_images_are_sniffed_and_unsupported_formats_stop(monkeypatch):
    answers = [{"type": "predicate", "name": "q", "probability": 0.9}]
    _, sent = run(load("yes_no"), answers, monkeypatch, image_bytes=PNG, question="Animals?",
                  image="https://example.test/a.png")
    part = sent[0]["input"][0]["content"][1]
    assert part["image_url"] == "data:image/png;base64," + base64.b64encode(PNG).decode()
    with pytest.raises(ValueError, match="PNG, JPEG or WebP"):
        run(load("yes_no"), answers, monkeypatch, image_bytes=GIF, question="Animals?", image="https://example.test/a.gif")


def error(status, body, headers=None):
    return urllib.error.HTTPError("https://example.test", status, "error", headers or {}, io.BytesIO(body))


def test_error_messages_follow_spec():
    module = load("yes_no")
    nested = error(400, b'{"error": {"message": "At most 8 questions"}}', {"x-llm-proxy-request-id": "p-1"})
    assert module._message(nested, "Valen API") == "Valen API HTTP 400: At most 8 questions (request p-1)"
    listed = error(422, b'{"detail": [{"msg": "field required"}, {"msg": "too long"}]}')
    assert module._message(listed, "Valen API") == "Valen API HTTP 422: field required; too long"
    assert module._message(error(429, b"{}"), "Valen API").endswith("(wait at least a minute)")


def test_retries_then_reports(monkeypatch):
    module = load("yes_no")
    calls = []

    def urlopen(request, timeout):
        calls.append(request)
        raise error(503, b'{"detail": "busy"}')

    monkeypatch.setattr(module.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    with pytest.raises(RuntimeError, match="HTTP 503: busy"):
        module._fetch("https://example.test/v1/decisions", b"{}")
    assert len(calls) == 3
    assert calls[0].headers["User-agent"] == "valen-coze/0.1.0"
