"""AI 3D Scene Describer — building pipeline.

Three stages, each independently testable:
    spec_agent  : natural language + form params -> BuildingSpec
    procedural  : BuildingSpec -> GLB (trimesh, CPU)   [generative GPU = pluggable]
    describer   : BuildingSpec -> marketing copy + digitization tips

All LLM access goes through ``builder.llm`` so the Mock provider can run the whole
pipeline offline; swap to Claude by setting LLM_PROVIDER=claude + ANTHROPIC_API_KEY.

``builder.schemas`` is the frozen contract shared by the backend API and the frontend
artifacts. Do not change field names without bumping ``SceneBundle.version``.
"""

__all__ = ["schemas"]
