"""Embeddings locales con Sentence Transformers.

Se generan en la máquina del usuario (gratis, sin API): OpenRouter no ofrece un
endpoint de embeddings fiable. Los modelos de la familia e5 esperan un prefijo
distinto para los documentos ("passage:") y para las consultas ("query:"); aquí
se aplica de forma transparente para mejorar la calidad de la recuperación.
"""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from . import config


@lru_cache(maxsize=1)
def _modelo() -> SentenceTransformer:
    """Carga el modelo una sola vez (la primera vez descarga los pesos)."""
    return SentenceTransformer(config.EMBEDDING_MODEL)


def _usa_prefijos_e5() -> bool:
    return "e5" in config.EMBEDDING_MODEL.lower()


def embed_documentos(textos: list[str]) -> list[list[float]]:
    """Vectoriza fragmentos del corpus (rol 'passage')."""
    if _usa_prefijos_e5():
        textos = [f"passage: {t}" for t in textos]
    vectores = _modelo().encode(textos, normalize_embeddings=True)
    return vectores.tolist()


def embed_consulta(texto: str) -> list[float]:
    """Vectoriza una consulta del usuario (rol 'query')."""
    if _usa_prefijos_e5():
        texto = f"query: {texto}"
    vector = _modelo().encode([texto], normalize_embeddings=True)[0]
    return vector.tolist()
