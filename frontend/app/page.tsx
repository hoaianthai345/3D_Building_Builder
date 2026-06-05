import {
  PencilSimpleLineIcon,
  BuildingsIcon,
  SparkleIcon,
  TextAaIcon,
  ArticleIcon,
  ListChecksIcon,
  ScanIcon,
} from "@phosphor-icons/react/dist/ssr";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";
import { Reveal } from "@/components/Reveal";
import { ModelViewer } from "@/components/ModelViewer";
import { ButtonLink, Card, SectionLabel } from "@/components/ui";

const HERO_GLB = "/artifacts/sunrise-office-tower-5f-6r.glb";

const STEPS = [
  {
    icon: PencilSimpleLineIcon,
    title: "Nhập thông số",
    body: "Tên dự án, loại không gian và một mô tả ngắn bằng ngôn ngữ tự nhiên.",
  },
  {
    icon: BuildingsIcon,
    title: "Dựng mô hình 3D",
    body: "Bộ dựng procedural tạo khối tòa nhà theo đúng số tầng và số phòng đã nhập.",
  },
  {
    icon: SparkleIcon,
    title: "AI mô tả bối cảnh",
    body: "Sinh tiêu đề, đoạn giới thiệu, điểm nổi bật và lưu ý số hóa cho không gian đó.",
  },
];

