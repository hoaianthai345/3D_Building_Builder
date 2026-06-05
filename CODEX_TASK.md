# CODEX TASK — Làm giàu tòa nhà lớn "Aurora Mixed-Use Tower" + prompt 360

Brief cho **Codex** (lane phụ). Phạm vi lần này: **DATA + prompt 360 mỗi phòng**.
KHÔNG sinh ảnh, KHÔNG dựng viewer panorama, KHÔNG đổi schema/hợp đồng.

---

## 0. Bối cảnh nhanh
- Repo Python (CPU, không GPU). Pipeline đã chạy được: `builder/` sinh GLB + cây cấu trúc
  (`SceneBundle`, schema v1.1). Frontend đọc artifact tĩnh ở `frontend/public/artifacts/`.
- Đã có **baseline**: `frontend/public/artifacts/aurora-mixed-use-tower-30f-6r.json` (+ `.glb`)
  — phức hợp 30 tầng: T1-3 bán lẻ, T4-20 office, T21-30 căn hộ; mỗi phòng đã có
  `panorama.prompt` (status `pending`) do builder seed. Việc của bạn là **nâng chất**.
- Chạy pipeline: `pip install -r requirements.txt` rồi
  `python -m builder.run --name "..." --space mixed --floors 30 --rooms 6 --out frontend/public/artifacts`.

## 1. Hợp đồng (ĐÓNG BĂNG — không sửa)
Nguồn chân lý: `builder/schemas.py`. Các model liên quan: `SceneBundle`, `Structure`,
`Floor`, `Room`, `Panorama`. **Không** đổi tên field, **không** sửa `schemas.py`,
`pipeline.py`, `procedural.py`. Bạn chỉ đọc cấu trúc và **ghi nội dung** vào đúng các field:
```
Room.name           # tiếng Việt, cụ thể theo tầng (vd "Phòng họp lớn T11-02")
Room.description     # tiếng Việt, 2-3 câu, theo bối cảnh phòng + công năng tầng
Room.panorama.prompt # TIẾNG ANH, mô tả nội thất để sinh ảnh 360 (xem §3)
Room.panorama.status # giữ "pending"
Room.panorama.image  # giữ "" (chưa sinh ảnh lần này)
```

## 2. Nhiệm vụ
Tạo script `builder/tools/enrich_aurora.py` (CPU, chạy 1 lệnh) làm các việc sau và GHI ĐÈ
lại bundle JSON (giữ nguyên `model`/GLB, `id`, `spec`):

1. **Biến thể theo tầng**: hiện mỗi band (bán lẻ/office/căn hộ) lặp cùng một chương trình
   phòng. Hãy đa dạng hoá giữa các tầng: tên phòng cụ thể, vài tầng có loại/khác biệt
   (vd tầng office cao có "Phòng họp lớn", "Khu lounge"; tầng căn hộ có "Penthouse" ở
   tầng đỉnh). Số phòng/tầng giữ nguyên để khớp GLB (room_id phải khớp node có sẵn).
2. **Mô tả phòng** (`Room.description`): viết lại phong phú, tự nhiên, tiếng Việt, bám
   công năng + vị trí tầng + nhóm khách (xem `input.target_audience`).
3. **Prompt 360** (`Room.panorama.prompt`): viết prompt tiếng Anh chất lượng cao cho từng
   phòng theo §3. Giữ `status="pending"`, `image=""`.
4. **Mô tả tổng** (`describer`): có thể nâng `summary`/`highlights` cho sát tòa 30 tầng
   mixed-use (giữ 3-5 highlights, >=2 tips — schema yêu cầu).

Nội dung có thể viết tay (hardcode rich data trong script) HOẶC gọi Claude API nếu có
`ANTHROPIC_API_KEY` (tùy chọn). Mặc định phải chạy được offline (nội dung hardcode).

## 3. Định dạng prompt 360 (bắt buộc nhất quán)
- Tiếng Anh, mô tả **equirectangular 360 interior panorama**.
- Cấu trúc: `360 equirectangular interior panorama of <chi tiết phòng theo loại + phong cách + vật liệu>, <ánh sáng>, photorealistic, wide angle, no people`.
- Đồng bộ phong cách toàn tòa (vd "modern minimalist, warm wood and glass") để các ảnh 360
  trông cùng một công trình.
- Ảnh tương lai sẽ lưu `frontend/public/artifacts/<id>/pano/<room_id>.jpg` → khi sinh ảnh,
  điền `panorama.image="<id>/pano/<room_id>.jpg"`, `status="ready"`. Lần này CHƯA làm.

## 4. Ràng buộc
- Tiếng Việt cho `name`/`description`/`summary`; tiếng Anh cho `panorama.prompt`.
- **Zero em-dash** (`—`) trong mọi chuỗi; dùng dấu `-`.
- `room_id` không đổi (phải khớp node GLB và cây cấu trúc) — chỉ đổi nội dung, không đổi số phòng.
- Không sửa `schemas.py`/`pipeline.py`/`procedural.py`; không commit `node_modules`/`.venv`.
- Chạy thuần CPU.

## 5. Tiêu chí hoàn thành (verify)
- `python builder/tools/enrich_aurora.py` chạy xong, ghi `frontend/public/artifacts/aurora-mixed-use-tower-30f-6r.json`.
- JSON hợp lệ với schema:
  ```python
  from builder.schemas import SceneBundle; import json
  SceneBundle.model_validate(json.load(open('frontend/public/artifacts/aurora-mixed-use-tower-30f-6r.json')))
  ```
- Mọi phòng có `panorama.prompt` không rỗng; `description` không rỗng; em-dash = 0.
- Số phòng mỗi tầng và toàn bộ `room_id` khớp với GLB hiện có (mở `/demo`, chọn tòa Aurora,
  bấm Tầng + click phòng → info hiển thị đúng).

## 6. Định nghĩa "xong"
Một bundle Aurora 30 tầng với nội dung phong phú theo tầng + prompt 360 sẵn sàng cho bước
sinh ảnh (Skybox/AI) ở phase sau, không phá vỡ contract và demo hiện tại.
