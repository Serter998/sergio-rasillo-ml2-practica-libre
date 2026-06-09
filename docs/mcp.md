# Servidor MCP (U6)

Centinela APPCC se expone también como **servidor MCP** (Model Context Protocol), de
modo que cualquier cliente MCP (por ejemplo **Claude Desktop**) pueda usar el verificador
como herramienta.

## Tools expuestas

| Tool | Qué hace | ¿Necesita clave? |
|---|---|---|
| `buscar_normativa(consulta, k=4)` | Recupera los fragmentos de normativa más relevantes (RAG). | No |
| `verificar_cumplimiento(situacion)` | Devuelve el veredicto estructurado completo. | Sí (`OPENROUTER_API_KEY`) |

## Ejecutar el servidor

Requiere haber creado la base vectorial antes (`python -m src.ingesta`).

```powershell
.\.venv\Scripts\Activate.ps1
python -m src.mcp_server
```

El servidor habla por **stdio**, que es como lo lanzan los clientes MCP.

## Conectarlo a Claude Desktop

Edita el archivo `claude_desktop_config.json` (en Windows:
`%APPDATA%\Claude\claude_desktop_config.json`) y añade el servidor. Sustituye las rutas por
las de tu equipo:

```json
{
  "mcpServers": {
    "centinela-appcc": {
      "command": "C:\\ruta\\al\\proyecto\\ml2-practica-libre\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server"],
      "cwd": "C:\\ruta\\al\\proyecto\\ml2-practica-libre",
      "env": {
        "OPENROUTER_API_KEY": "sk-or-v1-tu-clave"
      }
    }
  }
}
```

> `cwd` debe ser la raíz del proyecto para que `python -m src.mcp_server` encuentre el
> paquete `src`. La clave puede ir en `env` aquí o en el `.env` del proyecto.

Reinicia Claude Desktop. Aparecerán las tools `buscar_normativa` y `verificar_cumplimiento`,
que el modelo podrá invocar (por ejemplo: *"verifica si es seguro un pollo cocinado a 60 °C"*).

Hay un ejemplo de configuración en [`docs/claude_desktop_config.example.json`](claude_desktop_config.example.json).