export default function Home() {
  return (
    <main>
      <Nav />

      {/* Hero — asymmetric split */}
      <section className="mx-auto grid max-w-[1200px] items-center gap-10 px-5 pb-20 pt-16 lg:grid-cols-[1.05fr_0.95fr] lg:pt-20">
        <Reveal>
          <h1 className="serif text-4xl font-semibold leading-[1.08] tracking-tight md:text-5xl lg:text-[3.3rem]">
            Biến vài dòng mô tả thành mô hình 3D và bản giới thiệu sẵn sàng đăng.
          </h1>
          <p className="mt-5 max-w-[54ch] text-[1.0625rem] leading-relaxed text-[var(--text-muted)]">
            Nhập thông số cơ bản, công cụ dựng khối tòa nhà 3D rồi để AI viết tiêu đề,
            mô tả và các điểm nổi bật.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <ButtonLink href="/demo">Mở demo</ButtonLink>
            <ButtonLink href="#how" variant="secondary">
              Cách hoạt động
            </ButtonLink>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <Card className="h-[360px] overflow-hidden p-0 md:h-[440px]">
            <ModelViewer src={HERO_GLB} alt="Mô hình 3D tòa văn phòng mẫu" />
          </Card>
        </Reveal>
      </section>

      {/* Context band — full width, stacked */}
      <section className="border-y border-[var(--border)] bg-[var(--bg-subtle)]">
        <div className="mx-auto max-w-[1200px] px-5 py-16">
          <Reveal className="max-w-[68ch]">
            <h2 className="serif text-2xl font-semibold tracking-tight md:text-3xl">
              Mỗi dự án số hóa cần một bản mô tả nhất quán và nhanh.
            </h2>
            <p className="mt-4 text-[1.0625rem] leading-relaxed text-[var(--text-muted)]">
              Đội nội dung thường phải viết lại tiêu đề, đoạn giới thiệu và điểm nổi bật cho
              từng không gian. Công cụ này dựng sẵn khối 3D theo thông số và sinh phần mô tả
              theo bối cảnh, để bạn chỉnh sửa thay vì bắt đầu từ trang trắng.
            </p>
          </Reveal>
        </div>
      </section>

      {/* How it works — 2-col: heading left, steps list right */}
      <section id="how" className="mx-auto max-w-[1200px] px-5 py-20">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <Reveal>
            <SectionLabel>Cách hoạt động</SectionLabel>
            <h2 className="serif mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
              Ba bước, từ ý tưởng tới mô hình kèm mô tả.
            </h2>
          </Reveal>

          <div className="divide-y divide-[var(--border)]">
            {STEPS.map((s, i) => (
              <Reveal key={s.title} delay={i * 0.06}>
                <div className="flex gap-4 py-5 first:pt-0">
                  <span className="flex h-11 w-11 flex-none items-center justify-center rounded-[10px] bg-[var(--accent-soft)] text-[var(--accent-hover)]">
                    <s.icon size={22} />
                  </span>
                  <div>
                    <h3 className="text-base font-semibold">{s.title}</h3>
                    <p className="mt-1 text-[var(--text-muted)]">{s.body}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* AI output — bento with background variation */}
      <section id="output" className="border-t border-[var(--border)] bg-[var(--bg-subtle)]">
        <div className="mx-auto max-w-[1200px] px-5 py-20">
          <Reveal>
            <SectionLabel>AI tạo ra gì</SectionLabel>
            <h2 className="serif mt-3 max-w-[24ch] text-3xl font-semibold tracking-tight md:text-4xl">
              Bốn phần nội dung sẵn sàng cho trang giới thiệu.
            </h2>
          </Reveal>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            <Reveal className="md:col-span-1">
              <Card className="h-full p-6">
                <TextAaIcon size={24} className="text-[var(--accent-hover)]" />
                <h3 className="mt-4 text-lg font-semibold">Tiêu đề chuẩn</h3>
                <p className="mt-2 text-[var(--text-muted)]">
                  Một dòng tiêu đề gọn cho trang giới thiệu dự án.
                </p>
              </Card>
            </Reveal>

            <Reveal className="md:col-span-2" delay={0.05}>
              <div className="h-full rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
                <ArticleIcon size={24} className="text-[var(--accent-hover)]" />
                <h3 className="mt-4 text-lg font-semibold">Đoạn mô tả hấp dẫn</h3>
                <p className="mt-2 max-w-[60ch] text-[var(--text-muted)]">
                  Một đoạn ngắn giới thiệu không gian theo bối cảnh và nhóm khách hàng
                  mục tiêu, viết để khách đọc lướt vẫn nắm được giá trị chính.
                </p>
              </div>
            </Reveal>

            <Reveal className="md:col-span-2" delay={0.05}>
              <div className="h-full rounded-2xl border border-[var(--border)] bg-[var(--accent-soft)] p-6">
                <ListChecksIcon size={24} className="text-[var(--accent-hover)]" />
                <h3 className="mt-4 text-lg font-semibold">Ba tới năm điểm nổi bật</h3>
                <p className="mt-2 max-w-[60ch] text-[var(--text-muted)]">
                  AI đề xuất các điểm nổi bật theo loại không gian và quy mô đã nhập, bám
                  vào số tầng, số phòng và sức chứa.
                </p>
              </div>
            </Reveal>

            <Reveal className="md:col-span-1" delay={0.1}>
              <Card className="h-full p-6">
                <ScanIcon size={24} className="text-[var(--accent-hover)]" />
                <h3 className="mt-4 text-lg font-semibold">Lưu ý số hóa 3D</h3>
                <p className="mt-2 text-[var(--text-muted)]">
                  Gợi ý các điểm cần chú ý khi quét loại không gian này.
                </p>
              </Card>
            </Reveal>
          </div>
        </div>
      </section>

      {/* CTA band */}
      <section className="mx-auto max-w-[1200px] px-5 py-20">
        <Reveal>
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--accent-soft)] px-6 py-12 text-center">
            <h2 className="serif text-3xl font-semibold tracking-tight md:text-4xl">
              Thử với dự án của bạn.
            </h2>
            <p className="mx-auto mt-3 max-w-[48ch] text-[var(--text-muted)]">
              Nhập thông số, xem mô hình 3D và phần mô tả AI tạo ra ngay trong trình duyệt.
            </p>
            <div className="mt-7 flex justify-center">
              <ButtonLink href="/demo">Mở demo</ButtonLink>
            </div>
          </div>
        </Reveal>
      </section>

      <Footer />
    </main>
  );
}
