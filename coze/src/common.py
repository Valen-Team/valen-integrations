import base64
import json
import time
import urllib.error
import urllib.request

from runtime import Args
from typings.TOOL.TOOL import Input, Output

# Paste the plugin's Valen API key here in the Coze IDE only; it stays on Coze's servers.
API_KEY = ""
BASE_URL = "https://llm-proxy.openxxlab.com/v1"
USER_AGENT = "valen-coze/0.1.0"
RETRYABLE = (429, 502, 503, 504)


def _message(error, what):
    """HTTP status, the API's message and the request ID, per SPEC §6."""
    body = error.read()
    request_id = error.headers.get("x-request-id") or error.headers.get("x-llm-proxy-request-id")
    try:
        result = json.loads(body)
        detail = result.get("error", result.get("detail")) if isinstance(result, dict) else result
        if isinstance(detail, dict):
            detail = detail.get("message", detail)
        if isinstance(detail, list):
            detail = "; ".join(str(item.get("msg", item)) if isinstance(item, dict) else str(item) for item in detail)
    except ValueError:
        detail = body[:200].decode("utf-8", "replace")
    text = f"{what} HTTP {error.code}: {detail}"
    if error.code == 429:
        text += " (wait at least a minute)"
    return text + (f" (request {request_id})" if request_id else "")


def _fetch(url, data=None, headers=None, timeout=120, what="Valen API"):
    """GET or POST with two retries for rate limits, overload and connection failures."""
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.headers.get_content_type(), response.read()
        except urllib.error.HTTPError as error:
            if error.code not in RETRYABLE or attempt == 2:
                raise RuntimeError(_message(error, what)) from None
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == 2:
                raise RuntimeError(f"{what} unreachable: {error}") from None
        time.sleep(0.25 * 2**attempt)


def _image_type(data, header):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError(f"The image is {header}; Valen accepts PNG, JPEG or WebP images")


def _evidence(text, image_url):
    """Text alone, or one user message with the text and the image as a data URL. Coze sends no image as ""."""
    if not image_url:
        return text
    header, data = _fetch(image_url, timeout=60, what="Image download")
    url = f"data:{_image_type(data, header)};base64," + base64.b64encode(data).decode("ascii")
    return [{"role": "user", "content": [{"type": "input_text", "text": text},
                                         {"type": "input_image", "image_url": url}]}]


def _ask(args, questions):
    """POST /v1/decisions and return (answers, model)."""
    i = args.input
    body = {"model": getattr(i, "model", None) or "valen-2b",
            "input": _evidence(i.input, getattr(i, "image", None)), "questions": questions}
    headers = {"Content-Type": "application/json", **({"Authorization": "Bearer " + API_KEY} if API_KEY else {})}
    _, data = _fetch(BASE_URL + "/decisions", json.dumps(body, ensure_ascii=False).encode("utf-8"), headers)
    result = json.loads(data)
    return result["answers"], result.get("model_id") or result.get("model")


def _lines(text):
    """`value` or `value: description` per line; a missing description repeats the value (SPEC §2.2)."""
    pairs = []
    for line in (text or "").splitlines():
        if line.strip():
            value, _, description = line.partition(": ")
            pairs.append((value.strip(), description.strip() or value.strip()))
    return pairs


def _answer(answer):
    """One API answer as the SPEC §3 fields."""
    if answer["type"] == "predicate":
        return {"probability": answer["probability"]}
    if answer["type"] == "choice":
        return {"choice": answer["choice"], "confidence": answer.get("confidence"),
                "probabilities": {p["value"]: p["probability"] for p in answer["probabilities"]}}
    top = max(answer["probabilities"], key=lambda p: (p["probability"], -p["value"]))
    return {"score": answer["score"], "level": top["label"], "confidence": answer.get("confidence"),
            "probabilities": {p["label"]: p["probability"] for p in answer["probabilities"]}}
