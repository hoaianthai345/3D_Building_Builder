# BUILD_LOG — Nhật ký xây dựng sản phẩm

Ghi lại ngữ cảnh từng phiên phát triển để làm nguyên liệu viết `REPORT.md`. Mỗi mục
gồm: bối cảnh/yêu cầu, nghiên cứu, quyết định đã chốt với người dùng, việc đã làm, kết
quả (kèm số đo thật), và khó khăn gặp phải.

Sản phẩm: **AI 3D Scene Describer** — nhập thông số tòa nhà bằng ngôn ngữ tự nhiên,
dựng khối 3D + nội thất theo tầng/phòng, và để AI sinh tiêu đề, mô tả, điểm nổi bật,
lưu ý số hóa. Repo: `hoaianthai345/3D_Building_Builder`.

---

## 1. Timeline tổng quan

| Phiên | Ngày | Tính năng | Quyết định chính | Output |
|---|---|---|---|---|
| 1 | 06-05 | Nghiên cứu + plan | Lõi 3D = procedural trimesh→GLB; FE Next.js; LLM mock-first; spec-agent NL→thông số | Hướng kiến trúc |
| 2 | 06-05 | Tách Colab/Vercel | FE tĩnh trên Vercel; build trên Colab/CPU; repo chạy được trên máy GPU | Kiến trúc 3 lớp |
| 3 | 06-05 | Workflow đa-agent + skill + metrics | Freeze contract → lane song song; cài skill animation; bench đo CPU | `WORKFLOW.md` |
| 4 | 06-05 | Design system | Light mode, phong cách Anthropic, tiếng Việt, accent đổi clay→**blue** | `DESIGN.md` |
| 5 | 06-05 | Phase 0 + lõi builder | Đóng băng `schemas.py`; builder + backend + tests + Docker | builder/, backend/, 9/9 test |
| 6 | 06-05 | Frontend | Landing + demo, R3F sau này; build pass | frontend/ |
| 7 | 06-05 | Colab notebook | Clone hoặc upload zip; xem 3D inline; preset GreenFlow | `colab/build.ipynb` |
| 8 | 06-05 | Drill-down Explorer (Phase 1) | Hybrid: R3F trước, panorama AI sau; schema v1.1 + nội thất | `Explorer.tsx`, structure tree |
| 9 | 06-06 | Push GitHub | Đẩy `main` chuẩn bị Colab | repo public |
| 10 | 06-06 | Tòa lớn + brief Codex | Mixed-use 30 tầng; contract 360 (`Room.panorama`); per-floor program | Aurora baseline, `CODEX_TASK.md` |
| 11 | 06-06 | Skill repo | Đóng gói pipeline thành skill tái dùng | `.claude/skills/build-3d-building/` |
| 12 | 06-06 | Codex làm giàu Aurora + review | Codex enrich nội dung + prompt 360; contract-owner review PASS | `enrich_aurora.py`, JSON đã enrich |
| 13 | 06-06 | Panorama 360 "Bước vào" (phase 2) | Viewer R3F (đổi từ photo-sphere-viewer do xung đột `three`); tool placeholder CPU + Skybox | `PanoramaViewer`, gen tools, 30 ảnh demo |
| 14 | 06-06 | Realism: vỏ procedural + backend TRELLIS | Giữ procedural (CPU) nâng cấp curtain-wall + thêm generative (GPU); user chọn backend | Vỏ ngoài, `generate_from_image`, `trellis_build.ipynb` |

---

## 2. Công cụ AI/LLM đã dùng (cho phần "Cách dùng AI" của report)

| Công cụ | Dùng để làm gì | Kiểm tra output |
|---|---|---|
| **Claude Code (Opus 4.8)** | Agent chính: nghiên cứu, lên plan, viết toàn bộ code/builder/frontend/docs | Chạy `pytest`, `next build`, render thật, đọc lại diff |
| **WebSearch** | Research tooling 3D (Holodeck/SceneCraft/3D-GPT, Alpha3D, TRELLIS/Shap-E, trimesh, R3F, photo-sphere-viewer, Skybox AI) | So nhiều nguồn, ghi link trong `WORKFLOW.md` |
| **Skill `design-taste-frontend`** | Chuẩn hoá design light/Anthropic, tránh "AI slop" | Áp checklist anti-slop trong `DESIGN.md` |
| **Skill `framer-motion-animator`** (cài qua skills.sh) | Hướng dẫn animation FE | Reveal có honor `prefers-reduced-motion` |
| **Skill `find-skills`** | Tìm skill 3D/animation cần cài | Lọc theo install count/uy tín |
| **MockLLM (offline)** | Mặc định sinh spec + chương trình phòng + mô tả tiếng Việt | Validate bằng `DescriberOutput`/`SceneBundle` |
| **Claude API (tùy chọn)** | Nâng chất mô tả khi có `ANTHROPIC_API_KEY` | Fallback về mock nếu lỗi |
| **Codex (giao lane phụ)** | Làm giàu nội dung + viết prompt 360 (`CODEX_TASK.md`) | `SceneBundle.model_validate` |

