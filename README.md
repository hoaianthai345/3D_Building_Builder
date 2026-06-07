# AI Tour Guide Generator

AI Tour Guide Generator là ứng dụng tạo tour tham quan 3D có thuyết minh AI. Người dùng tạo dự án tour, tải ảnh hoặc panorama, chọn LLM provider, sinh mô tả từng điểm dừng, chỉnh sửa script hướng dẫn viên, render giọng đọc nữ và mở tour toàn màn hình với thẻ thông tin nổi trên ảnh.

## Tính Năng

- Landing page giới thiệu sản phẩm, architecture graph, flow graph, slot video demo, audio guide và nhạc nền loop nhẹ.
- Tour Builder quản lý nhiều dự án: tạo mới, sửa, xóa, upload ảnh, thêm URL ảnh online, thêm panorama mẫu.
- LLM runtime hỗ trợ Gemini, Groq, OpenAI, Claude và mock AI khi không có key.
- Dropdown model theo provider, có thể tải danh sách model từ provider bằng API key người dùng nhập.
- Validate input rỗng, loading state, lỗi API rõ ràng, drag and drop ảnh.
- Preview ảnh lớn trong lộ trình và trong màn chỉnh script.
- Tour Player toàn màn hình, hỗ trợ ảnh panorama 360, ảnh thường, audio thuyết minh và fallback Web Speech.
- VieNeu-TTS tạo giọng nữ, lưu WAV để dùng lại.
- Supabase lưu project tour lâu dài; nếu chưa cấu hình thì fallback localStorage.

## Architecture

```text
Browser / Next.js
  - Landing page
  - Tour Builder
  - Tour Player
  - localStorage fallback
        |
        | NEXT_PUBLIC_API_URL
        v
FastAPI backend
  - /api/describe-image
  - /api/describe-image-url
  - /api/tour
  - /api/tts/generate
  - /api/llm/models
  - /api/tour-projects
        |
        +--> LLM providers: Gemini / Groq / OpenAI / Claude / Mock
        +--> VieNeu-TTS local or remote
        +--> Supabase REST for saved projects
        +--> artifacts/tts for generated audio
```

## Yêu Cầu

- Python 3.11 hoặc 3.12 khuyến nghị.
- Node.js 20+.
- npm.
- ffmpeg chỉ cần nếu muốn tự cắt/nén audio assets.
- Supabase project nếu muốn lưu project tour qua database.

## Cài Đặt Local

### 1. Clone Và Tạo Env

```bash
git clone <your-repo-url>
cd 3D_Building

cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Mặc định backend chạy mock AI nên có thể chạy ngay không cần API key.

### 2. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Kiểm tra:

```bash
curl http://127.0.0.1:8000/api/health
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Mở:

- `http://localhost:3000/` để xem landing page.
- `http://localhost:3000/tour` để tạo tour.

## Chạy Nhanh Bằng Makefile

Sau khi đã tạo `.venv` và cài dependencies:

```bash
make backend
make frontend
make test
```

## Cấu Hình LLM

Có hai cách dùng LLM:

- Nhập API key trực tiếp trong tab Tour AI. Cách này tiện demo, key chỉ gửi theo request, không ghi xuống database.
- Cấu hình provider bằng biến môi trường backend.

Ví dụ Gemini:

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_key_here
export GEMINI_MODEL=gemini-3.5-flash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Ví dụ Groq:

```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_key_here
export GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Các biến khác có trong [.env.example](./.env.example).

## Supabase: Lưu Dự Án Tour

Tạo bảng bằng SQL trong Supabase SQL Editor:

```sql
create table if not exists public.tour_projects (
  id text primary key,
  payload jsonb not null,
  updated_at timestamptz not null default now()
);

create index if not exists tour_projects_updated_at_idx
  on public.tour_projects (updated_at desc);

alter table public.tour_projects enable row level security;
```

File schema có sẵn tại [supabase/schema.sql](./supabase/schema.sql).

Cấu hình backend:

```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
export SUPABASE_TOUR_PROJECTS_TABLE=tour_projects
```

Lưu ý:

- Dùng `service_role` key ở backend, không đưa key này vào frontend.
- Backend gọi Supabase REST.
- Nếu thiếu Supabase env, frontend tự fallback về localStorage.

## VieNeu-TTS

Backend có endpoint `POST /api/tts/generate` để tạo WAV và lưu vào `artifacts/tts`.

Cài TTS local:

```bash
source .venv/bin/activate
pip install -r requirements-tts.txt
export VIENEU_TTS_VOICE="Ngọc Lan"
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Dùng VieNeu-TTS remote server:

```bash
export VIENEU_TTS_MODE=remote
export VIENEU_TTS_API_BASE=http://your-server-ip:23333/v1
export VIENEU_TTS_MODEL=pnnbao-ump/VieNeu-TTS-v2
export VIENEU_TTS_EMOTION=storytelling
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Nếu TTS lỗi hoặc chưa cài, Tour Player vẫn có fallback bằng giọng trình duyệt.

## Docker Backend

```bash
cp .env.example .env
docker compose up --build
```

Backend chạy tại:

```text
http://127.0.0.1:8000
```

Docker image mặc định không cài VieNeu-TTS nặng. Với TTS, ưu tiên dùng remote VieNeu-TTS hoặc cài local ngoài Docker.

## Test Và Build

Backend tests:

```bash
source .venv/bin/activate
pytest
```

Frontend type-check:

```bash
cd frontend
npx tsc --noEmit
```

Frontend production build:

```bash
cd frontend
npm run build
```
