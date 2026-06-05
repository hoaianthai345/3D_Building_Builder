"""FastAPI backend for live generation (local / GPU / Docker).

Endpoints
    GET  /api/health         -> liveness + active LLM provider
    GET  /api/scenes         -> list bundle ids present in the artifacts dir
    POST /api/generate       -> run the pipeline, return a SceneBundle
    GET  /artifacts/<id>.glb -> the generated 3D model (static)

The Vercel demo does NOT need this service: it reads pre-built artifacts statically.
This backend is for running the full pipeline live on a machine with the deps
installed (see Dockerfile / docker-compose.yml).
"""

from __future__ import annotations

import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from builder.llm import get_llm
from builder.pipeline import generate
from builder.schemas import GenerateRequest, SceneBundle

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

app = FastAPI(title="AI 3D Scene Describer", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_DIR), name="artifacts")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": get_llm().name, "artifacts_dir": ARTIFACTS_DIR}


@app.get("/api/scenes")
def scenes() -> dict:
    index_path = os.path.join(ARTIFACTS_DIR, "index.json")
    if not os.path.exists(index_path):
        return {"version": "1.0", "scenes": []}
    with open(index_path, encoding="utf-8") as fh:
        return json.load(fh)


@app.post("/api/generate", response_model=SceneBundle)
def api_generate(req: GenerateRequest) -> SceneBundle:
    try:
        return generate(req, out_dir=ARTIFACTS_DIR)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"generation failed: {exc}") from exc
