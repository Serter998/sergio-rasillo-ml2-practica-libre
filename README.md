# Centinela APPCC — Verificador de cumplimiento en seguridad alimentaria con RAG

Centinela APPCC es un **verificador de cumplimiento** (no un chatbot): el usuario
describe una situación operativa de una cocina/industria alimentaria o rellena un
checklist, y el sistema emite un **veredicto estructurado** (🟢 cumple / 🟡 requiere
atención / 🔴 no cumple) con las **normas aplicables citadas** (indicando el documento
de origen), los **incumplimientos detectados** y las **acciones correctivas**.

> El razonamiento cualitativo (criterios, procedimientos, correcciones) proviene de un
> pipeline **RAG** sobre un corpus didáctico de seguridad alimentaria; las comprobaciones
> numéricas (temperaturas, tiempos en zona de peligro, alérgenos) las realizan **tools
> deterministas** que el LLM decide invocar. El veredicto se apoya en datos fiables, no en
> alucinación.

---

## Unidades del curso aplicadas

- **U1 — IA Generativa y LLMs:** un LLM (vía OpenRouter) evalúa la situación descrita y
  redacta el veredicto final. _(Justificación del modelo en «Decisiones técnicas».)_
- **U2 — Prompt Engineering:** system prompt que **obliga a citar la fuente** y **prohíbe
  inventar umbrales**; **few-shot** para clasificar el tipo de consulta (escenario libre vs.
  checklist y dominio implicado); **chain-of-thought** para razonar cadenas tiempo/temperatura.
- **U3 — Transformers y APIs:** acceso programático al LLM vía la API de OpenRouter
  (cliente OpenAI-compatible) con **timeouts, reintentos con backoff exponencial** y
  **validación de la salida estructurada**.
- **U4 — Agentes y function calling:** el LLM decide cuándo invocar **tools deterministas**
  (`comprobar_temperatura`, `evaluar_tiempo_zona_peligro`, `buscar_alergeno`) que devuelven
  resultados numéricos fiables sobre los que se construye el veredicto.
- **U5 — RAG y Bases Vectoriales:** ingesta del corpus → chunking → embeddings locales →
  base vectorial (ChromaDB) → recuperación semántica top-k de la normativa aplicable.
- **U6 — MCP _(opcional)_:** exposición de la verificación como servidor MCP con una tool.

> **Cobertura:** 5 unidades (U1–U5), con U6 como ampliación opcional.

---

## Arquitectura

```
                 ┌─────────────────────────────────────────────────────┐
  Entrada  ──▶   │  Escenario en lenguaje natural  /  Checklist         │
                 └───────────────────────────┬─────────────────────────┘
                                             │
                 ┌───────────────────────────▼─────────────────────────┐
   U5  RAG   ──▶ │  Recuperación semántica (Chroma, top-k) de la        │
                 │  normativa aplicable  →  parte CUALITATIVA            │
                 └───────────────────────────┬─────────────────────────┘
                                             │  contexto citado
                 ┌───────────────────────────▼─────────────────────────┐
 U1/U2/U3  ──▶   │  LLM (OpenRouter) razona y DECIDE invocar tools      │
                 └───────────────────────────┬─────────────────────────┘
                                             │  function calling
                 ┌───────────────────────────▼─────────────────────────┐
   U4 Tools  ──▶ │  Comprobaciones numéricas deterministas              │
                 │  (temperatura, tiempo en zona 5–65 °C, alérgenos)    │
                 └───────────────────────────┬─────────────────────────┘
                                             │
                 ┌───────────────────────────▼─────────────────────────┐
  Salida   ──▶   │  VEREDICTO ESTRUCTURADO (validado con Pydantic):     │
                 │  estado · normas citadas (con documento) ·           │
                 │  incumplimientos · acciones correctivas              │
                 └─────────────────────────────────────────────────────┘
```

_(Diagrama detallado y capturas en la sección «Capturas / Demo».)_

---

## Tecnologías utilizadas

- **Python 3.13** (entorno Windows + PowerShell).
- **OpenRouter** como pasarela al LLM (cliente `openai` OpenAI-compatible).
- **sentence-transformers** para embeddings **locales** (multilingüe, español).
- **ChromaDB** como base vectorial local persistente.
- **Pydantic** para validar el veredicto estructurado.
- **NiceGUI** para la interfaz tipo panel de inspección.

