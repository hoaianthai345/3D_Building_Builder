"""Generative GPU backend: image -> realistic 3D mesh via TRELLIS.

This runs on a GPU machine / Colab (>=6GB VRAM), not on the CPU pipeline. It turns
a building photo or render into a single textured GLB. Unlike the procedural
backend it does NOT produce per-floor/per-room structure, so generative scenes
show in the plain model viewer (no drill-down).

Usage is via ``builder.pipeline.generate_from_image`` (which calls
``image_to_glb`` here, then assembles a SceneBundle with the CPU describer).

TRELLIS install + run is GPU-only and version-sensitive: see colab/trellis_build.ipynb
and https://github.com/microsoft/TRELLIS . This module lazily imports TRELLIS and
raises a clear error if it is not available, so importing it on CPU is safe.
"""

from __future__ import annotations

import os

from .schemas import BuildingSpec, ModelInfo


def image_to_glb(
    image_path: str,
    out_path: str,
    *,
    seed: int = 1,
    simplify: float = 0.95,
    texture_size: int = 1024,
) -> ModelInfo:
    """Run TRELLIS image-to-3D and export a GLB. GPU required."""
    # TRELLIS reads these at import; set sensible defaults if unset.
    os.environ.setdefault("ATTN_BACKEND", "xformers")
    os.environ.setdefault("SPCONV_ALGO", "native")

    try:
        from PIL import Image
        from trellis.pipelines import TrellisImageTo3DPipeline
        from trellis.utils import postprocessing_utils
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "TRELLIS not available. Run on a GPU machine / Colab with TRELLIS installed "
            "(see colab/trellis_build.ipynb). Original error: " + str(exc)
        ) from exc

    pipeline = TrellisImageTo3DPipeline.from_pretrained("microsoft/TRELLIS-image-large")
    pipeline.cuda()

    image = Image.open(image_path).convert("RGB")
    outputs = pipeline.run(image, seed=seed)
    glb = postprocessing_utils.to_glb(
        outputs["gaussian"][0],
        outputs["mesh"][0],
        simplify=simplify,
        texture_size=texture_size,
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    glb.export(out_path)

    tri = int(glb.faces.shape[0]) if hasattr(glb, "faces") else 0
    return ModelInfo(
        glb=os.path.basename(out_path),
        backend="generative",
        tri_count=tri,
        size_kb=round(os.path.getsize(out_path) / 1024.0, 1),
    )


def build_glb(spec: BuildingSpec, out_path: str, **kwargs) -> ModelInfo:  # pragma: no cover
    raise NotImplementedError(
        "Generative backend is image-driven. Use image_to_glb(image_path, out_path) "
        "or builder.pipeline.generate_from_image(req, image_path)."
    )
