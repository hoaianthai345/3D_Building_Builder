# WORKFLOW — AI 3D Scene Describer (multi-agent)

Tài liệu điều phối để **chia việc song song cho nhiều agent** (Claude / Codex / khác).
Nguyên tắc: **đóng băng contract trước → mọi lane code song song theo contract → tích hợp sau.**

---

## 0. Nguyên tắc phân chia

| Loại việc | Ai làm | Vì sao |
|---|---|---|
| **Critical path** — contract, lõi 3D, orchestration, tích hợp | Agent chính (Claude) | Cần nhất quán, dễ sai contract, ảnh hưởng toàn bộ |
| **Independent / low-risk** — frontend tĩnh, docs, notebook, sample data | Codex / agent phụ | Chỉ phụ thuộc *contract JSON*, không phụ thuộc implementation |

> Quy tắc vàng: agent phụ **không bao giờ** sửa `builder/schemas.py` hay shape của API.
> Nếu cần đổi contract → báo agent chính, bump `version`, sync lại fixtures.

---

## 1. PHASE 0 — Freeze contract (agent chính, BLOCKING ~30')

Tạo và chốt 3 thứ. Sau bước này mọi lane chạy song song.

### 1.1 `builder/schemas.py` (Pydantic v2) — nguồn chân lý

### 1.2 Hợp đồng API
```
POST /api/generate
  body: GenerateRequest {
    project_name, space_type, description,
    target_audience, floors?, rooms_per_floor?, occupancy?
  }
  200 -> SceneBundle (xem 1.3)

GET /static/generated/<id>.glb   # file 3D
GET /api/health
```

### 1.3 `SceneBundle` — artifact mà DEMO đọc (frontend + Vercel)
```json
{
  "id": "office-5f-6r",
  "version": "1.0",
  "input": {
    "project_name": "Sunrise Office Tower",
    "space_type": "office",
    "description": "Tòa văn phòng 5 tầng, mỗi tầng 6 phòng, ~120 người",
    "target_audience": "Doanh nghiệp SME thuê văn phòng",
    "floors": 5, "rooms_per_floor": 6, "occupancy": 120
  },
  "spec": {
    "floors": 5, "rooms_per_floor": 6, "occupancy": 120,
    "footprint_w": 24.0, "footprint_d": 16.0, "floor_height": 3.2,
    "space_type": "office", "layout_hint": "central-core", "palette": "teal"
  },
  "describer": {
    "title": "Sunrise Office Tower — Không gian làm việc hiện đại 5 tầng",
    "summary": "Đoạn mô tả ngắn hấp dẫn ...",
    "highlights": ["...", "...", "...", "..."],
    "digitization_tips": ["...", "...", "..."]
  },
  "model": { "glb": "office-5f-6r.glb", "backend": "procedural",
             "tri_count": 0, "size_kb": 0 },
  "meta": { "llm_provider": "mock", "build_ms": 0, "created_at": "" }
}
```

**Deliverable Phase 0:** `builder/schemas.py` + `frontend/public/artifacts/sample.json` (fixture đúng shape trên) + `frontend/public/artifacts/index.json` (list id). → unblock toàn bộ.

---

## 2. PHASE 1 — Song song (sau Phase 0)

### Lane MAIN — Agent chính (critical, KHÔNG giao Codex)
- `builder/llm/` : `base.py` interface · `mock.py` (default, offline) · `claude.py` (cắm key sau) · `factory.py`
- `builder/spec_agent.py` : NL + params → `BuildingSpec`
- `builder/procedural.py` : `BuildingSpec` → **GLB** (trimesh) — đúng số tầng × số phòng
- `builder/describer.py` : `BuildingSpec` → title/summary/highlights/tips
- `builder/generative.py` : **stub** GPU backend (interface + hướng dẫn TRELLIS/Shap-E)
- `builder/run.py` : CLI `python -m builder.run --prompt ... --out ...`
- `backend/main.py` : FastAPI `/api/generate`
- `builder/tools/bench.py` : đo phần cứng (xem §4)
- `tests/` : pytest builder + api

### Lane FE — Agent phụ #1 (Codex OK) — phụ thuộc CHỈ §1.3 fixture
- Next.js (mượn `Card/Badge/Button/SectionTitle` + theme teal của GreenFlow ở
  `../VinHack/green-flow/src/components/shared/`).