---

## Instalación y configuración

> Requiere **Python 3.13** (las dependencias de embeddings/vector store no funcionan en
> versiones antiguas). Comandos para **Windows + PowerShell**.

```powershell
# 1) Clonar el repositorio
git clone <URL-del-repo>
cd ml2-practica-libre

# 2) Crear y activar el entorno virtual
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Instalar dependencias
pip install -r requirements.txt

# 4) Configurar la clave (solo necesaria a partir de la Fase 2)
copy .env.example .env
#   …y edita .env para poner tu OPENROUTER_API_KEY
```

> La app **no se rompe** si arrancas sin `OPENROUTER_API_KEY`: muestra un aviso claro
> indicando que falta la clave y dónde ponerla. El corpus, la ingesta y el retrieval
> (Fases 0–1) son ejecutables **sin clave**.

---

## Uso

```powershell
# Construir la base vectorial a partir del corpus (no requiere clave)
python -m src.ingesta

# Probar la recuperación semántica sin LLM (no requiere clave)
python scripts\probar_retrieval.py "carne de pollo cocinada a 60 grados en el centro"

# Ejecutar el verificador por consola (requiere OPENROUTER_API_KEY)
python -m src.cli

# Lanzar la interfaz web tipo panel de inspección (requiere OPENROUTER_API_KEY)
python -m src.app
```

_(Ejemplos concretos de entrada/salida se añaden a medida que avanzan las fases.)_

---

## Capturas / Demo

> _Mínimo 3 capturas que demuestren funcionalidad real (pendiente de Fase 3)._

1. _(hueco)_ Panel de inspección con un veredicto **🟢 cumple**. → `docs/capturas/01_veredicto_cumple.png`
2. _(hueco)_ Veredicto **🔴 no cumple** con incumplimientos y acciones correctivas. → `docs/capturas/02_veredicto_no_cumple.png`
3. _(hueco)_ Sección de **normas citadas** mostrando el documento de origen. → `docs/capturas/03_citas.png`

---

## Decisiones técnicas

- **Modelo LLM:** `openai/gpt-oss-120b:free` vía OpenRouter. _(Justificación: gratuito,
  buen soporte de function calling y de español. Pendiente de validar en Fase 2.)_
- **Temperatura:** `0.1` — dominio de cumplimiento ⇒ se prioriza la consistencia y se
  minimiza la alucinación.
- **Embeddings locales** (no se usa OpenRouter para embeddings, que no ofrece un endpoint
  fiable): `intfloat/multilingual-e5-base`. Buen rendimiento multilingüe en español y corre
  en CPU sin coste. Se aplican los prefijos `query:`/`passage:` que el modelo espera.
- **Vector store:** ChromaDB — guarda metadatos (documento de origen, dominio, sección)
  junto al vector, imprescindible para **citar la fuente** en el veredicto. Distancia coseno
  sobre embeddings normalizados.
- **Chunking:** troceado *consciente de encabezados* (cada sección `##` es una unidad),
  con subdivisión en ventanas de **600 caracteres** y **100 de solape** para las secciones
  largas. Así cada umbral/criterio queda íntegro y la cita sale limpia (44 chunks en total).
- **k = 4** en la recuperación: suficiente para traer 2-4 criterios aplicables sin meter
  ruido. En las pruebas, las consultas relevantes recuperan los fragmentos correctos con
  similitudes de 0.82–0.89.
- **Dificultades encontradas:** _(se documentan a medida que aparecen.)_

### Apoyo de herramientas de IA

_(Se detalla qué partes se apoyaron en IA y qué se ajustó manualmente.)_

---

## Posibles mejoras

1. _(pendiente — mínimo 2)_
2. _(pendiente)_

---

## Autor

- **Sergio Rasillo** _(confirmar nombre completo)_

---

> **Aviso:** el corpus incluido es **contenido didáctico de elaboración propia** basado en
> criterios estándar y públicos del sector. **No constituye normativa oficial** ni reproduce
> ningún reglamento ni material de empresa alguna.
