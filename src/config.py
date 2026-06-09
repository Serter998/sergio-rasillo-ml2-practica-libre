"""Configuración central del proyecto.

Carga las variables de entorno desde .env y centraliza rutas, parámetros del
pipeline RAG y la configuración del LLM. Importante: este módulo NO falla si falta
la clave de OpenRouter; solo expone si está disponible, de modo que las fases 0-1
(corpus, ingesta, retrieval) se puedan ejecutar sin clave.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Rutas del proyecto ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"

# Carga el .env de la raíz del proyecto (si existe).
load_dotenv(PROJECT_ROOT / ".env")

# ── Embeddings locales (Sentence Transformers) ────────────────────
# Multilingüe apto para español. Los modelos de la familia e5 requieren prefijos
# "query:"/"passage:" (se gestionan en src/embeddings.py).
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

# ── Parámetros de chunking ────────────────────────────────────────
# Troceado consciente de encabezados (## secciones); las secciones más largas se
# subdividen en ventanas de CHUNK_SIZE caracteres con CHUNK_OVERLAP de solape.
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# ── Recuperación ──────────────────────────────────────────────────
TOP_K = 4
COLLECTION_NAME = "centinela_appcc"

# ── LLM vía OpenRouter (cliente OpenAI-compatible) ────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b:free")
LLM_TEMPERATURE = 0.1

# Parámetros de robustez de la API (fase 2).
LLM_TIMEOUT = 60          # segundos
LLM_MAX_REINTENTOS = 4    # nº de reintentos ante errores transitorios
LLM_BACKOFF_BASE = 2.0    # segundos; backoff exponencial: base * 2**intento


def hay_api_key() -> bool:
    """Indica si hay clave de OpenRouter configurada."""
    return bool(OPENROUTER_API_KEY)


MENSAJE_FALTA_CLAVE = (
    "Falta la clave de OpenRouter.\n"
    "1) Copia el archivo .env.example a .env\n"
    "       copy .env.example .env\n"
    "2) Consigue una clave gratuita en https://openrouter.ai/keys\n"
    "3) Pega la clave en la línea  OPENROUTER_API_KEY=  del archivo .env\n\n"
    "Nota: el corpus, la ingesta y la prueba de retrieval funcionan SIN clave."
)