**Prompt mẫu (1):** brief cho skill design — "Design system spec (DESIGN.md)... LIGHT MODE,
Anthropic-like (warm cream paper, accent), editorial serif + clean sans, copy tiếng Việt..."
→ kết quả kiểm tra bằng checklist anti-slop (zero em-dash, 1 accent, contrast AA).

**Prompt mẫu (2):** prompt describer trong `builder/prompts.py` — "Viết nội dung giới
thiệu cho một dự án số hóa 3D. Trả JSON với khóa title, summary, highlights (3-5),
digitization_tips..." → kiểm tra bằng `DescriberOutput.model_validate` (ép đúng 3-5 highlight).

**Cách verify chung:** mọi output AI đi qua schema Pydantic (ép cấu trúc), test `pytest`
9/9, build `next build`, và render thật (Chrome headless + xem trực tiếp).

---

## 3. Chi tiết từng phiên

### Phiên 1 — Nghiên cứu nền + plan (06-05)
- **Bối cảnh:** đề bài "AI 3D Scene Describer", xây dựng dựa trên ý tưởng dự án VinHack.
- **Nghiên cứu:** đọc GreenFlow (Next.js dashboard, nhúng Sketchfab iframe, data mock,
  kiến trúc agent HVAC) — phần "3D" của nó KHÔNG generate, chỉ nhúng model có sẵn. Khảo
  sát landscape: research-grade LLM→3D (Holodeck, SceneCraft, 3D-GPT — nặng, cần GPU/Blender),
  thương mại (Alpha3D — trả phí, sinh vật thể), procedural Python (trimesh — nhẹ, CPU).
- **Quyết định (chốt 4 câu hỏi):** procedural trimesh→GLB · FE Next.js mượn GreenFlow ·
  LLM abstraction mock-trước-cắm-key-sau · có spec-agent NL→thông số.

### Phiên 2 — Tách Colab/Vercel (06-05)
- **Bối cảnh:** người dùng thêm yêu cầu: 1 FE cho landing+demo+giới thiệu, deploy Vercel,
  dựng model bằng tài nguyên Colab, repo vẫn build được trên máy GPU.
- **Nghiên cứu:** TRELLIS (Colab T4/L4/A100, ≥6GB VRAM, GLB), Shap-E (Colab free), Hunyuan3D
  (~10-25s) — đều sinh vật thể, không phải tòa nhà nhiều tầng theo phòng.
- **Quyết định:** procedural-only (Colab/GPU-ready, GPU optional) · demo Vercel đọc
  **artifact tĩnh**. Kiến trúc 3 lớp: FE tĩnh ↔ builder (Colab/CPU) ↔ backend (local/GPU).

### Phiên 3 — Workflow đa-agent + skill + metrics (06-05)
- **Bối cảnh:** muốn chia việc cho nhiều agent (Codex), tìm skill (FE đẹp/animation/3D),
  ước tính phần cứng cho report.
- **Đã làm:** `WORKFLOW.md` (Phase 0 freeze contract → lane MAIN/FE/DOCS song song). Cài
  `framer-motion-animator`; xác định 3D không cần skill (dùng `<model-viewer>`). Lập kế
  hoạch `bench.py`.
- **Khó khăn:** macOS không có lệnh `timeout` → bỏ khi gọi `npx skills`.

### Phiên 4 — Design system (06-05)
- **Bối cảnh:** light mode, giống Anthropic, tiếng Việt; sau đó đổi accent clay→**blue cobalt**.
- **Đã làm:** `DESIGN.md` (nền giấy ngà ấm + accent blue "Cobalt + Cream"; serif Lora +
  Be Vietnam Pro hỗ trợ dấu; tokens; cấu trúc landing+demo; biện minh override palette/serif).

### Phiên 5 — Phase 0 contract + lõi builder (06-05)
- **Đã làm:** `schemas.py` (contract đóng băng, validate fixture). `procedural.py`
  (trimesh→GLB), LLM layer (mock/claude/fallback), `spec_agent`, `describer`, `pipeline`,
  `run.py`, FastAPI `backend/main.py`, `bench.py`, tests, Docker. Sinh 3 artifact demo.