- **Trang 1 — Landing/giới thiệu dự án**: hero + animation (skill
  `framer-motion-animator`, `high-end-visual-design`), mô tả bài toán, sơ đồ kiến
  trúc, link REPORT, CTA "Mở demo".
- **Trang 2 — Demo**: form nhập liệu (trái) + `<model-viewer>` GLB (phải) + cards
  describer (dưới). **Đọc `public/artifacts/*.json` + `.glb` tĩnh** (KHÔNG gọi backend).
- Dùng skill `design-taste-frontend` để tránh giao diện "AI slop".
- Deploy Vercel: `frontend/` là root, static + `<model-viewer>` qua CDN.
- ⚠️ Không hard-code dữ liệu — luôn map từ JSON theo §1.3.

### Lane DOCS — Agent phụ #2 (Codex OK) — phụ thuộc CHỈ §1.2/§1.3
- `README.md` : cách chạy backend (`uvicorn`) + frontend (`npm run dev`) + cắm key.
- `REPORT.md` : khung sẵn — chức năng, cách dùng AI (+1–2 prompt mẫu + cách verify),
  khó khăn, **3 lỗi/điểm UX chưa hợp lý + mức ảnh hưởng + cách cải thiện**, hướng
  phát triển. Chừa chỗ `<<HARDWARE METRICS>>` để agent chính điền số đo thật.
- `colab/build.ipynb` : clone repo → `pip install -r requirements.txt` → chạy
  `builder.run` trên vài prompt mẫu → zip `artifacts/` để tải về.
- `.gitignore`, `frontend/vercel.json`, kịch bản demo 3–5'.

---

## 3. PHASE 2 — Tích hợp (agent chính)
1. Chạy `builder.run` cho 3–4 prompt mẫu → sinh `artifacts/*.glb + *.json` thật.
2. Copy artifacts vào `frontend/public/artifacts/` → thay fixture.
3. Thu thập số đo phần cứng → điền `<<HARDWARE METRICS>>` trong REPORT.
4. Chạy pytest, smoke-test demo, chốt deploy Vercel.

---

## 4. HARDWARE METRICS — đo trong lúc dựng (cho REPORT)

`builder/tools/bench.py` log CSV mỗi lần generate:

| Chỉ số | Cách đo | Đường |
|---|---|---|
| Build time (ms) | `time.perf_counter()` quanh procedural | đo thật |
| Peak RAM (MB) | `tracemalloc` / `resource.getrusage(ru_maxrss)` | đo thật |
| GLB size (KB) | `os.path.getsize` | đo thật |
| Tri/vertex count | `mesh.triangles`, `len(vertices)` | đo thật |
| Độ phức tạp | floors × rooms_per_floor | đo thật |
| LLM latency/token | wrap call (mock≈0; Claude khi có key) | đo thật |
| Frontend bundle | `next build` output | đo thật |

**GPU path (generative — hiện stub, số *ước tính* trích nguồn):**
- TRELLIS: chạy ≥6GB VRAM, Colab T4/L4/A100, GLB export — [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS)
- Shap-E: Colab free T4, nhẹ hơn, output PLY
- Hunyuan3D: ~10–25s/asset (turbo <10s)
- Colab T4 ≈ 16GB VRAM / ~12GB RAM — ghi rõ "projected, not measured (stub)".

---

## 5. SKILLS dùng cho dự án

| Nhu cầu | Skill | Trạng thái |
|---|---|---|
| Frontend cao cấp, chống "AI slop" | `design-taste-frontend` | có sẵn |
| Spacing/typography/shadow cấp agency | `high-end-visual-design` | có sẵn |
| Ảnh tham chiếu design theo section | `imagegen-frontend-web` | có sẵn |
| Animation (framer-motion) | `framer-motion-animator` | **đã cài** |
| 3D viewer web | _không cần skill_ — `@google/model-viewer` (1 web component) hoặc react-three-fiber | dùng trực tiếp |

Optional (không bắt buộc): `0xbigboss/claude-code@react-best-practices` (2.7K),
`eng0ai/eng0-template-skills@awwwards-landing-page` (773).
