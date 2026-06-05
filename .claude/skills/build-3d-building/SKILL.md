---
name: build-3d-building
description: Use when generating, enriching, or adding a 3D building model in THIS repo (AI 3D Scene Describer) - e.g. "dựng tòa nhà 3D", "tạo building mới", "generate a 3D building", "add a scene", "author 360 prompts". Drives the procedural builder pipeline (CPU, no GPU) to produce a GLB + structure + Vietnamese describer + 360 panorama prompts, written as a SceneBundle artifact the frontend reads.
---

# Build a 3D building model (this repo)

Reusable playbook to produce a new building scene with the local pipeline. Works
fully offline (MockLLM); plug an Anthropic API key for richer copy. CPU only.

## When to use
- "Dựng / tạo / thêm một tòa nhà 3D" theo prompt + thông số (số tầng, số phòng, số người).
- Làm giàu nội dung phòng + viết prompt 360 cho một scene đã có.
- Bổ sung scene mới vào demo (`frontend/public/artifacts/`).

## Contract (frozen — never edit `builder/schemas.py` shape)
One generation = one `SceneBundle` (schema v1.1) in `builder/schemas.py`:
`input` (GenerateRequest) · `spec` (BuildingSpec) · `describer` (title, summary,
3-5 highlights, 2+ digitization_tips) · `model` (GLB info) · `structure`
(floors -> rooms; each `Room` has type, rect, area, description, and
`panorama {prompt, image, status}`). Room ids `room_<floor>_<idx>` MUST match the
GLB node names. Do not rename fields or change room counts after a GLB exists.

## Setup (once)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # trimesh + numpy + fastapi + pydantic; CPU only
```

## Mode A — Generate a new building from a prompt
```bash
source .venv/bin/activate
python -m builder.run \
  --name "Tên dự án" \
  --space office \                # office | residential | retail | education | mixed
  --prompt "5 tầng, mỗi tầng 6 phòng, khoảng 120 người" \
  --audience "Nhóm khách hàng mục tiêu" \
  --out frontend/public/artifacts   # writes <id>.glb + <id>.json + refreshes index.json
```
- Leave `--floors/--rooms/--occupancy` out to let `spec_agent` infer them from the
  natural-language `--prompt`; pass them to force exact values.
- `--space mixed` auto-bands floors: retail podium -> office -> residential. Good for
  large towers and for varied 360 scenes. Example (large):
  ```bash
  python -m builder.run --name "Aurora Mixed-Use Tower" --space mixed \
    --floors 30 --rooms 6 --occupancy 2500 \
    --prompt "Phức hợp 30 tầng: đế bán lẻ, khối office, khối căn hộ" \
    --audience "Nhà đầu tư, khách thuê và cư dân" --out frontend/public/artifacts
  ```
- The pipeline seeds an English 360 `panorama.prompt` per room (status `pending`).

## Mode B — Enrich an existing scene + author 360 prompts (data only)
Write a small script `builder/tools/enrich_<id>.py` that loads the bundle JSON,
rewrites `Room.name`/`Room.description` (rich Vietnamese, per floor) and
`Room.panorama.prompt` (English, see format below), optionally improves
`describer`, then re-saves the SAME JSON. Keep `model`/GLB, `id`, `spec`, every
`room_id`, and room counts unchanged. See `CODEX_TASK.md` for a full worked brief.

360 prompt format (consistent across the whole building):
`360 equirectangular interior panorama of <room detail + style + materials>, <lighting>, photorealistic, wide angle, no people`
Future images live at `frontend/public/artifacts/<id>/pano/<room_id>.jpg`; when
generated, set `panorama.image` to that path and `panorama.status = "ready"`.

## LLM provider (subscription note)
- Default `LLM_PROVIDER=mock`: offline, free, deterministic. Enough for geometry +
  baseline copy.
- Richer copy: `export LLM_PROVIDER=claude` + `export ANTHROPIC_API_KEY=sk-ant-...`
  (pay-as-you-go API, a few cents per building). A Claude Pro/Max or ChatGPT/Codex
  **subscription is NOT an API key** and cannot be plugged into the SDK here; run
  agentically with the subscription, but the per-scene text still uses mock or an
  API key. Do not wire unofficial subscription-to-API proxies.

## Rules
- Vietnamese for `name` / `description` / `summary` / `highlights` / `digitization_tips`;
  English for `panorama.prompt`. Zero em-dash (`—`) anywhere; use `-`.
- CPU only. Do not edit `builder/schemas.py`, `builder/pipeline.py`,
  `builder/procedural.py` contract. Never commit `node_modules/` or `.venv/`.

## Verify (definition of done)
```bash
source .venv/bin/activate
python -m pytest -q                       # builder + pipeline + api: must stay green
python - <<'PY'                            # the new/edited bundle validates
import json; from builder.schemas import SceneBundle
b = SceneBundle.model_validate(json.load(open("frontend/public/artifacts/<id>.json")))
assert all(r.panorama and r.panorama.prompt for f in b.structure.floors for r in f.rooms)
print("OK", b.id, b.spec.floors, "floors", b.model.tri_count, "tris")
PY
```
Then view: `cd frontend && npm run dev` -> http://localhost:3000/demo -> pick the
scene -> use Tầng / Tách tầng / Cắt lát and click a room.

## Reference files
`builder/schemas.py` (contract) · `builder/run.py` / `builder/pipeline.py` (entry) ·
`builder/room_agent.py` + `builder/structure.py` + `builder/layout.py` (rooms/360 seed) ·
`CODEX_TASK.md` (enrichment brief) · `WORKFLOW.md` (multi-agent split) · `DESIGN.md` (UI).
