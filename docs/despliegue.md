# Despliegue (bonificación +0.25)

La app se despliega con la imagen **Docker** incluida ([`Dockerfile`](../Dockerfile)). La base
vectorial se construye dentro de la imagen, así que el contenedor arranca listo. La clave
`OPENROUTER_API_KEY` se configura como variable de entorno en la plataforma (nunca en el repo).

> **Nota sobre memoria:** la app usa PyTorch + Sentence Transformers. Por eso la imagen fija
> un modelo de embeddings ligero (`paraphrase-multilingual-MiniLM-L12-v2`). Aun así, los
> planes *free* (≈512 MB de RAM) pueden ir justos; si el contenedor se queda sin memoria,
> usa el plan de pago más pequeño o un servicio con algo más de RAM.

## Opción A — Render (con `render.yaml`)

1. Sube el repositorio a GitHub.
2. En https://dashboard.render.com → **New → Blueprint** → conecta el repo.
   Render detecta [`render.yaml`](../render.yaml) y crea un servicio web Docker.
3. En **Environment**, pega tu `OPENROUTER_API_KEY`.
4. Deploy. Render asigna un puerto vía la variable `PORT` (la app la respeta) y te da una
   URL pública `https://centinela-appcc.onrender.com`.

## Opción B — Koyeb

1. Sube el repositorio a GitHub.
2. En https://app.koyeb.com → **Create Web Service → GitHub** → elige el repo.
3. Build: **Dockerfile**. Exposed port: **8080** (Koyeb inyecta `PORT`).
4. En **Environment variables** añade `OPENROUTER_API_KEY` (tipo *secret*).
5. Deploy → obtendrás una URL `https://<app>-<org>.koyeb.app`.

## Probar en local con Docker

```powershell
docker build -t centinela-appcc .
docker run -p 8080:8080 -e OPENROUTER_API_KEY=sk-or-v1-tu-clave centinela-appcc
# Abre http://localhost:8080
```

Una vez desplegada, añade la URL pública al README (sección «Capturas / Demo» o «Uso»).
