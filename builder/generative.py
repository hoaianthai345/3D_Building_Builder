"""Generative GPU backend (pluggable stub).

The default 3D backend is ``procedural`` (trimesh, CPU) which is the right tool for
"N floors x M rooms" massing. This module reserves the interface for a GPU
text-to-3D / image-to-3D model (e.g. TRELLIS, Shap-E, Hunyuan3D) to enrich assets
on Colab / a GPU machine. It is intentionally not implemented here.

To implement later:
    1. Add the model deps behind an extra (e.g. requirements-gpu.txt).
    2. Run image/text -> GLB on GPU, write to ``out_path``.
    3. Return a ModelInfo(backend="generative", ...).
See WORKFLOW.md section 4 for the projected VRAM / latency figures and sources.
"""

from __future__ import annotations

from .schemas import BuildingSpec, ModelInfo


def build_glb(spec: BuildingSpec, out_path: str, **kwargs) -> ModelInfo:  # pragma: no cover
    raise NotImplementedError(
        "Generative GPU backend is a stub. Use backend='procedural' (default), or "
        "implement TRELLIS/Shap-E here on a GPU/Colab machine. See WORKFLOW.md."
    )
