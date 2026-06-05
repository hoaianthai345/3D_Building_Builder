"""describer: BuildingSpec (+ request) -> DescriberOutput (the assignment core).

Produces a page title, an attractive summary, 3-5 AI highlights, and digitization
tips. Output is validated against DescriberOutput so highlight/tip counts are
guaranteed regardless of provider.
"""

from __future__ import annotations

from .llm.base import LLMClient
from .prompts import describe_prompt
from .schemas import BuildingSpec, DescriberOutput, GenerateRequest


def describe(spec: BuildingSpec, req: GenerateRequest, llm: LLMClient) -> DescriberOutput:
    context = {
        "project_name": req.project_name,
        "space_type": spec.space_type.value,
        "target_audience": req.target_audience,
        "description": req.description,
        "floors": spec.floors,
        "rooms_per_floor": spec.rooms_per_floor,
        "occupancy": spec.occupancy,
    }
    data = llm.complete_json(purpose="describe", context=context, prompt=describe_prompt(spec, req))
    # Clamp highlights to the schema's 3-5 window if a real LLM returns more.
    if isinstance(data.get("highlights"), list) and len(data["highlights"]) > 5:
        data["highlights"] = data["highlights"][:5]
    return DescriberOutput.model_validate(data)
