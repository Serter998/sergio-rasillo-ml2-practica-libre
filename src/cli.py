"""Interfaz de línea de comandos del verificador (HITO de la Fase 2).

No es un chat: recibe UNA situación (o checklist) y emite UN veredicto estructurado.

Uso (PowerShell):
    python -m src.cli "el pollo se ha cocinado a 60 grados en el centro"
    python -m src.cli            # pregunta la situación por teclado
"""
from __future__ import annotations

import sys

# La consola de Windows usa cp1252; forzamos UTF-8 para imprimir °, ≤, emojis, etc.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from src import config, veredicto  # noqa: E402
from src.llm import LLMNoConfigurado  # noqa: E402

SEMAFORO = {
    "cumple": "🟢 CUMPLE",
    "requiere_atencion": "🟡 REQUIERE ATENCIÓN",
    "no_cumple": "🔴 NO CUMPLE",
}


def imprimir_veredicto(v: veredicto.Veredicto, consulta: str) -> None:
    linea = "═" * 70
    print("\n" + linea)
    print(f"  VEREDICTO:  {SEMAFORO.get(v.estado.value, v.estado.value)}")
    print(linea)
    print(f"\nSituación evaluada: {consulta}")
    if v.tipo_consulta:
        print(f"Tipo de consulta:   {v.tipo_consulta}")

    print(f"\n▶ Resumen\n  {v.resumen}")

    if v.comprobaciones:
        print("\n▶ Comprobaciones (herramientas deterministas)")
        for c in v.comprobaciones:
            marca = "·" if c.cumple is None else ("✓" if c.cumple else "✗")
            print(f"  {marca} [{c.herramienta}] {c.resultado}")

    if v.incumplimientos:
        print("\n▶ Incumplimientos detectados")
        for inc in v.incumplimientos:
            print(f"  • {inc}")

    if v.acciones_correctivas:
        print("\n▶ Acciones correctivas")
        for acc in v.acciones_correctivas:
            print(f"  → {acc}")

    if v.normas_citadas:
        print("\n▶ Normas citadas")
        for n in v.normas_citadas:
            print(f"  «{n.documento}» › {n.seccion}")
            if n.texto:
                print(f"      {n.texto}")

    print("\n" + linea + "\n")


def main() -> int:
    consulta = " ".join(sys.argv[1:]).strip()

    if not config.hay_api_key():
        print("\n" + config.MENSAJE_FALTA_CLAVE + "\n")
        return 1

    if not consulta:
        print("Describe la situación a verificar (o pega un checklist):")
        try:
            consulta = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1
    if not consulta:
        print("No se ha introducido ninguna situación.")
        return 1

    print("\nVerificando… (recuperando normativa y consultando al LLM)")
    try:
        v = veredicto.generar_veredicto(consulta)
    except LLMNoConfigurado as exc:
        print("\n" + str(exc) + "\n")
        return 1
    except Exception as exc:  # noqa: BLE001 — la CLI no debe reventar
        print(f"\nNo se pudo generar el veredicto: {exc}\n")
        return 1

    imprimir_veredicto(v, consulta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
