"""Tools deterministas para las comprobaciones CUANTITATIVAS (U4).

El LLM decide cuándo invocarlas (function calling), pero el cálculo lo hace este
código, no el modelo: así el veredicto se apoya en datos fiables y no en
alucinación. Los umbrales coinciden con el corpus didáctico (data/corpus).
"""
from __future__ import annotations

import re
import unicodedata

# ── Umbrales estándar (ver data/corpus/02_temperaturas_tiempos.md) ─
UMBRALES_TEMPERATURA = {
    "refrigeracion": {"limite": 4.0, "operador": "<=", "etiqueta": "refrigeración (≤ 4 °C)"},
    "congelacion": {"limite": -18.0, "operador": "<=", "etiqueta": "congelación (≤ −18 °C)"},
    "cocinado": {"limite": 75.0, "operador": ">=", "etiqueta": "cocinado en núcleo (≥ 75 °C)"},
    "mantenimiento_caliente": {"limite": 65.0, "operador": ">=", "etiqueta": "mantenimiento en caliente (≥ 65 °C)"},
}
ZONA_PELIGRO_MIN = 5.0
ZONA_PELIGRO_MAX = 65.0
TIEMPO_MAX_ZONA_PELIGRO_MIN = 120  # 2 horas

# 14 alérgenos de declaración obligatoria → términos habituales que los delatan.
ALERGENOS = {
    "Cereales con gluten": ["gluten", "trigo", "centeno", "cebada", "avena", "espelta",
                            "kamut", "harina", "pan", "pasta", "pan rallado", "rebozado",
                            "rebozada", "empanado", "empanada", "seitan"],
    "Crustáceos": ["crustaceo", "gamba", "langostino", "cangrejo", "marisco", "cigala",
                   "langosta", "nécora", "buey de mar", "quisquilla"],
    "Huevos": ["huevo", "clara de huevo", "yema", "mayonesa", "tortilla", "merengue", "ovoproducto"],
    "Pescado": ["pescado", "merluza", "bacalao", "atun", "salmon", "anchoa", "boqueron",
                "sardina", "lubina", "dorada", "salsa worcester"],
    "Cacahuetes": ["cacahuete", "mani", "manteca de cacahuete"],
    "Soja": ["soja", "tofu", "edamame", "salsa de soja", "lecitina de soja", "tempeh"],
    "Leche": ["leche", "queso", "mantequilla", "nata", "yogur", "lactosa", "crema", "cuajada", "kefir"],
    "Frutos de cáscara": ["almendra", "avellana", "nuez", "nueces", "anacardo", "pistacho",
                          "macadamia", "pacana", "marañon"],
    "Apio": ["apio"],
    "Mostaza": ["mostaza"],
    "Granos de sésamo": ["sesamo", "tahini", "tahin", "gomasio"],
    "Dióxido de azufre y sulfitos": ["sulfito", "dioxido de azufre", "metabisulfito", "e-220"],
    "Altramuces": ["altramuz", "lupino", "harina de altramuz"],
    "Moluscos": ["molusco", "mejillon", "almeja", "calamar", "pulpo", "ostra", "sepia",
                 "berberecho", "vieira", "caracol", "chipiron", "navaja"],
}