- **Kết quả (đo thật):** 5×6 = 87ms, 1.9k tris, 75KB; 40×10 = 1.4s, 18MB RAM, 24k tris,
  1MB. **Tests 9/9 pass.**
- **Khó khăn:** màu GLB phải gán qua `PBRMaterial`+`TextureVisuals` để sống sót trong
  model-viewer (verify bằng reload trimesh).

### Phiên 6 — Frontend (06-05)
- **Đã làm:** Next.js 15 + Tailwind v4 + Lora/Be Vietnam Pro + Phosphor + motion. Landing
  (hero asymmetric, dải bối cảnh, cách hoạt động, bento, CTA) + demo (form + viewer +
  cards). `next build` pass, prerender tĩnh; chụp ảnh kiểm tra.
- **Khó khăn:** model-viewer trống trong ảnh chụp Chrome headless (WebGL một-nhịp) — render
  thật trong trình duyệt vẫn đúng.

### Phiên 7 — Colab notebook (06-05)
- **Đã làm:** `colab/build.ipynb` (clone repo hoặc upload zip; cài deps; chạy pipeline;
  xem GLB inline bằng base64+model-viewer; tải artifact). Thêm preset GreenFlow OfficeSmall.
- **Khó khăn:** `NotebookEdit` cần `cell_id` (notebook chưa có id) → ghi lại bằng Write.

### Phiên 8 — Drill-down Explorer / Phase 1 (06-05)
- **Bối cảnh:** cần "đi sâu vào từng phòng và cấu trúc" — sản phẩm là 3D view tham quan web.
- **Nghiên cứu:** R3F + drei (clipping/exploded/select), r3f-cutter, photo-sphere-viewer/
  pannellum (tour 360), Skybox AI (text→360). Chốt **Hybrid** (R3F trước, panorama AI sau).
- **Đã làm:** schema **v1.1** (`Structure` floors→rooms), `layout.py` (chia ô không đều),
  `room_agent` (LLM chương trình phòng), nội thất dollhouse trong `procedural.py`, mô tả
  từng phòng, **Explorer R3F** (tách tầng / cắt lát / tách 1 tầng / click phòng → info).
- **Kết quả:** model nội thất 5×6 = 1.9k tris/75KB; tests 9/9; build pass; render thật OK.
- **Khó khăn:** React 19 + R3F làm props `model-viewer` thành `never` → cast `any`. Chrome
  headless cần cờ swiftshader để render WebGL của R3F.

### Phiên 9 — Push GitHub (06-06)
- **Đã làm:** `git init` + commit + push lên `hoaianthai345/3D_Building_Builder` (main).
  Kiểm tra không lọt `node_modules`/`.venv`/`.DS_Store` (59 files, 688KB).

### Phiên 10 — Tòa lớn mixed-use + brief Codex (06-06)
- **Bối cảnh:** dùng Codex dựng trước một building lớn thật sự để mock demo, đầy đủ scene/
  nội thất, chuẩn bị asset 360.
- **Quyết định:** mixed-use ~30 tầng (T1-3 bán lẻ, T4-20 office, T21-30 căn hộ) · Codex làm
  **data + prompt 360/phòng**.
- **Đã làm:** mở rộng contract — `Room.panorama {prompt,image,status}` (builder tự seed
  prompt 360 English); `room_agent` per-floor + banding mixed-use; dựng **Aurora 30 tầng**
  (180 phòng, 8 loại, 11.2k tris, 475KB, 163ms CPU); viết `CODEX_TASK.md`.

### Phiên 11 — Skill repo (06-06)
- **Đã làm:** `.claude/skills/build-3d-building/SKILL.md` — playbook tái dùng (Mode A dựng
  mới, Mode B làm giàu + prompt 360, contract, provider, verify). Ghi rõ **subscription ≠
  API key**.

### Phiên 12 — Codex làm giàu Aurora + review (06-06)
- **Bối cảnh:** giao Codex theo `CODEX_TASK.md` (data + prompt 360, không sinh ảnh).
- **Đã làm (Codex):** `builder/tools/enrich_aurora.py` → ghi đè bundle Aurora; tên + mô tả
  tiếng Việt theo band (retail / office / residential / penthouse); prompt 360 English cho
  mỗi phòng; giữ `status=pending`, `image=""`.
- **Review (contract-owner):** schema validate OK; 180 `room_id` khớp baseline; `spec`/
  `model`/`id` giữ nguyên; mọi phòng có prompt + description; pano pending + no image;
  em-dash = 0 → **PASS**.
