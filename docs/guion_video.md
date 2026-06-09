# Guion del vídeo demo (máx. 3 min) — bonificación +0.25

Objetivo: demostrar que el proyecto **funciona** y que integra las unidades del curso.
Graba la pantalla (p. ej. con Xbox Game Bar: `Win + G`) y narra siguiendo este guion.

**Preparación antes de grabar:**
- Ten el `.env` con la clave puesta y la base vectorial creada (`python -m src.ingesta`).
- Abre dos cosas: una terminal de PowerShell y el navegador en `http://localhost:8080`
  (con `python -m src.app` corriendo).

---

### 0:00 – 0:25 · Qué es (y qué NO es)
> «Esto es **Centinela APPCC**, un **verificador de cumplimiento** en seguridad
> alimentaria. No es un chatbot: describes una situación de una cocina y te devuelve un
> **veredicto** —cumple, requiere atención o no cumple— con la **normativa citada** y las
> **acciones correctivas**.»

*(En pantalla: la cabecera "Panel de inspección" de la app.)*

### 0:25 – 0:50 · Cómo está hecho (unidades)
> «Por dentro: un **RAG** sobre un corpus de seguridad alimentaria recupera la normativa
> aplicable (U5); un **LLM vía OpenRouter** (U1, U3) razona y **decide invocar herramientas
> deterministas** (U4) para las comprobaciones numéricas; los **prompts** obligan a citar y
> prohíben inventar umbrales (U2); y todo se expone también como **servidor MCP** (U6).»

### 0:50 – 1:25 · Demo 1: NO CUMPLE (temperatura)
*(En la app, escribe y pulsa Verificar:)*
`Hemos cocinado pechuga de pollo y el termómetro marca 60 °C en el centro.`
> «Veredicto **rojo: no cumple**. La herramienta `comprobar_temperatura` ha calculado que
> 60 °C no llega a los 75 °C de cocinado, y cita el documento de temperaturas. La acción
> correctiva: seguir cocinando hasta 75 °C.»

### 1:25 – 1:55 · Demo 2: tiempo en zona de peligro y alérgenos
*(Escribe:)* `Una tarta de nata se ha quedado a 22 °C durante 3 horas.`
> «Aquí actúa `evaluar_tiempo_zona_peligro`: 180 minutos superan el límite de 2 horas → no
> cumple.»

*(Escribe:)* `Plato de gambas rebozadas con salsa de soja y mostaza.`
> «La herramienta `buscar_alergeno` detecta gluten, crustáceos, soja y mostaza, y cita la
> lista de alérgenos de declaración obligatoria.»

### 1:55 – 2:15 · Demo 3: CUMPLE
*(Escribe:)* `El arcón congelador está a -20 °C para conservar carne congelada.`
> «Veredicto **verde: cumple**, porque −20 °C está por debajo del umbral de −18 °C.»

### 2:15 – 2:40 · Robustez
> «El sistema está pensado para evaluarse: sin la clave de OpenRouter no se rompe, avisa de
> que falta; y el RAG se puede probar sin LLM.»

*(En la terminal:)*
`python scripts\probar_retrieval.py "como descongelar carne de forma segura"`
> «Recupera el fragmento correcto del corpus con su puntuación de similitud.»

### 2:40 – 3:00 · Cierre
> «Decisiones clave: modelo gratuito con *function calling*, embeddings locales para no
> depender de pago, ChromaDB con metadatos para poder citar, y temperatura baja para
> veredictos consistentes. Mejoras futuras: modo checklist y exportación del veredicto a un
> registro APPCC. Gracias.»

---

**Consejo:** si una llamada al modelo gratuito tarda, ten una pestaña con un veredicto ya
generado para no cortar el ritmo del vídeo.
