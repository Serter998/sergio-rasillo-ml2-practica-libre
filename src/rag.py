"""Recuperación semántica (RAG) sobre la base vectorial de Chroma.

Vectoriza la consulta con el mismo modelo local de embeddings y recupera los
top-k fragmentos más relevantes del corpus, devolviendo su texto y los metadatos
necesarios para citar la fuente (documento y sección).

No requiere clave de OpenRouter.
"""
from __future__ import annotations

from dataclasses import dataclass

import chromadb

from . import config, embeddings


@dataclass
class Fragmento:
    """Un fragmento recuperado del corpus, listo para citar."""

    texto: str
    documento: str
    seccion: str
    dominio: str
    archivo: str
    similitud: float  # 0..1 (mayor = más relevante)

    def cita(self) -> str:
        return f"{self.documento} › {self.seccion}"


def _abrir_coleccion():
    cliente = chromadb.PersistentClient(path=str(config.VECTORSTORE_DIR))
    try:
        return cliente.get_collection(config.COLLECTION_NAME)
    except Exception as exc:  # colección inexistente
        raise RuntimeError(
            "La base vectorial no existe todavía. Ejecuta primero la ingesta:\n"
            "    python -m src.ingesta"
        ) from exc


def recuperar(consulta: str, k: int | None = None) -> list[Fragmento]:
    """Devuelve los k fragmentos más relevantes para la consulta."""
    k = k or config.TOP_K
    coleccion = _abrir_coleccion()
    vector = embeddings.embed_consulta(consulta)
    resultado = coleccion.query(
        query_embeddings=[vector],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    fragmentos: list[Fragmento] = []
    documentos = resultado["documents"][0]
    metadatos = resultado["metadatas"][0]
    distancias = resultado["distances"][0]
    for texto, meta, dist in zip(documentos, metadatos, distancias):
        fragmentos.append(
            Fragmento(
                texto=texto,
                documento=meta.get("documento", "?"),
                seccion=meta.get("seccion", "?"),
                dominio=meta.get("dominio", "?"),
                archivo=meta.get("archivo", "?"),
                # Chroma con espacio coseno devuelve distancia = 1 - similitud.
                similitud=round(1.0 - float(dist), 3),
            )
        )
    return fragmentos
