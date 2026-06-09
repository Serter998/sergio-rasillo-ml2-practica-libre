r"""Prueba manual del pipeline RAG SIN LLM.

Recupera y muestra los fragmentos más relevantes del corpus para una consulta.
Sirve para comprobar, sin necesidad de clave de OpenRouter, que la ingesta y la
recuperación semántica funcionan correctamente.

Uso (PowerShell):
    python scripts\probar_retrieval.py "carne de pollo cocinada a 60 grados en el centro"
    python scripts\probar_retrieval.py            # usa consultas de ejemplo
"""
from __future__ import annotations

import sys
from pathlib import Path

# La consola de Windows usa cp1252 por defecto y no puede imprimir caracteres
# como «≤» o «°»; forzamos UTF-8 para que la salida no falle.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Permite importar el paquete src/ al ejecutar el script directamente.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import rag  # noqa: E402

CONSULTAS_EJEMPLO = [
    "¿A qué temperatura hay que cocinar el pollo en el centro?",
    "tengo mayonesa fuera de la nevera desde hace tres horas",
    "qué alérgenos lleva un plato con gambas y salsa de soja",
    "cómo descongelar carne de forma segura",
]


def mostrar(consulta: str) -> None:
    print("=" * 78)
    print(f"CONSULTA: {consulta}")
    print("=" * 78)
    fragmentos = rag.recuperar(consulta)
    for i, f in enumerate(fragmentos, 1):
        print(f"\n[{i}] similitud={f.similitud}  ·  {f.cita()}  ({f.dominio})")
        texto = f.texto if len(f.texto) <= 280 else f.texto[:280] + "…"
        print(f"    {texto}")
    print()


def main() -> None:
    consultas = sys.argv[1:] or CONSULTAS_EJEMPLO
    for consulta in consultas:
        mostrar(consulta)


if __name__ == "__main__":
    main()
