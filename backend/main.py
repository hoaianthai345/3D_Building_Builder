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

import base64
import json
import os
from datetime import datetime, timezone
from typing import Any, List
from urllib.parse import quote
from uuid import uuid4

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional local convenience
    load_dotenv = None

from builder.llm import get_llm, llm_from_runtime_key
from builder.llm.base import LLMClient
from builder.pipeline import generate
from builder.schemas import (
    GenerateRequest, IndustryTone, SceneBundle, StopDescribe, Tour,
)
from builder.tour import generate_tour
from builder.tts import TTSUnavailable, synthesize
from builder.vision_describer import describe_image

if load_dotenv:
    load_dotenv()

LLM_MODEL_DEFAULTS: dict[str, list[str]] = {
    "gemini": [
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
    "groq": [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ],
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
    ],
    "claude": [
        "claude-sonnet-4-6",
        "claude-sonnet-4-5",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
    ],
}

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts")
FRONTEND_ORIGINS_RAW = os.getenv("FRONTEND_ORIGINS", os.getenv("FRONTEND_ORIGIN", "*"))
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TOUR_PROJECTS_TABLE = os.getenv("SUPABASE_TOUR_PROJECTS_TABLE", "tour_projects")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "3D")

os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def _cors_origins(raw: str) -> list[str]:
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if not origins or "*" in origins:
        return ["*"]
    return origins


cors_origins = _cors_origins(FRONTEND_ORIGINS_RAW)
cors_origin_regex = (
    None
    if "*" in cors_origins
    else r"https://.*\.vercel\.app|https://.*\.ngrok-free\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+"
)

app = FastAPI(title="AI 3D Scene Describer", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
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
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="description is required")
    try:
        return generate(req, out_dir=ARTIFACTS_DIR)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"generation failed: {exc}") from exc


# --------------------------------------------------------------------------- #
# Guided tour: AI vision describe + narrated tour assembly                     #
# --------------------------------------------------------------------------- #
@app.post("/api/describe-image", response_model=StopDescribe)
async def api_describe_image(
    file: UploadFile = File(...),
    industry: str = Form("real_estate"),
    hint: str = Form(""),
    llm_provider: str = Form(""),
    llm_api_key: str = Form(""),
    llm_model: str = Form(""),
) -> StopDescribe:
    try:
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="image file is empty")
        media = file.content_type or "image/jpeg"
        if not media.startswith("image/"):
            raise HTTPException(status_code=400, detail="uploaded file must be an image")
        if len(raw) > 8 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="image is larger than 8 MB")
        b64 = base64.b64encode(raw).decode()
        llm = _runtime_llm(llm_provider, llm_api_key, llm_model)
        return describe_image(b64, media, IndustryTone(industry), llm=llm, hint=hint)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"describe failed: {exc}") from exc


class TourStopIn(BaseModel):
    id: str
    image: str
    kind: str = "photo"
    describe: StopDescribe


class TourRequest(BaseModel):
    project_name: str
    industry: IndustryTone = IndustryTone.real_estate
    stops: List[TourStopIn]
    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""


class LLMModelsRequest(BaseModel):
    provider: str
    api_key: str = ""


class LLMModelsResponse(BaseModel):
    provider: str
    models: List[str]
    source: str


class TourProjectPayload(BaseModel):
    project: dict[str, Any]


class TourProjectSaveResponse(BaseModel):
    configured: bool
    project: dict[str, Any] | None = None


class TourProjectsResponse(BaseModel):
    configured: bool
    projects: List[dict[str, Any]]


class ImageUrlRequest(BaseModel):
    url: str
    industry: IndustryTone = IndustryTone.real_estate
    hint: str = ""
    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1600)
    voice: str = Field("", max_length=120)


class TTSGenerateResponse(BaseModel):
    audio_url: str
    filename: str
    storage: str = "local"
    bucket: str = ""
    path: str = ""


