"""Ingesta del corpus → chunking → embeddings locales → base vectorial (Chroma).

Lee los documentos markdown de data/corpus/, los trocea de forma consciente de los
encabezados (cada sección ## es una unidad), genera los embeddings en local y los
persiste en ChromaDB junto con sus metadatos (documento de origen, dominio y
sección), que son los que permiten CITAR la fuente en el veredicto.

Uso (no requiere clave de OpenRouter):
    python -m src.ingesta
"""
from __future__ import annotations

import re

import chromadb

from . import config, embeddings

# Etiqueta legible del dominio a partir del nombre de archivo.
DOMINIOS = {
    "01_principios_appcc": "Principios APPCC",
    "02_temperaturas_tiempos": "Temperaturas y tiempos",
    "03_alergenos_etiquetado": "Alérgenos y etiquetado",
    "04_higiene_manipulador": "Higiene del manipulador",
    "05_limpieza_desinfeccion": "Limpieza y desinfección",
    "06_trazabilidad": "Trazabilidad",
    "07_recepcion_almacenamiento": "Recepción y almacenamiento",
}


def _dividir_seccion_larga(texto: str) -> list[str]:
    """Subdivide una sección que excede CHUNK_SIZE en ventanas con solape,
    intentando cortar en un espacio para no partir palabras."""
    if len(texto) <= config.CHUNK_SIZE:
        return [texto]

    trozos: list[str] = []
    inicio = 0
    while inicio < len(texto):
        fin = inicio + config.CHUNK_SIZE
        if fin < len(texto):
            corte = texto.rfind(" ", inicio, fin)
            if corte <= inicio:
                corte = fin
        else:
            corte = len(texto)
        fragmento = texto[inicio:corte].strip()
        if fragmento:
            trozos.append(fragmento)
        if corte >= len(texto):
            break
        inicio = max(corte - config.CHUNK_OVERLAP, inicio + 1)
    return trozos


def trocear_documento(nombre_archivo: str, texto: str) -> list[dict]:
    """Trocea un documento markdown por secciones (##), conservando metadatos."""
    stem = nombre_archivo.replace(".md", "")
    dominio = DOMINIOS.get(stem, stem)

    titulo_doc = stem
    seccion_actual = "Introducción"
    buffer: list[str] = []
    secciones: list[tuple[str, str]] = []

    def cerrar_seccion() -> None:
        contenido = "\n".join(buffer).strip()
        if contenido:
            secciones.append((seccion_actual, contenido))

    for linea in texto.splitlines():
        if linea.startswith("Contenido didáctico"):
            continue  # omitir el aviso de cabecera
        if linea.startswith("# "):
            titulo_doc = linea[2:].strip()
            buffer = []  # descartar lo previo al título
            continue
        if linea.startswith("## "):
            cerrar_seccion()
            seccion_actual = linea[3:].strip()
            buffer = []
            continue
        buffer.append(linea)
    cerrar_seccion()

    chunks: list[dict] = []
    for idx_sec, (seccion, contenido) in enumerate(secciones):
        # Limpia espacios en blanco repetidos manteniendo párrafos.
        contenido = re.sub(r"\n{3,}", "\n\n", contenido).strip()
        for idx_sub, fragmento in enumerate(_dividir_seccion_larga(contenido)):
            chunks.append(
                {
                    "id": f"{stem}::{idx_sec}::{idx_sub}",
                    "texto": fragmento,
                    "metadatos": {
                        "documento": titulo_doc,
                        "archivo": nombre_archivo,
                        "dominio": dominio,
                        "seccion": seccion,
                    },
                    # Texto que se vectoriza: incluye documento y sección como
                    # contexto, lo que mejora la calidad de la recuperación.
                    "texto_indexado": f"{titulo_doc}. {seccion}.\n{fragmento}",
                }
            )
    return chunks


def cargar_corpus() -> list[dict]:
    """Lee y trocea todos los documentos del corpus."""
    if not config.CORPUS_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta del corpus: {config.CORPUS_DIR}"
        )
    todos: list[dict] = []
    for ruta in sorted(config.CORPUS_DIR.glob("*.md")):
        todos.extend(trocear_documento(ruta.name, ruta.read_text(encoding="utf-8")))
    if not todos:
        raise ValueError(
            f"No se encontraron documentos .md en {config.CORPUS_DIR}"
        )
    return todos


def construir_base_vectorial() -> int:
    """Genera los embeddings y (re)crea la colección de Chroma. Devuelve el nº de chunks."""
    chunks = cargar_corpus()
    print(f"Documentos troceados en {len(chunks)} chunks.")

    print(f"Generando embeddings locales (modelo: {config.EMBEDDING_MODEL})...")
    print("  (la primera vez se descargan los pesos del modelo; puede tardar)")
    vectores = embeddings.embed_documentos([c["texto_indexado"] for c in chunks])

    cliente = chromadb.PersistentClient(path=str(config.VECTORSTORE_DIR))
    # Recrea la colección desde cero para que la ingesta sea idempotente.
    try:
        cliente.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass
    coleccion = cliente.create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    coleccion.add(
        ids=[c["id"] for c in chunks],
        documents=[c["texto"] for c in chunks],
        embeddings=vectores,
        metadatas=[c["metadatos"] for c in chunks],
    )
    print(f"Base vectorial creada en: {config.VECTORSTORE_DIR}")
    print(f"Colección '{config.COLLECTION_NAME}' con {coleccion.count()} chunks.")
    return coleccion.count()


if __name__ == "__main__":
    construir_base_vectorial()