- **Khó khăn/ghi chú:** thay đổi Codex bị gộp vào commit `6e5e11b` (do `git add -A` cùng
  lúc) — đã push, vô hại, chỉ là message không mô tả phần enrich.

### Phiên 13 — Panorama 360 "Bước vào" / Phase 2 (06-06)
- **Bối cảnh:** gắn tham quan 360 vào nút "Bước vào" trong Explorer.
- **Đã làm:** `PanoramaViewer` (sphere equirect mặt trong, dựng bằng R3F sẵn có); wire nút
  "Bước vào" + modal trong Explorer (bật khi `panorama.status=ready`); 2 tool sinh ảnh —
  `gen_placeholder_panoramas.py` (CPU/Pillow, offline) và `gen_panoramas.py` (Skybox AI,
  cần key); sinh 30 placeholder cho scene office (status ready) để demo chạy ngay.
- **Khó khăn:** `@photo-sphere-viewer/core` xung đột peer `three` với R3F (0.17x) → chuyển
  sang sphere R3F (cùng stack, không thêm dep). `@google/model-viewer` ghim peer `three^0.163`
  vs 0.171 → thêm `frontend/.npmrc` `legacy-peer-deps=true` để install sạch (local + Vercel).
- **Kết quả:** build pass; chụp xác nhận panorama render đúng; ảnh 360 phục vụ HTTP 200.

### Phiên 14 — Realism: vỏ procedural + backend TRELLIS (06-06)
- **Bối cảnh:** phản hồi "demo 3D vô nghĩa, không kết cấu". Chọn giữ Hướng 1 (procedural,
  CPU, chạy mọi máy) + thêm Hướng 4 (TRELLIS, GPU) + cho user chọn backend.
- **Đã làm:**
  - *Nâng procedural:* thêm **vỏ ngoài** curtain-wall (kính + mullion), slab tầng đua ra,
    mái + parapet, canopy lối vào, mặt đất; nội thất inset bên trong. Explorer: nút **"Vỏ
    ngoài"** (mặc định hiện ngoại thất; tách tầng / chọn tầng / ẩn vỏ để lộ phòng).
  - *Backend generative:* `generative.image_to_glb` (TRELLIS, lazy import, CPU-safe),
    `pipeline.bundle_from_glb` + `generate_from_image`, CLI `--image`, `colab/trellis_build.ipynb`.
    Scene generative `structure=None` → frontend hiện model-viewer (không drill).
- **Kết quả:** procedural 5×6 ~3.5k tris/152KB (40×10 ~42k/1.85MB, 2.9s, vẫn CPU); tests
  10/10; build pass; chụp xác nhận tòa nhà curtain-wall thật. Aurora rebuild GLB vỏ mới
  giữ nguyên nội dung Codex.
- **Khó khăn:** cân bằng realism vs tri-count (gói kính/mullion theo cột để chặn số mặt);
  HMR dev hỏng sau nhiều đổi dep → xoá `.next` restart.

---

## 4. Nguyên liệu cho REPORT.md (gợi ý ánh xạ)

- **Chức năng đã làm:** form nhập liệu (NL + thông số) → API → spec-agent → builder
  procedural (khối + nội thất theo tầng/phòng, bố cục không đều) → describer (tiêu đề, mô
  tả, 3-5 điểm nổi bật, lưu ý số hóa) → SceneBundle; FE landing + demo + **Explorer 3D**
  (tách tầng/cắt lát/tách tầng/click phòng); Colab pipeline; Docker; skill tái dùng.
- **Cách dùng AI/LLM:** xem §2 (công cụ, 2 prompt mẫu, cách verify qua schema + test + build).
- **Khó khăn gặp phải:** màu GLB (PBRMaterial), WebGL headless, JSX typing R3F/React 19,
  NotebookEdit cell_id, `timeout` trên macOS, refactor per-floor program, ranh giới
  subscription vs API key.
- **3 lỗi/điểm chưa hợp lý (quan sát — điền khi viết report):** ví dụ ứng viên: (a) demo
  tĩnh "Tạo" chỉ khớp scene gần nhất chứ không sinh thật trên Vercel; (b) khối nội thất là
  block-massing, chưa có nội thất chi tiết; (c) chip "Tầng" với tòa 30 tầng nhiều nút.
- **Hướng cải thiện nếu thêm thời gian:** panorama 360 "Bước vào" (Skybox + photo-sphere-
  viewer), generative GPU backend (TRELLIS/Shap-E), camera auto-fit khi chọn phòng, layout
  LLM non-uniform thật, README/REPORT hoàn chỉnh.
