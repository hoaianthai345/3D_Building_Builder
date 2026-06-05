# Backend + builder (Python). Procedural 3D needs no GPU and no system GL libs
# (we export GLB, we do not render server-side), so a slim image is enough.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ARTIFACTS_DIR=/app/artifacts \
    LLM_PROVIDER=mock

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY builder ./builder
COPY backend ./backend

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
