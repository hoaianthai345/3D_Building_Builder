# DESIGN.md — AI 3D Scene Describer (light, Anthropic-style, tiếng Việt)

Spec giao diện cho **Lane FE** (agent FE / Codex implement). Không build app ở bước này —
đây là design system + cấu trúc trang để code theo.

> **Design Read:** landing + công cụ nhẹ cho người làm nội dung số hóa 3D, ngôn ngữ
> *editorial-calm kiểu Anthropic*, light-mode khóa cứng, copy tiếng Việt, nghiêng về
> Tailwind v4 + serif editorial (display) + grotesque Việt hóa (body) + motion tiết chế.

**Dials:** `DESIGN_VARIANCE: 6` · `MOTION_INTENSITY: 5` · `VISUAL_DENSITY: 3`
(landing calm/premium; trang demo nhích density ~4 vì có form + viewer).

---

## 0. Hai override được biện minh (đọc trước khi áp anti-slop)

1. **Palette giấy-ấm Anthropic + accent BLUE (Cobalt + Cream)** — skill mặc định cấm
   bộ "kem ấm + brass/clay" cho brief premium-consumer. **Override hợp lệ:** nền giấy
   ngà ấm (#FAF9F5 / #F0EEE6) + chữ near-black ấm là *brand-referenced* (Anthropic);
   accent dùng **blue cobalt** theo yêu cầu — đây đúng là cặp **"Cobalt + Cream"** mà
   skill liệt kê là palette nên dùng (1 màu lạnh bão hòa trên 1 nền trung tính, không brass).
2. **Serif cho display** — skill rất hạn chế serif. **Override hợp lệ:** Anthropic dùng
   serif editorial cho heading. Ta dùng serif cho *heading*, sans cho *body*.
   **Không dùng** `Fraunces` / `Instrument Serif` (bị cấm). Chọn serif có **bộ dấu
   tiếng Việt** đầy đủ.
3. **Light-mode only** — skill mặc định bắt dark mode; **người dùng yêu cầu rõ light**.
   → Page Theme Lock = light, khóa toàn trang, không section nào đảo nền.

---

## 1. Tokens màu (CSS variables — chỉ light)

```css
:root {
  /* nền giấy ấm kiểu Anthropic */
  --bg:            #FAF9F5;   /* nền chính (ngà) */
  --bg-subtle:     #F0EEE6;   /* section xen kẽ / nền nhạt */
  --surface:       #FFFFFF;   /* card nổi trên nền ngà */
  --border:        #E7E2D6;   /* viền ấm, mảnh */
  --border-strong: #D8D2C4;

  /* chữ ấm (không pure black) */
  --text:          #1F1E1C;   /* near-black ấm */
  --text-muted:    #6B6760;   /* phụ */
  --text-faint:    #908B81;   /* caption */

  /* accent blue (cobalt) */
  --accent:        #2D5BD0;   /* fill/icon trang trí */
  --accent-strong: #1F4FC4;   /* nền nút (white text đạt AA ~5.5:1) */
  --accent-hover:  #1A43A8;   /* hover/pressed + link text trên nền sáng (AA ~7:1) */
  --accent-soft:   #E7EDFB;   /* tint badge / nền nhấn nhẹ */

  /* trạng thái (giữ tông ấm, ít bão hòa) */
  --ok:    #4F7A52;
  --warn:  #B5832F;
  --danger:#B14A3A;

  --shadow-sm: 0 1px 2px rgba(31,30,28,.05);
  --shadow-md: 0 10px 34px rgba(31,30,28,.07);  /* tint theo nền, không đen tuyền */
}
```

Quy tắc khóa:
- **1 accent duy nhất** (blue cobalt) cho toàn trang. Link/text-accent dùng `--accent-hover` để
  đạt contrast trên nền sáng; nút primary dùng `--accent-strong` + chữ trắng.
- **Không** AI-purple, không gradient neon, shadow luôn ám nâu ấm.

---

## 2. Typography (bắt buộc hỗ trợ dấu tiếng Việt)

Dùng `next/font/google`:

| Vai trò | Font | Vì sao |
|---|---|---|
| Display / heading (serif) | **Lora** (w 500/600) hoặc **Source Serif 4** | serif editorial ấm kiểu Tiempos/Copernicus của Anthropic; **có subset `vietnamese`** |
| Body / UI (sans) | **Be Vietnam Pro** (w 400/500/600) | grotesque trung tính kiểu Styrene; **thiết kế cho tiếng Việt**, dấu chuẩn |
| Mono (số/kỹ thuật, tùy chọn) | **Geist Mono** / **JetBrains Mono** | cho số liệu metric |

```ts
// app/fonts.ts
import { Lora, Be_Vietnam_Pro } from "next/font/google";
export const serif = Lora({ subsets: ["vietnamese","latin"], weight: ["500","600"], variable: "--font-serif" });
export const sans  = Be_Vietnam_Pro({ subsets: ["vietnamese","latin"], weight: ["400","500","600"], variable: "--font-sans" });
```

Thang chữ:
- Hero H1: serif, `text-4xl md:text-5xl lg:text-[3.4rem] tracking-tight leading-[1.1]`, weight 600.
- Section H2: serif, `text-3xl md:text-4xl tracking-tight`.
- Body: sans, `text-base md:text-[1.0625rem] leading-relaxed text-[var(--text-muted)] max-w-[65ch]`.
- Nhấn từ trong heading: dùng *italic cùng font serif*, **không** chèn font khác.

---

## 3. Hình khối, viền, icon, motion

- **Radius (khóa, có quy tắc):** card `rounded-2xl` (16px) · nút & input `rounded-[10px]`
  · badge/pill `rounded-full`. Áp nhất quán toàn trang.
- **Card chỉ dùng khi cần phân cấp thật**; còn lại nhóm bằng `border-t` / khoảng trắng.
- **Icon:** `@phosphor-icons/react` (1 họ duy nhất), weight `regular`, riêng nút bấm dùng
  `bold`. KHÔNG tự vẽ SVG path.
- **Motion (`motion/react`, MOTION 5):** reveal `whileInView` (opacity+translateY 16px,
  ease `[0.16,1,0.3,1]`, stagger 0.06), hover nút `:active` lún `translate-y-[1px]`.
  Bọc `useReducedMotion()`; mọi animation phải giải thích được mục đích. Tối đa **1
  marquee/trang** (mà ở đây không cần marquee). Không scroll-cue, không decoration strip.

---

## 4. Cấu trúc trang

### 4.1 Landing `/` — giới thiệu dự án (áp luật landing)
Tối đa 1 eyebrow / 3 section; ≥4 layout family khác nhau; không 3 card đều nhau lặp lại.

1. **Nav** (1 dòng, cao ≤72px): logo chữ "Scene Describer" · liên kết *Tổng quan ·
   Cách hoạt động · Demo* · nút primary **"Mở demo"**.
2. **Hero** (asymmetric split 55/45): trái = H1 serif (≤2 dòng) + phụ đề (≤20 từ) +
   1 nút primary **"Tạo mô tả 3D"** + 1 nút phụ "Xem cách hoạt động". Phải = ảnh/`<model-viewer>`
   preview 1 tòa nhà. Nền `--bg`. Không version-label, không tagline dưới CTA.
   - H1 gợi ý: *"Biến vài dòng mô tả thành mô hình 3D và lời giới thiệu sẵn sàng đăng."*
   - Phụ đề: *"Nhập loại không gian và thông số cơ bản. Công cụ dựng khối tòa nhà 3D và để AI viết tiêu đề, mô tả, điểm nổi bật."*
3. **Bối cảnh/Vấn đề** (full-width, stack dọc, nền `--bg-subtle`): 1 đoạn ngắn về việc
   số hóa 3D cần mô tả nhất quán, nhanh.
4. **Cách hoạt động** (3 bước, layout không lặp): *Nhập thông số → Dựng mô hình 3D →
   AI mô tả bối cảnh*. Dùng nhãn động-từ trực tiếp (KHÔNG "Bước 1/2/3").
5. **AI tạo ra gì** (bento có biến hóa nền, không toàn card chữ trắng): Tiêu đề chuẩn ·
   Đoạn mô tả hấp dẫn · 3–5 điểm nổi bật · Lưu ý khi số hóa 3D.
6. **Dải CTA**: nền `--accent-soft`, headline ngắn + nút **"Mở demo"** (1 intent CTA toàn trang).
7. **Footer**: tên dự án, liên kết REPORT/README, năm. Không version footer, không locale strip.

### 4.2 Demo `/demo` — công cụ (product styling, density ~4)
Lưới: `grid lg:grid-cols-[minmax(360px,420px)_1fr]`, gap 24px, `max-w-[1400px] mx-auto`.

- **Cột trái — Form** (`bg-surface rounded-2xl border`):
  - Tên dự án (input)
  - Loại không gian (select: *Văn phòng · Tòa nhà ở · Bán lẻ · Hỗn hợp · Giáo dục*)
  - Mô tả ngắn (textarea, placeholder ví dụ: *"Tòa văn phòng 5 tầng, mỗi tầng 6 phòng, khoảng 120 người."*)
  - Số tầng · Số phòng mỗi tầng · Số người (3 input số, hàng grid)
  - Nhóm khách hàng mục tiêu (input)
  - Nút primary full-width **"Tạo mô tả & dựng 3D"**
  - Label LUÔN nằm trên input; helper dưới; lỗi dưới input. Không placeholder-as-label.
- **Cột phải — Viewer 3D** (`bg-bg-subtle rounded-2xl border`, `min-h-[480px]`):
  `<model-viewer>` tải GLB; có nền ngà, camera-controls, auto-rotate nhẹ.
- **Hàng dưới — Kết quả describer** (full-width): 4 khối —
  *Tiêu đề* (serif lớn) · *Mô tả* (đoạn) · *Điểm nổi bật* (list 3–5, mỗi item 1 icon
  phosphor + 1 dòng) · *Lưu ý số hóa 3D* (list). Mỗi khối là card mảnh, viền ấm.

Trạng thái (bắt buộc đủ chu kỳ):
- **Loading:** skeleton đúng hình (khung viewer xám ngà + 3 dòng chữ shimmer), KHÔNG spinner tròn.
- **Empty (chưa tạo):** viewer hiện gợi ý "Nhập thông số bên trái rồi bấm Tạo." + icon nhẹ.
- **Error:** banner inline đỏ-ấm `--danger` dưới nút, câu rõ ràng tiếng Việt.

---

## 5. Component spec nhanh

- **Button primary:** `bg-[var(--accent-strong)] text-white rounded-[10px] px-5 h-11
  font-medium hover:bg-[var(--accent-hover)] active:translate-y-[1px]`. **Kiểm tra
  contrast** (white trên `--accent-strong` ≈ 5.5:1 đạt AA). Nhãn ≤3 từ, không wrap 2 dòng.
- **Button secondary (ghost):** `border border-[var(--border-strong)] text-[var(--text)]
  bg-transparent hover:bg-[var(--bg-subtle)]`.
- **Input/Select/Textarea:** `bg-white border border-[var(--border)] rounded-[10px] h-11
  px-3 text-[var(--text)] placeholder:text-[var(--text-faint)] focus:border-[var(--accent)]
  focus:ring-2 focus:ring-[var(--accent-soft)]`. Helper/label/placeholder đều đạt AA.
- **Badge:** `rounded-full bg-[var(--accent-soft)] text-[var(--accent-hover)] text-xs px-2.5 py-1`.
- **Highlight item:** icon phosphor (blue) + text; nhóm bằng `divide-y` hoặc gap, không
  viền trên+dưới mỗi dòng.

Có thể mượn nguyên `Card/Badge/Button/SectionTitle` từ GreenFlow
(`../VinHack/green-flow/src/components/shared/`) rồi **đổi token sang bộ blue ở §1** (GreenFlow
dùng teal — phải thay hết sang cobalt, không để lẫn teal).

---

## 6. `<model-viewer>` (3D trên web, không cần skill)

```html
<!-- nạp 1 lần, vd trong layout -->
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
```
```tsx
<model-viewer
  src={glbUrl}                 // /artifacts/<id>.glb (tĩnh trên Vercel)
  camera-controls auto-rotate
  shadow-intensity="0.6"
  exposure="1.0"
  style={{ width: "100%", height: "100%", background: "var(--bg-subtle)" }}
/>
```
Khai báo type cho JSX (`model-viewer` là web component). Lazy-load, không chặn LCP hero.

---

## 7. Anti-slop checklist (rút gọn cho dự án này)

- [ ] Zero em-dash `—` trong mọi chữ hiển thị (dùng `-`).
- [ ] 1 theme light khóa toàn trang; 1 accent blue (cobalt) nhất quán; 1 hệ radius.
- [ ] Nút/form đạt WCAG AA; nhãn nút không wrap; 1 intent CTA ("Mở demo").
- [ ] Serif chỉ ở heading, KHÔNG Fraunces/Instrument Serif; font có dấu tiếng Việt.
- [ ] ≤1 eyebrow / 3 section; ≥4 layout family; không 3 card đều lặp lại; bento có biến hóa nền.
- [ ] Có ảnh thật/preview 3D ở hero (không text + gradient suông, không fake screenshot bằng div).
- [ ] Reduced-motion honored; motion có lý do; không scroll-cue/decoration strip/version footer/locale strip.
- [ ] Copy tiếng Việt đọc tự nhiên, không sáo ngữ; số liệu mock có nhãn.
```
