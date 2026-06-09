"""Orquestación del veredicto (núcleo del sistema).

Integra todas las unidades:
  1. Clasifica la consulta con few-shot (U2) y obtiene una búsqueda optimizada.
  2. Recupera la normativa aplicable con RAG (U5).
  3. Llama al LLM (U1/U3), que decide invocar tools deterministas (U4) en bucle.
  4. Construye un VEREDICTO ESTRUCTURADO validado con Pydantic.

El resultado es un objeto `Veredicto`: estado (semáforo), resumen, comprobaciones
(de las tools, deterministas), normas citadas (con documento de origen),
incumplimientos y acciones correctivas.
"""
from __future__ import annotations

import json
from enum import Enum

from pydantic import BaseModel, Field, ValidationError

from . import llm, prompts, rag, tools

MAX_RONDAS_TOOLS = 4


# ── Modelos del veredicto ─────────────────────────────────────────
class Estado(str, Enum):
    cumple = "cumple"
    no_cumple = "no_cumple"
    requiere_atencion = "requiere_atencion"


class NormaCitada(BaseModel):
    documento: str
    seccion: str
    texto: str = ""


class Comprobacion(BaseModel):
    herramienta: str
    entrada: dict = Field(default_factory=dict)
    resultado: str = ""
    cumple: bool | None = None


class Veredicto(BaseModel):
    estado: Estado = Estado.requiere_atencion
    resumen: str = ""
    incumplimientos: list[str] = Field(default_factory=list)
    acciones_correctivas: list[str] = Field(default_factory=list)
    normas_citadas: list[NormaCitada] = Field(default_factory=list)
    comprobaciones: list[Comprobacion] = Field(default_factory=list)
    tipo_consulta: str = ""


# ── Utilidades internas ───────────────────────────────────────────
def _assistant_a_dict(msg) -> dict:
    """Serializa el mensaje del asistente (incluyendo tool_calls) para el historial."""
    d: dict = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return d


def _extraer_json(texto: str) -> dict | None:
    """Extrae el primer objeto JSON de un texto (tolera ``` y texto alrededor)."""
    if not texto:
        return None
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio == -1 or fin == -1 or fin <= inicio:
        return None
    try:
        return json.loads(texto[inicio:fin + 1])
    except json.JSONDecodeError:
        return None


def _formato_contexto(fragmentos: list[rag.Fragmento]) -> str:
    bloques = []
    for i, f in enumerate(fragmentos, 1):
        bloques.append(
            f"[{i}] (Documento: {f.documento} | Sección: {f.seccion})\n{f.texto}"
        )
    return "\n\n".join(bloques)


def _frag_a_norma(f: rag.Fragmento) -> NormaCitada:
    texto = f.texto if len(f.texto) <= 200 else f.texto[:200] + "…"
    return NormaCitada(documento=f.documento, seccion=f.seccion, texto=texto)


def clasificar(consulta: str) -> dict:
    """Clasifica la consulta (few-shot). Si falla, degrada con valores por defecto."""
    messages = (
        [{"role": "system", "content": prompts.SISTEMA_CLASIFICACION}]
        + prompts.FEWSHOT_CLASIFICACION
        + [{"role": "user", "content": prompts.plantilla_clasificacion(consulta)}]
    )
    try:
        msg = llm.chat(messages)
        datos = _extraer_json(msg.content or "")
    except Exception:
        datos = None
    if not isinstance(datos, dict):
        return {"tipo_consulta": "escenario", "dominios": [], "consulta_busqueda": consulta}
    datos.setdefault("consulta_busqueda", consulta)
    datos.setdefault("tipo_consulta", "escenario")
    datos.setdefault("dominios", [])
    return datos


def _construir_veredicto(datos, comprobaciones, fragmentos, clasif, texto_bruto) -> Veredicto:
    tipo = clasif.get("tipo_consulta", "")
    citas_fallback = [_frag_a_norma(f) for f in fragmentos[:2]]

    if not isinstance(datos, dict):
        resumen = "No se pudo estructurar el veredicto automáticamente."
        if texto_bruto:
            resumen += " Respuesta del modelo: " + texto_bruto[:300]
        return Veredicto(
            estado=Estado.requiere_atencion,
            resumen=resumen,
            comprobaciones=comprobaciones,
            normas_citadas=citas_fallback,
            tipo_consulta=tipo,
        )

    normas = []
    for n in datos.get("normas_citadas") or []:
        if isinstance(n, dict):
            normas.append(
                NormaCitada(
                    documento=str(n.get("documento", "")),
                    seccion=str(n.get("seccion", "")),
                    texto=str(n.get("texto", "")),
                )
            )

    try:
        veredicto = Veredicto(
            estado=datos.get("estado", "requiere_atencion"),
            resumen=str(datos.get("resumen", "")),
            incumplimientos=[str(x) for x in (datos.get("incumplimientos") or [])],
            acciones_correctivas=[str(x) for x in (datos.get("acciones_correctivas") or [])],
            normas_citadas=normas,
            comprobaciones=comprobaciones,
            tipo_consulta=tipo,
        )
    except ValidationError:
        veredicto = Veredicto(
            estado=Estado.requiere_atencion,
            resumen=str(datos.get("resumen", "")) or "Veredicto incompleto.",
            comprobaciones=comprobaciones,
            normas_citadas=normas or citas_fallback,
            tipo_consulta=tipo,
        )

    if not veredicto.normas_citadas:
        veredicto.normas_citadas = citas_fallback
    return veredicto


# ── Función principal ─────────────────────────────────────────────
def generar_veredicto(consulta: str, k: int | None = None) -> Veredicto:
    """Genera el veredicto estructurado para una situación o checklist."""
    clasif = clasificar(consulta)
    consulta_busqueda = clasif.get("consulta_busqueda") or consulta
    fragmentos = rag.recuperar(consulta_busqueda, k=k)
    contexto = _formato_contexto(fragmentos)

    messages = [
        {"role": "system", "content": prompts.SISTEMA_VEREDICTO},
        {"role": "user", "content": prompts.plantilla_usuario(consulta, contexto)},
    ]

    comprobaciones: list[Comprobacion] = []
    contenido_final: str | None = None

    for _ in range(MAX_RONDAS_TOOLS):
        msg = llm.chat(messages, tools=tools.TOOLS_SCHEMA, tool_choice="auto")
        messages.append(_assistant_a_dict(msg))
        if not msg.tool_calls:
            contenido_final = msg.content or ""
            break
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            resultado = tools.ejecutar(tc.function.name, args)
            comprobaciones.append(
                Comprobacion(
                    herramienta=tc.function.name,
                    entrada=args,
                    resultado=str(resultado.get("mensaje", resultado)),
                    cumple=resultado.get("cumple"),
                )
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                }
            )

    # Si agotó las rondas sin texto final, pide el JSON explícitamente.
    if not contenido_final:
        messages.append(
            {"role": "user", "content": "Devuelve AHORA el veredicto en JSON, sin texto adicional."}
        )
        contenido_final = llm.chat(messages).content or ""

    datos = _extraer_json(contenido_final)
    if datos is None:
        messages.append(
            {"role": "user",
             "content": "Tu respuesta no era JSON válido. Devuelve SOLO el objeto JSON del veredicto."}
        )
        datos = _extraer_json(llm.chat(messages).content or "")

    return _construir_veredicto(datos, comprobaciones, fragmentos, clasif, contenido_final)
