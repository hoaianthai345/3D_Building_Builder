"""Optional VieNeu-TTS integration for narrated tours.

The core project must run without heavy audio dependencies, so this module lazily
imports the ``vieneu`` SDK only when /api/tts is called. If the SDK is missing,
the frontend falls back to the browser's Web Speech voice.
"""

from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path


class TTSUnavailable(RuntimeError):
    """Raised when the optional VieNeu-TTS SDK is not installed or cannot load."""


_LOCK = threading.Lock()
_ENGINE = None
DEFAULT_FEMALE_VOICE = "Ngọc Lan"
_FEMALE_VOICE_CANDIDATES = (
    "Ngọc Lan",
    "Ngọc Linh",
    "Mỹ Duyên",
    "Trúc Ly",
    "Ly",
    "Ngoc",
    "Doan",
)


def _engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    with _LOCK:
        if _ENGINE is not None:
            return _ENGINE
        try:
            from vieneu import Vieneu  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise TTSUnavailable("VieNeu-TTS SDK is not installed. Install it with: pip install vieneu") from exc

        kwargs: dict[str, str] = {}
        mode = os.getenv("VIENEU_TTS_MODE", "").strip()
        api_base = os.getenv("VIENEU_TTS_API_BASE", "").strip()
        model = os.getenv("VIENEU_TTS_MODEL", "").strip()
        emotion = os.getenv("VIENEU_TTS_EMOTION", "").strip()
        if mode:
            kwargs["mode"] = mode
        if api_base:
            kwargs["api_base"] = api_base
        if model:
            kwargs["model_name"] = model
        if emotion:
            kwargs["emotion"] = emotion

        try:
            _ENGINE = Vieneu(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise TTSUnavailable(f"VieNeu-TTS could not start: {exc}") from exc
        return _ENGINE


def _voice_id(value) -> str:
    if isinstance(value, tuple) and len(value) >= 2:
        return str(value[1])
    return str(value)


def _resolve_voice(tts, requested: str) -> str:
    if requested:
        return requested

    configured = os.getenv("VIENEU_TTS_VOICE", DEFAULT_FEMALE_VOICE).strip()
    candidates = (configured, *[v for v in _FEMALE_VOICE_CANDIDATES if v != configured])

    preset_names: set[str] = set()
    try:
        preset_names.update(str(name) for name in getattr(tts, "_preset_voices", {}).keys())
    except Exception:  # noqa: BLE001
        pass
    try:
        preset_names.update(_voice_id(item) for item in tts.list_preset_voices())
    except Exception:  # noqa: BLE001
        pass

    if not preset_names:
        return configured
    for candidate in candidates:
        if candidate in preset_names:
            return candidate
    return configured


def synthesize(text: str, out_dir: str = "artifacts", voice: str = "") -> Path:
    cleaned = " ".join(text.split())
    if not cleaned:
        raise ValueError("text is required")

    tts = _engine()
    resolved_voice = _resolve_voice(tts, voice.strip())
    cache_dir = Path(out_dir) / "tts"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{resolved_voice}\n{cleaned}".encode("utf-8")).hexdigest()[:24]
    wav_path = cache_dir / f"{key}.wav"
    if wav_path.exists() and wav_path.stat().st_size > 0:
        return wav_path

    try:
        audio = tts.infer(cleaned, voice=resolved_voice)
        tts.save(audio, str(wav_path))
    except Exception as exc:  # noqa: BLE001
        raise TTSUnavailable(f"VieNeu-TTS synthesis failed: {exc}") from exc
    return wav_path