class MediaUploadResponse(BaseModel):
    configured: bool
    url: str = ""
    storage: str = "local"
    bucket: str = ""
    path: str = ""


def _artifact_url(path: os.PathLike[str] | str) -> str:
    rel = os.path.relpath(os.fspath(path), ARTIFACTS_DIR)
    return f"/artifacts/{rel.replace(os.sep, '/')}"


def _runtime_llm(provider: str, api_key: str, model: str) -> LLMClient | None:
    if not api_key.strip():
        return None
    try:
        return llm_from_runtime_key(provider, api_key, model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _supabase_storage_configured() -> bool:
    return bool(_supabase_configured() and SUPABASE_STORAGE_BUCKET.strip())


def _storage_object_path(path: str) -> str:
    clean = [quote(part.strip("/"), safe="") for part in path.split("/") if part.strip("/")]
    return "/".join(clean)


def _supabase_public_url(path: str) -> str:
    bucket = quote(SUPABASE_STORAGE_BUCKET.strip(), safe="")
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{_storage_object_path(path)}"


def _upload_supabase_storage(raw: bytes, path: str, content_type: str) -> MediaUploadResponse:
    if not _supabase_storage_configured():
        return MediaUploadResponse(configured=False)

    object_path = _storage_object_path(path)
    bucket = quote(SUPABASE_STORAGE_BUCKET.strip(), safe="")
    try:
        res = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/{bucket}/{object_path}",
            timeout=35,
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "content-type": content_type,
                "cache-control": "3600",
                "x-upsert": "true",
            },
            data=raw,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"supabase storage request failed: {exc}") from exc
    if res.status_code >= 400:
        raise RuntimeError(f"supabase storage returned {res.status_code}: {res.text[:240]}")
    return MediaUploadResponse(
        configured=True,
        url=_supabase_public_url(object_path),
        storage="supabase",
        bucket=SUPABASE_STORAGE_BUCKET.strip(),
        path=object_path,
    )


def _supabase_headers(prefer: str = "") -> dict[str, str]:
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "content-type": "application/json",
    }
    if prefer:
        headers["prefer"] = prefer
    return headers


def _supabase_rest_url(path: str = "") -> str:
    table = SUPABASE_TOUR_PROJECTS_TABLE.strip() or "tour_projects"
    return f"{SUPABASE_URL}/rest/v1/{table}{path}"


def _project_row(project: dict[str, Any]) -> dict[str, Any]:
    project_id = str(project.get("id", "")).strip()
    if not project_id:
        raise HTTPException(status_code=400, detail="project.id is required")
    updated_at = str(project.get("updatedAt") or "").strip() or datetime.now(timezone.utc).isoformat()
    return {"id": project_id, "payload": project, "updated_at": updated_at}


@app.get("/api/tour-projects", response_model=TourProjectsResponse)
def api_list_tour_projects() -> TourProjectsResponse:
    if not _supabase_configured():
        return TourProjectsResponse(configured=False, projects=[])
    try:
        res = requests.get(
            _supabase_rest_url("?select=id,payload,updated_at&order=updated_at.desc"),
            timeout=20,
            headers=_supabase_headers(),
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"supabase request failed: {exc}") from exc
    if res.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"supabase returned {res.status_code}: {res.text[:240]}")
    rows = res.json()
    projects = [
        row.get("payload")
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("payload"), dict)
    ]
    return TourProjectsResponse(configured=True, projects=projects)


@app.put("/api/tour-projects/{project_id}", response_model=TourProjectSaveResponse)
def api_save_tour_project(project_id: str, req: TourProjectPayload) -> TourProjectSaveResponse:
    if not _supabase_configured():
        raise HTTPException(status_code=503, detail="supabase is not configured")
    row = _project_row(req.project)
    if row["id"] != project_id:
        raise HTTPException(status_code=400, detail="project id does not match URL")
    try:
        res = requests.post(
            _supabase_rest_url("?on_conflict=id"),
            timeout=25,
            headers=_supabase_headers("resolution=merge-duplicates,return=representation"),
            json=[row],
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"supabase request failed: {exc}") from exc
    if res.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"supabase returned {res.status_code}: {res.text[:240]}")
    rows = res.json()
    saved = rows[0].get("payload") if rows and isinstance(rows[0], dict) else req.project
    return TourProjectSaveResponse(configured=True, project=saved)


