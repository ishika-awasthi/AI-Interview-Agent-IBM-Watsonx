"""
WatsonX client — wraps ibm-watsonx-ai ModelInference for IBM Granite.

Reads credentials from environment variables (populated by python-dotenv):
  WATSONX_API_KEY    — IBM Cloud IAM API key
  WATSONX_PROJECT_ID — WatsonX project UUID
  WATSONX_URL        — service endpoint, e.g. https://us-south.ml.cloud.ibm.com
"""

import logging
import os
import time
from collections.abc import Callable

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.wml_client_error import ApiRequestFailure

logger = logging.getLogger(__name__)

# ── Model identifier ──────────────────────────────────────────────────────────

GRANITE_MODEL_ID: str = os.getenv("MODEL_ID", "ibm/granite-4-h-small")

# ── Generation parameters ─────────────────────────────────────────────────────

MAX_NEW_TOKENS: int = 1024
TEMPERATURE: float = 0.7
TOP_P: float = 0.9

# ── Retry settings for 429 rate-limit errors ─────────────────────────────────

_MAX_RETRIES: int = 5
_BASE_DELAY: int = 4  # seconds; doubles each attempt → 4, 8, 16, 32, 64 s


def build_client() -> ModelInference:
    """Instantiate a ModelInference client authenticated via IAM API key.

    Reads WATSONX_API_KEY, WATSONX_PROJECT_ID, and WATSONX_URL from the
    environment.

    Raises:
        ValueError: When one or more required environment variables are absent.
    """
    api_key = os.environ.get("WATSONX_API_KEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url = os.environ.get("WATSONX_URL")

    missing = [
        k
        for k, v in {
            "WATSONX_API_KEY": api_key,
            "WATSONX_PROJECT_ID": project_id,
            "WATSONX_URL": url,
        }.items()
        if not v
    ]

    if missing:
        raise ValueError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )

    credentials = Credentials(url=url, api_key=api_key)

    params = {
        GenParams.MAX_NEW_TOKENS: MAX_NEW_TOKENS,
        GenParams.TEMPERATURE: TEMPERATURE,
        GenParams.TOP_P: TOP_P,
    }

    return ModelInference(
        model_id=GRANITE_MODEL_ID,
        credentials=credentials,
        project_id=project_id,
        params=params,
    )


def _chat_via_api(
    model: ModelInference,
    messages: list[dict[str, str]],
) -> str:
    """Send *messages* via model.chat() — available in ibm-watsonx-ai >= ~1.2."""
    response = model.chat(messages=messages)
    return response["choices"][0]["message"]["content"]


def _chat_via_generate_text(model: ModelInference, prompt: str) -> str:
    """Fallback for older SDKs without model.chat().

    Wraps *prompt* in Granite 4 chat tokens and calls generate_text().
    Granite 4 uses the ``<|start_of_role|>`` format.
    """
    formatted = (
        f"<|start_of_role|>user<|end_of_role|>{prompt}<|end_of_text|>"
        f"<|start_of_role|>assistant<|end_of_role|>"
    )
    return model.generate_text(prompt=formatted)


def generate(
    model: ModelInference,
    prompt: str,
    on_retry: Callable[[int, int, int], None] | None = None,
) -> str:
    """Send *prompt* to the Granite 4 chat model and return the reply text.

    ibm/granite-4-h-small is a chat model — it needs structured chat messages,
    not a bare string prompt (which returns empty output).

    Tries model.chat() first (newer SDK). Falls back to a Granite-4-formatted
    generate_text() call for older SDK versions that lack model.chat().

    Retries up to _MAX_RETRIES times with exponential back-off on 429 errors.

    Args:
        model:    The ModelInference client returned by build_client().
        prompt:   The user-facing text to send to the model.
        on_retry: Optional callback invoked before each retry sleep with
                  signature ``(attempt, max_retries, wait_seconds)``, useful
                  for updating a progress UI.

    Returns:
        The model's reply as a plain string.

    Raises:
        RuntimeError: When the rate-limit is not resolved after _MAX_RETRIES
                      attempts.
        ApiRequestFailure: For non-429 API errors (re-raised immediately).
    """
    messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
    delay = _BASE_DELAY
    last_error: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            if hasattr(model, "chat"):
                text = _chat_via_api(model, messages)
            else:
                text = _chat_via_generate_text(model, prompt)

            logger.info("attempt=%d response: %.300s", attempt, repr(text))
            return text

        except ApiRequestFailure as exc:
            # Only retry on rate-limit (429); re-raise anything else immediately.
            if "429" in str(exc) or "consumption_limit_reached" in str(exc):
                last_error = exc
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "Rate-limited — retrying in %ds (attempt %d/%d).",
                        delay,
                        attempt,
                        _MAX_RETRIES,
                    )
                    if on_retry:
                        on_retry(attempt, _MAX_RETRIES, delay)
                    time.sleep(delay)
                    delay *= 2
            else:
                raise

    raise RuntimeError(
        f"WatsonX is rate-limiting after {_MAX_RETRIES} attempts. "
        "Please wait a minute and try again."
    ) from last_error
