"""Cliente del LLM vía OpenRouter (U3 — APIs).

Envuelve el SDK de OpenAI apuntado a OpenRouter y añade la robustez exigida:
- Timeout por petición.
- Reintentos con backoff exponencial ante errores transitorios (límite de tasa,
  caídas de red, errores 5xx) — especialmente útil con modelos del tier gratuito.
- Mensaje claro (sin traza) cuando falta la clave.
"""
from __future__ import annotations

import time

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from . import config

# Errores que merece la pena reintentar.
ERRORES_TRANSITORIOS = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)


class LLMNoConfigurado(RuntimeError):
    """Se lanza cuando se intenta usar el LLM sin clave de OpenRouter."""


_cliente: OpenAI | None = None


def _get_cliente() -> OpenAI:
    global _cliente
    if not config.hay_api_key():
        raise LLMNoConfigurado(config.MENSAJE_FALTA_CLAVE)
    if _cliente is None:
        _cliente = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
            timeout=config.LLM_TIMEOUT,
        )
    return _cliente


def chat(messages: list[dict], tools: list | None = None,
         tool_choice: str | None = None):
    """Llama al endpoint de chat con reintentos y backoff exponencial.

    Devuelve el objeto `message` de la primera elección de la respuesta.
    """
    cliente = _get_cliente()
    kwargs: dict = {
        "model": config.LLM_MODEL,
        "temperature": config.LLM_TEMPERATURE,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice or "auto"

    ultimo_error: Exception | None = None
    for intento in range(config.LLM_MAX_REINTENTOS + 1):
        try:
            respuesta = cliente.chat.completions.create(**kwargs)
            return respuesta.choices[0].message
        except ERRORES_TRANSITORIOS as exc:
            ultimo_error = exc
            if intento == config.LLM_MAX_REINTENTOS:
                break
            espera = config.LLM_BACKOFF_BASE * (2 ** intento)
            print(
                f"  [LLM] error transitorio ({type(exc).__name__}); "
                f"reintento {intento + 1}/{config.LLM_MAX_REINTENTOS} en {espera:.0f}s..."
            )
            time.sleep(espera)
        except APIStatusError as exc:
            # Errores no transitorios (p. ej. 400/401/403): no tiene sentido reintentar.
            raise RuntimeError(
                f"Error de la API de OpenRouter ({exc.status_code}): {exc.message}"
            ) from exc

    raise RuntimeError(
        f"No se pudo contactar con el LLM tras {config.LLM_MAX_REINTENTOS} reintentos. "
        f"Último error: {ultimo_error}"
    )