@app.delete("/api/tour-projects/{project_id}")
def api_delete_tour_project(project_id: str) -> dict[str, bool]:
    if not _supabase_configured():
        raise HTTPException(status_code=503, detail="supabase is not configured")
    try:
        res = requests.delete(
            _supabase_rest_url(f"?id=eq.{project_id}"),
            timeout=20,
            headers=_supabase_headers(),
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"supabase request failed: {exc}") from exc
    if res.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"supabase returned {res.status_code}: {res.text[:240]}")
    return {"ok": True}


@app.post("/api/tour-assets/image", response_model=MediaUploadResponse)
async def api_upload_tour_image(file: UploadFile = File(...)) -> MediaUploadResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="image file is empty")
    media = file.content_type or "image/jpeg"
    if not media.startswith("image/"):
        raise HTTPException(status_code=400, detail="uploaded file must be an image")
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="image is larger than 8 MB")
    if not _supabase_storage_configured():
        return MediaUploadResponse(configured=False)

    subtype = media.split("/", 1)[1].split(";", 1)[0].lower()
    ext = {"jpeg": "jpg", "pjpeg": "jpg", "svg+xml": "svg"}.get(subtype, subtype or "jpg")
    if ext not in {"jpg", "jpeg", "png", "webp", "gif", "avif", "svg"}:
        ext = "jpg"
    date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    path = f"photos/{date_path}/{uuid4().hex}.{ext}"
    try:
        return _upload_supabase_storage(raw, path, media)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _normalize_provider(provider: str) -> str:
    provider = (provider or "").strip().lower()
    if provider == "google":
        return "gemini"
    if provider == "anthropic":
        return "claude"
    if provider in LLM_MODEL_DEFAULTS:
        return provider
    raise HTTPException(status_code=400, detail="unsupported llm provider")


def _default_models(provider: str) -> list[str]:
    return list(LLM_MODEL_DEFAULTS[provider])


def _preferred_first(provider: str, models: list[str]) -> list[str]:
    defaults = _default_models(provider)
    seen: set[str] = set()
    merged: list[str] = []
    for model in [*defaults, *models]:
        model = model.strip()
        if model and model not in seen:
            seen.add(model)
            merged.append(model)
    return merged


def _list_openai_compatible_models(api_key: str, base_url: str, provider: str) -> list[str]:
    res = requests.get(
        f"{base_url.rstrip('/')}/models",
        timeout=20,
        headers={"authorization": f"Bearer {api_key}"},
    )
    if res.status_code >= 400:
        raise RuntimeError(f"model list returned {res.status_code}")
    raw = res.json().get("data", [])
    models = [str(item.get("id", "")).strip() for item in raw if isinstance(item, dict)]
    excluded = ("audio", "embedding", "guard", "moderation", "rerank", "tts", "whisper")
    if provider == "openai":
        models = [
            m for m in models
            if m.startswith(("gpt-", "o", "chatgpt-")) and not any(x in m.lower() for x in excluded)
        ]
    else:
        models = [
            m for m in models
            if not any(x in m.lower() for x in excluded)
        ]
    return sorted(set(models))


def _list_gemini_models(api_key: str) -> list[str]:
    res = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        timeout=20,
        headers={"x-goog-api-key": api_key},
    )
    if res.status_code >= 400:
        raise RuntimeError(f"model list returned {res.status_code}")
    models: list[str] = []
    for item in res.json().get("models", []):
        if not isinstance(item, dict):
            continue
        methods = item.get("supportedGenerationMethods") or []
        if "generateContent" not in methods:
            continue
        name = str(item.get("name", "")).removeprefix("models/").strip()
        if name:
            models.append(name)
    return sorted(set(models))


