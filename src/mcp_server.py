"""Servidor MCP de Centinela APPCC (U6 — Model Context Protocol).

Expone la funcionalidad del verificador como tools MCP, de modo que cualquier
cliente MCP (por ejemplo Claude Desktop) pueda:

- `buscar_normativa`: recuperar fragmentos de la normativa por similitud (RAG).
  No requiere clave de OpenRouter.
- `verificar_cumplimiento`: emitir un veredicto estructurado completo sobre una
  situación. Requiere `OPENROUTER_API_KEY`.

Ejecución (stdio):
    python -m src.mcp_server

Configuración en Claude Desktop (claude_desktop_config.json), ver docs/mcp.md.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import config, rag, veredicto

mcp = FastMCP("centinela-appcc")


@mcp.tool()
def buscar_normativa(consulta: str, k: int = 4) -> list[dict]:
    """Busca en el corpus de seguridad alimentaria los fragmentos de normativa más
    relevantes para una consulta (recuperación semántica RAG). No requiere clave.

    Args:
        consulta: tema o situación sobre la que buscar normativa.
        k: número de fragmentos a devolver (por defecto 4).
    """
    fragmentos = rag.recuperar(consulta, k=k)
    return [
        {
            "documento": f.documento,
            "seccion": f.seccion,
            "dominio": f.dominio,
            "similitud": f.similitud,
            "texto": f.texto,
        }
        for f in fragmentos
    ]


@mcp.tool()
def verificar_cumplimiento(situacion: str) -> dict:
    """Evalúa una situación o checklist de seguridad alimentaria y devuelve un
    veredicto estructurado: estado (cumple / requiere_atencion / no_cumple),
    resumen, comprobaciones deterministas, incumplimientos, acciones correctivas
    y normas citadas con su documento de origen. Requiere OPENROUTER_API_KEY.

    Args:
        situacion: descripción en lenguaje natural de la situación a verificar.
    """
    if not config.hay_api_key():
        return {"error": "Falta OPENROUTER_API_KEY en el entorno del servidor MCP."}
    veredicto_obj = veredicto.generar_veredicto(situacion)
    return veredicto_obj.model_dump(mode="json")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
