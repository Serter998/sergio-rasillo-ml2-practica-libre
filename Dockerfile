# Imagen para desplegar Centinela APPCC (Render, Koyeb, Railway…).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    # En despliegue se usa un modelo de embeddings ligero (menos memoria/disco).
    EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

WORKDIR /app

# 1) PyTorch en versión CPU-only (mucho más pequeña que la de GPU).
RUN pip install --upgrade pip \
    && pip install torch --index-url https://download.pytorch.org/whl/cpu

# 2) Resto de dependencias (torch ya está satisfecho).
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3) Código y corpus.
COPY . .

# 4) Construye la base vectorial en el build (descarga el modelo de embeddings una vez).
#    No requiere clave de OpenRouter.
RUN python -m src.ingesta

EXPOSE 8080

# El puerto efectivo lo toma la app de la variable PORT (la fija la plataforma).
CMD ["python", "-m", "src.app"]