def _list_claude_models(api_key: str) -> list[str]:
    res = requests.get(
        "https://api.anthropic.com/v1/models",
        timeout=20,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    if res.status_code >= 400:
        raise RuntimeError(f"model list returned {res.status_code}")
    data: Any = res.json().get("data", [])
    models = [str(item.get("id", "")).strip() for item in data if isinstance(item, dict)]
    return sorted(set(m for m in models if m))


@app.post("/api/llm/models", response_model=LLMModelsResponse)
def api_llm_models(req: LLMModelsRequest) -> LLMModelsResponse:
    provider = _normalize_provider(req.provider)
    api_key = req.api_key.strip()
    if not api_key:
        return LLMModelsResponse(provider=provider, models=_default_models(provider), source="default")

    try:
        if provider == "gemini":
            models = _list_gemini_models(api_key)
        elif provider == "groq":
            models = _list_openai_compatible_models(api_key, "https://api.groq.com/openai/v1", provider)
        elif provider == "openai":
            models = _list_openai_compatible_models(api_key, "https://api.openai.com/v1", provider)
        elif provider == "claude":
            models = _list_claude_models(api_key)
        else:
            raise HTTPException(status_code=400, detail="unsupported llm provider")
    except HTTPException:
        raise
    except Exception:
        return LLMModelsResponse(provider=provider, models=_default_models(provider), source="default")

    return LLMModelsResponse(
        provider=provider,
        models=_preferred_first(provider, models),
        source="provider",
    )


def _download_image(url: str) -> tuple[str, str]:
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="image URL must start with http:// or https://")
    try:
        res = requests.get(
            url,
            timeout=12,
            headers={"user-agent": "AI-3D-Scene-Describer/1.0"},
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"could not download image: {exc}") from exc
    if res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"image URL returned {res.status_code}")
    media = res.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    if not media.startswith("image/"):
        raise HTTPException(status_code=400, detail="URL did not return an image")
    if len(res.content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="image is larger than 8 MB")
    return base64.b64encode(res.content).decode(), media


@app.post("/api/describe-image-url", response_model=StopDescribe)
def api_describe_image_url(req: ImageUrlRequest) -> StopDescribe:
    b64, media = _download_image(req.url)
    try:
        llm = _runtime_llm(req.llm_provider, req.llm_api_key, req.llm_model)
        return describe_image(b64, media, req.industry, llm=llm, hint=req.hint)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"describe failed: {exc}") from exc


@app.post("/api/tour", response_model=Tour)
def api_tour(req: TourRequest) -> Tour:
    try:
        llm = _runtime_llm(req.llm_provider, req.llm_api_key, req.llm_model)
        return generate_tour(req.project_name, req.industry, [s.model_dump() for s in req.stops], llm=llm)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"tour generation failed: {exc}") from exc


@app.post("/api/tts")
def api_tts(req: TTSRequest) -> FileResponse:
    try:
        wav = synthesize(req.text, out_dir=ARTIFACTS_DIR, voice=req.voice.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TTSUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return FileResponse(wav, media_type="audio/wav", filename=wav.name)


@app.post("/api/tts/generate", response_model=TTSGenerateResponse)
def api_tts_generate(req: TTSRequest) -> TTSGenerateResponse:
    try:
        wav = synthesize(req.text, out_dir=ARTIFACTS_DIR, voice=req.voice.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TTSUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if _supabase_storage_configured():
        try:
            uploaded = _upload_supabase_storage(wav.read_bytes(), f"tts/{wav.name}", "audio/wav")
            if uploaded.url:
                return TTSGenerateResponse(
                    audio_url=uploaded.url,
                    filename=wav.name,
                    storage=uploaded.storage,
                    bucket=uploaded.bucket,
                    path=uploaded.path,
                )
        except RuntimeError:
            pass
    return TTSGenerateResponse(audio_url=_artifact_url(wav), filename=wav.name)