def _norm(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar de forma robusta."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    return sin_tildes


# ── Tools ─────────────────────────────────────────────────────────
def comprobar_temperatura(valor: float, tipo: str) -> dict:
    """Comprueba si una temperatura cumple el umbral estándar de su operación."""
    clave = _norm(tipo).replace(" ", "_").replace("-", "_")
    if clave not in UMBRALES_TEMPERATURA:
        return {
            "herramienta": "comprobar_temperatura",
            "error": (
                f"Tipo de operación no reconocido: '{tipo}'. "
                f"Use uno de: {', '.join(UMBRALES_TEMPERATURA)}."
            ),
        }
    u = UMBRALES_TEMPERATURA[clave]
    cumple = valor <= u["limite"] if u["operador"] == "<=" else valor >= u["limite"]
    return {
        "herramienta": "comprobar_temperatura",
        "tipo": clave,
        "valor_medido_c": valor,
        "umbral_c": u["limite"],
        "criterio": f"{u['operador']} {u['limite']} °C",
        "etiqueta": u["etiqueta"],
        "cumple": cumple,
        "mensaje": (
            f"{valor} °C {'CUMPLE' if cumple else 'NO CUMPLE'} el umbral de {u['etiqueta']}."
        ),
    }


def evaluar_tiempo_zona_peligro(temperatura: float, minutos: float) -> dict:
    """Evalúa si un alimento ha estado demasiado tiempo en la zona de peligro (5–65 °C)."""
    en_zona = ZONA_PELIGRO_MIN <= temperatura <= ZONA_PELIGRO_MAX
    if not en_zona:
        return {
            "herramienta": "evaluar_tiempo_zona_peligro",
            "temperatura_c": temperatura,
            "minutos": minutos,
            "en_zona_peligro": False,
            "cumple": True,
            "limite_min": TIEMPO_MAX_ZONA_PELIGRO_MIN,
            "mensaje": (
                f"{temperatura} °C está fuera de la zona de peligro "
                f"({ZONA_PELIGRO_MIN:g}–{ZONA_PELIGRO_MAX:g} °C); el tiempo no es crítico."
            ),
        }
    cumple = minutos <= TIEMPO_MAX_ZONA_PELIGRO_MIN
    return {
        "herramienta": "evaluar_tiempo_zona_peligro",
        "temperatura_c": temperatura,
        "minutos": minutos,
        "en_zona_peligro": True,
        "cumple": cumple,
        "limite_min": TIEMPO_MAX_ZONA_PELIGRO_MIN,
        "mensaje": (
            f"A {temperatura} °C (zona de peligro), {minutos:g} min "
            f"{'CUMPLE' if cumple else 'SUPERA'} el límite de "
            f"{TIEMPO_MAX_ZONA_PELIGRO_MIN} min."
        ),
    }


def buscar_alergeno(texto: str) -> dict:
    """Detecta, en un texto libre, posibles alérgenos de declaración obligatoria."""
    norm = _norm(texto)
    detectados: dict[str, list[str]] = {}
    for alergeno, terminos in ALERGENOS.items():
        encontrados = [
            t for t in terminos
            # \b…s?\b admite el plural simple (p. ej. "gamba" casa con "gambas").
            if re.search(rf"\b{re.escape(_norm(t))}s?\b", norm)
        ]
        if encontrados:
            detectados[alergeno] = encontrados
    return {
        "herramienta": "buscar_alergeno",
        "texto_analizado": texto,
        "alergenos_detectados": list(detectados.keys()),
        "terminos_coincidentes": detectados,
        "mensaje": (
            "Posibles alérgenos: " + ", ".join(detectados)
            if detectados else "No se detectaron alérgenos de declaración obligatoria."
        ),
    }


# ── Esquemas para function calling (formato OpenAI) ───────────────
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "comprobar_temperatura",
            "description": (
                "Comprueba si una temperatura medida cumple el umbral estándar de "
                "seguridad alimentaria según la operación."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "valor": {"type": "number", "description": "Temperatura medida en grados Celsius."},
                    "tipo": {
                        "type": "string",
                        "enum": list(UMBRALES_TEMPERATURA.keys()),
                        "description": (
                            "Operación: 'refrigeracion' (≤4 °C), 'congelacion' (≤−18 °C), "
                            "'cocinado' (núcleo ≥75 °C) o 'mantenimiento_caliente' (≥65 °C)."
                        ),
                    },
                },
                "required": ["valor", "tipo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluar_tiempo_zona_peligro",
            "description": (
                "Evalúa si un alimento ha permanecido demasiado tiempo en la zona de "
                "peligro (5–65 °C). El límite seguro es 120 minutos acumulados."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "temperatura": {"type": "number", "description": "Temperatura del alimento en °C."},
                    "minutos": {"type": "number", "description": "Minutos que ha estado a esa temperatura."},
                },
                "required": ["temperatura", "minutos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_alergeno",
            "description": (
                "Detecta en un texto (ingredientes, receta o descripción de un plato) "
                "posibles alérgenos de declaración obligatoria."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Texto con ingredientes o descripción del plato."},
                },
                "required": ["texto"],
            },
        },
    },
]

_DISPATCH = {
    "comprobar_temperatura": comprobar_temperatura,
    "evaluar_tiempo_zona_peligro": evaluar_tiempo_zona_peligro,
    "buscar_alergeno": buscar_alergeno,
}


def ejecutar(nombre: str, argumentos: dict) -> dict:
    """Ejecuta la tool indicada con sus argumentos; nunca lanza excepción al modelo."""
    funcion = _DISPATCH.get(nombre)
    if funcion is None:
        return {"error": f"Herramienta desconocida: {nombre}"}
    try:
        return funcion(**argumentos)
    except TypeError as exc:
        return {"error": f"Argumentos inválidos para {nombre}: {exc}"}
