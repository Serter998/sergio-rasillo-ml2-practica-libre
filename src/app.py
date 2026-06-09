"""Interfaz web tipo PANEL DE INSPECCIÓN (Fase 3, U-extra).

No es un chat: es un verificador. El inspector describe una situación o pega un
checklist, pulsa «Verificar» y obtiene un veredicto estructurado con semáforo,
comprobaciones deterministas, normas citadas (con su documento) y acciones
correctivas.

NiceGUI mantiene el estado del formulario sin reejecutar el script en cada
interacción (modelo orientado a eventos).

Uso (PowerShell):
    python -m src.app
Luego abre http://localhost:8080 en el navegador.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Permite ejecutar tanto «python -m src.app» como «python src/app.py».
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nicegui import run, ui  # noqa: E402

from src import config, veredicto  # noqa: E402

# Aspecto del semáforo según el estado del veredicto.
ESTADOS_UI = {
    "cumple": {"texto": "CUMPLE", "icono": "check_circle", "color": "#2e7d32", "fondo": "#e8f5e9"},
    "requiere_atencion": {"texto": "REQUIERE ATENCIÓN", "icono": "warning", "color": "#f57f17", "fondo": "#fff8e1"},
    "no_cumple": {"texto": "NO CUMPLE", "icono": "cancel", "color": "#c62828", "fondo": "#ffebee"},
}

EJEMPLOS = [
    "Hemos cocinado pechuga de pollo y el termómetro marca 60 °C en el centro.",
    "Una tarta de nata se ha quedado en la encimera a 22 °C durante 3 horas.",
    "Plato de gambas rebozadas con salsa de soja y mostaza: ¿qué hay que declarar?",
    "El camión de refrigerados llega con el producto a 9 °C en la recepción.",
    "El arcón congelador está a −20 °C para conservar carne congelada.",
]


def cabecera() -> None:
    with ui.header().classes("items-center justify-between").style(
        "background:#1d3557"
    ):
        with ui.row().classes("items-center gap-2"):
            ui.icon("verified_user", size="28px").style("color:white")
            with ui.column().classes("gap-0"):
                ui.label("Centinela APPCC").classes("text-white text-h6 leading-none")
                ui.label("Verificador de cumplimiento en seguridad alimentaria").classes(
                    "text-white text-caption opacity-80"
                )
        ui.label("Panel de inspección").classes("text-white text-caption opacity-70")


def aviso_sin_clave() -> None:
    with ui.card().classes("w-full").style("background:#fff8e1; border-left:6px solid #f57f17"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("key_off", size="24px").style("color:#f57f17")
            ui.label("Falta la clave de OpenRouter").classes("text-subtitle1 text-weight-bold")
        ui.label(
            "El verificador necesita una clave para evaluar situaciones. Las pruebas de "
            "recuperación (RAG) funcionan sin clave."
        )
        ui.markdown(
            "1. Copia `.env.example` a `.env`.\n"
            "2. Consigue una clave gratis en **https://openrouter.ai/keys**.\n"
            "3. Pégala en la línea `OPENROUTER_API_KEY=` del `.env` y reinicia la app."
        ).classes("text-caption")


def render_veredicto(contenedor: ui.column, v: veredicto.Veredicto, consulta: str) -> None:
    contenedor.clear()
    est = ESTADOS_UI.get(v.estado.value, ESTADOS_UI["requiere_atencion"])
    with contenedor:
        # Semáforo / badge de estado.
        with ui.card().classes("w-full").style(
            f"background:{est['fondo']}; border-left:8px solid {est['color']}"
        ):
            with ui.row().classes("items-center gap-3 no-wrap"):
                ui.icon(est["icono"], size="40px").style(f"color:{est['color']}")
                with ui.column().classes("gap-0"):
                    ui.label(est["texto"]).classes("text-h5 text-weight-bold").style(
                        f"color:{est['color']}"
                    )
                    if v.tipo_consulta:
                        ui.label(f"Tipo de consulta: {v.tipo_consulta}").classes("text-caption opacity-70")
            if v.resumen:
                ui.label(v.resumen).classes("text-body1 q-mt-sm")

        # Comprobaciones deterministas (resultado de las tools).
        if v.comprobaciones:
            with ui.card().classes("w-full"):
                ui.label("Comprobaciones (herramientas deterministas)").classes(
                    "text-subtitle1 text-weight-bold"
                )
                for c in v.comprobaciones:
                    if c.cumple is True:
                        icono, color = "check_circle", "#2e7d32"
                    elif c.cumple is False:
                        icono, color = "cancel", "#c62828"
                    else:
                        icono, color = "info", "#1d3557"
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        ui.icon(icono, size="20px").style(f"color:{color}")
                        ui.label(f"[{c.herramienta}] {c.resultado}").classes("text-body2")

        # Incumplimientos y acciones correctivas, lado a lado.
        with ui.row().classes("w-full gap-4 items-stretch"):
            if v.incumplimientos:
                with ui.card().classes("col").style("border-left:6px solid #c62828"):
                    ui.label("Incumplimientos detectados").classes("text-subtitle1 text-weight-bold")
                    for inc in v.incumplimientos:
                        with ui.row().classes("items-start gap-2 no-wrap"):
                            ui.icon("error_outline", size="18px").style("color:#c62828")
                            ui.label(inc).classes("text-body2")
            if v.acciones_correctivas:
                with ui.card().classes("col").style("border-left:6px solid #2e7d32"):
                    ui.label("Acciones correctivas").classes("text-subtitle1 text-weight-bold")
                    for acc in v.acciones_correctivas:
                        with ui.row().classes("items-start gap-2 no-wrap"):
                            ui.icon("arrow_forward", size="18px").style("color:#2e7d32")
                            ui.label(acc).classes("text-body2")

        # Normas citadas con su documento de origen.
        if v.normas_citadas:
            with ui.card().classes("w-full"):
                ui.label("Normas citadas").classes("text-subtitle1 text-weight-bold")
                for n in v.normas_citadas:
                    with ui.card().classes("w-full q-my-xs").style("background:#f5f7fa"):
                        with ui.row().classes("items-center gap-2 no-wrap"):
                            ui.icon("menu_book", size="18px").style("color:#1d3557")
                            ui.label(f"{n.documento} › {n.seccion}").classes(
                                "text-weight-medium text-body2"
                            )
                        if n.texto:
                            ui.label(f"“{n.texto}”").classes("text-caption text-italic q-pl-md")


@ui.page("/")
def pagina_principal() -> None:
    ui.query("body").style("background-color:#eef2f7")
    cabecera()

    with ui.column().classes("w-full max-w-screen-md mx-auto q-pa-md gap-4"):
        if not config.hay_api_key():
            aviso_sin_clave()

        # ── Panel de entrada ──────────────────────────────────────
        with ui.card().classes("w-full"):
            ui.label("Situación a verificar").classes("text-subtitle1 text-weight-bold")
            entrada = (
                ui.textarea(
                    placeholder="Describe una situación operativa o pega un checklist…"
                )
                .props("outlined autogrow")
                .classes("w-full")
            )
            with ui.row().classes("items-center gap-2 wrap"):
                ui.label("Ejemplos:").classes("text-caption opacity-70")
                for ej in EJEMPLOS:
                    ui.button(
                        ej[:34] + "…",
                        on_click=lambda e=ej: entrada.set_value(e),
                    ).props("flat dense no-caps size=sm color=primary")

            boton = ui.button("Verificar cumplimiento", icon="gavel").props(
                "color=primary unelevated"
            )

        # ── Panel de resultados ───────────────────────────────────
        resultados = ui.column().classes("w-full gap-4")

        async def verificar() -> None:
            consulta = (entrada.value or "").strip()
            if not consulta:
                ui.notify("Escribe primero una situación a verificar.", type="warning")
                return
            if not config.hay_api_key():
                ui.notify("Falta la clave de OpenRouter (ver aviso superior).", type="negative")
                return

            resultados.clear()
            boton.disable()
            with resultados:
                with ui.row().classes("items-center gap-2"):
                    ui.spinner(size="lg")
                    ui.label("Verificando… recuperando normativa y consultando al LLM.")
            try:
                v = await run.io_bound(veredicto.generar_veredicto, consulta)
                render_veredicto(resultados, v, consulta)
            except Exception as exc:  # noqa: BLE001 — la UI no debe romperse
                resultados.clear()
                with resultados:
                    with ui.card().classes("w-full").style("border-left:6px solid #c62828"):
                        ui.label("No se pudo generar el veredicto").classes(
                            "text-subtitle1 text-weight-bold"
                        )
                        ui.label(str(exc)).classes("text-body2")
            finally:
                boton.enable()

        boton.on_click(verificar)


ui.run(title="Centinela APPCC", favicon="🛡️", reload=False, port=8080)
