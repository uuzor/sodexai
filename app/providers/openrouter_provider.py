import os
import json
import logging
import datetime
import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b:free"


def get_openrouter_key() -> str | None:
    return os.getenv("OPENROUTER_API_KEY")


def get_openrouter_model() -> str:
    return os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL


def openrouter_ready() -> bool:
    return bool(get_openrouter_key())


def call_openrouter(
    messages: list[dict],
    timeout: int = 45,
    temperature: float = 0.2,
    max_tokens: int = 600,
    model: str | None = None,
) -> dict:
    """Call OpenRouter chat completions with reasoning enabled and JSON response format.

    Conservative defaults keep the request fast and the response compact:
    - low temperature (0.2) for deterministic structured output
    - bounded max_tokens (600) sized for a small JSON object with 3 forecasts
    - 45s default timeout to avoid hanging connections

    Returns the full parsed JSON envelope. Raises on any error.
    """
    key = get_openrouter_key()
    if not key:
        raise RuntimeError("Missing OPENROUTER_API_KEY environment variable")
    if model is None:
        model = get_openrouter_model()
    body = {
        "model": model,
        "messages": messages,
        "reasoning": {"enabled": True},
        "response_format": {"type": "json_object"},
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.9,
    }
    started = datetime.datetime.now()
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(body),
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        latency = int(
            (datetime.datetime.now() - started).total_seconds() * 1000
        )
        payload["_latency_ms"] = latency
        return payload
    except requests.Timeout as e:
        logging.exception(f"OpenRouter timeout after {timeout}s: {e}")
        raise RuntimeError(
            f"OpenRouter request timed out after {timeout}s — the model is taking too long to respond."
        ) from e
    except requests.HTTPError as e:
        text = ""
        status_code: int | None = None
        status = "?"
        try:
            if e.response is not None:
                status_code = e.response.status_code
                status = str(status_code)
                text = e.response.text[:300]
        except Exception:
            logging.exception("Unexpected error")
            text = ""
        # Treat 404/429 as handled per-model failures (no stack trace noise).
        if status_code in (404, 429):
            short = text.replace("\n", " ")[:180]
            logging.warning(f"OpenRouter HTTP {status} (handled): {short}")
            raise RuntimeError(f"OpenRouter HTTP {status}: {short}") from None
        logging.exception(f"OpenRouter HTTP error {status}: {e} :: {text}")
        raise RuntimeError(f"OpenRouter HTTP {status}: {text}") from e
    except requests.ConnectionError as e:
        logging.exception(f"OpenRouter connection error: {e}")
        raise RuntimeError(
            f"OpenRouter connection failed: {str(e)[:200]}"
        ) from e
    except Exception as e:
        logging.exception(f"OpenRouter request error: {e}")
        raise