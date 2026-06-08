import {
  ArticleIcon,
  BrainIcon,
  DatabaseIcon,
  ImagesIcon,
  MicrophoneStageIcon,
  PlayCircleIcon,
  SpeakerHighIcon,
  StackIcon,
  WaveformIcon,
} from "@phosphor-icons/react/dist/ssr";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";
import { LandingAudioGuide } from "@/components/LandingAudioGuide";
import { Reveal } from "@/components/Reveal";
import { ButtonLink, Card, SectionLabel } from "@/components/ui";

const HERO_IMAGE = "/landing/councilroom-pan.jpg";
const LANDING_AUDIO_URL = "/audio/landing-guide.mp3";

const FLOW = [
  {
    icon: ImagesIcon,
    title: "Tạo dự án và tải view",
    body: "Người dùng tạo nhiều dự án tour, thêm ảnh thường, ảnh panorama hoặc nguồn ảnh online cho từng điểm dừng.",
  },
  {
    icon: BrainIcon,
    title: "LLM đọc ảnh và viết nội dung",
    body: "Backend gửi ảnh đến Gemini, Groq, OpenAI, Claude hoặc mock AI để sinh tiêu đề, mô tả và điểm nổi bật bằng tiếng Việt.",
  },
  {
    icon: ArticleIcon,
    title: "Biên tập lời dẫn",
    body: "Hệ thống tạo script hướng dẫn viên gồm mở đầu, từng điểm dừng và phần kết; người dùng có thể chỉnh sửa trước khi lưu.",
  },
  {
    icon: SpeakerHighIcon,
    title: "Render giọng nữ và phát tour",
    body: "VieNeu-TTS tạo WAV, lưu lên Supabase Storage nếu đã cấu hình, rồi ghi lại cùng manifest để mở lại tour không phải render audio từ đầu.",
  },
];

const ARCHITECTURE = [
  {
    title: "Frontend",
    body: "Next.js App Router, React state local-first, Tailwind CSS, viewer panorama bằng Three.js/R3F.",
  },
  {
    title: "Backend/API",
    body: "FastAPI nhận upload, đẩy media lên Storage, tải ảnh URL, gọi LLM runtime, tạo script tour và render audio.",
  },
  {
    title: "AI Layer",
    body: "Adapter cho Gemini, Groq, OpenAI, Claude và mock AI; model được chọn theo provider từ dropdown.",
  },
  {
    title: "Audio & Storage",
    body: "VieNeu-TTS sinh giọng nữ, ảnh/audio lưu Supabase Storage khi có cấu hình; project tour lưu Supabase hoặc localStorage fallback.",
  },
];

const SYSTEM_GRAPH = [
  { label: "Landing page", detail: "Giới thiệu, audio guide, video demo slot" },
  { label: "Tour Builder", detail: "Project CRUD, upload ảnh, chọn provider/model" },
  { label: "FastAPI", detail: "Validate request, upload media, điều phối LLM/TTS" },
  { label: "Supabase", detail: "Postgres lưu project, Storage lưu ảnh và WAV" },
  { label: "AI Providers", detail: "Gemini, Groq, OpenAI, Claude hoặc mock AI" },
  { label: "VieNeu-TTS", detail: "Sinh WAV giọng nữ và cache theo script" },
  { label: "Tour Player", detail: "Panorama toàn màn hình, info overlay, audio segment" },
];

const RUNTIME_GRAPH = [
  "Upload panorama",
  "Describe image",
  "Generate script",
  "Edit narration",
  "Render voice",
  "Open saved tour",
];

export default function Home() {
  return (
    <main>
      <Nav />

      <section className="relative min-h-[calc(100dvh-4rem)] overflow-hidden border-b border-[var(--border)]">
        <img
          src={HERO_IMAGE}
          alt="Panorama sảnh lễ tân dùng trong tour tham quan AI"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(20,24,32,0.82),rgba(20,24,32,0.45),rgba(20,24,32,0.18))]" />
        <div className="relative mx-auto flex min-h-[calc(100dvh-4rem)] max-w-[1200px] flex-col justify-center px-5 py-16 text-white">
          <Reveal>
            <p className="inline-flex w-fit rounded-full border border-white/25 bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.16em] text-white/86 backdrop-blur">
              AI Tour Guide Generator
            </p>
            <h1 className="serif mt-5 max-w-[12ch] text-5xl font-semibold leading-[1.02] tracking-tight md:text-6xl lg:text-7xl">
              Tạo tour 3D có thuyết minh AI.
            </h1>
            <p className="mt-5 max-w-[58ch] text-lg leading-relaxed text-white/82">
              Tải ảnh hoặc panorama, để LLM viết lời dẫn hướng dẫn viên, chỉnh sửa script và render giọng nữ bằng VieNeu-TTS cho từng điểm dừng trong tour.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/tour">Mở AI Tour</ButtonLink>
              <ButtonLink href="#demo-video" variant="secondary" className="border-white/35 bg-white/10 text-white hover:bg-white/16">
                Xem video demo
              </ButtonLink>
            </div>
          </Reveal>
        </div>
      </section>

      <section id="overview" className="border-b border-[var(--border)] bg-[var(--bg)]">
        <div className="mx-auto grid max-w-[1200px] gap-10 px-5 py-16 lg:grid-cols-[0.95fr_1.05fr]">
          <Reveal>
            <SectionLabel>Giới thiệu dự án</SectionLabel>
            <h2 className="serif mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
              Dự án tập trung vào một luồng chính: sinh tour tham quan có giọng dẫn.
            </h2>
          </Reveal>
          <Reveal delay={0.08}>
            <div className="space-y-4 text-[1.0625rem] leading-relaxed text-[var(--text-muted)]">
              <p>
                Công cụ này hỗ trợ tạo tour 3D từ bộ ảnh thực tế hoặc panorama. Người dùng quản lý nhiều dự án, sắp xếp lộ trình tham quan, chọn provider AI, sinh mô tả từng view và chuyển script thành audio.
              </p>
              <p>
                Tính năng AI tạo building đã được rút khỏi trang giới thiệu để sản phẩm rõ trọng tâm hơn: AI tour guide, panorama viewer, thông tin nổi trên ảnh và giọng thuyết minh có thể tái sử dụng.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      <section id="flow" className="mx-auto max-w-[1200px] px-5 py-20">
        <Reveal>
          <SectionLabel>Cơ chế hoạt động</SectionLabel>
          <h2 className="serif mt-3 max-w-[23ch] text-3xl font-semibold tracking-tight md:text-4xl">
            Từ ảnh đầu vào tới tour toàn màn hình có audio.
          </h2>
        </Reveal>

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {FLOW.map((step, index) => (
            <Reveal key={step.title} delay={index * 0.05}>
              <Card className="h-full p-6">
                <div className="flex items-start gap-4">
                  <span className="flex h-11 w-11 flex-none items-center justify-center rounded-[10px] bg-[var(--accent-soft)] text-[var(--accent-hover)]">
                    <step.icon size={22} />
                  </span>
                  <div>
                    <p className="text-xs font-semibold text-[var(--text-faint)]">Bước {index + 1}</p>
                    <h3 className="mt-1 text-lg font-semibold">{step.title}</h3>
                    <p className="mt-2 leading-relaxed text-[var(--text-muted)]">{step.body}</p>
                  </div>
                </div>
              </Card>
            </Reveal>
          ))}
        </div>
      </section>

      <section id="architecture" className="border-y border-[var(--border)] bg-[var(--bg-subtle)]">
        <div className="mx-auto max-w-[1200px] px-5 py-20">
          <Reveal>
            <SectionLabel>Architecture sử dụng</SectionLabel>
            <h2 className="serif mt-3 max-w-[24ch] text-3xl font-semibold tracking-tight md:text-4xl">
              Local-first frontend, FastAPI backend và AI provider có thể thay đổi.
            </h2>
          </Reveal>

          <div className="mt-10 grid gap-4 lg:grid-cols-4">
            {ARCHITECTURE.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.05}>
                <Card className="h-full p-5">
                  <StackIcon size={22} className="text-[var(--accent-hover)]" />
                  <h3 className="mt-4 font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--text-muted)]">{item.body}</p>
                </Card>
              </Reveal>
            ))}
          </div>

          <Reveal delay={0.08}>
            <div className="mt-8 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
              <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                  <h3 className="text-lg font-semibold">Architecture graph</h3>
                  <p className="mt-1 max-w-[66ch] text-sm leading-relaxed text-[var(--text-muted)]">
                    Sơ đồ tổng thể các khối chính trong hệ thống AI tour, từ landing page đến player toàn màn hình.
                  </p>
                </div>
                <span className="w-fit rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-medium text-[var(--accent-hover)]">
                  Local-first + API runtime
                </span>
              </div>

              <div className="mt-6 grid gap-3 lg:grid-cols-6">
                {SYSTEM_GRAPH.map((node, index) => (
                  <div key={node.label} className="relative">
                    <div className="min-h-[142px] rounded-[12px] border border-[var(--border)] bg-[var(--bg)] p-4">
                      <p className="text-xs font-semibold text-[var(--text-faint)]">Node {index + 1}</p>
                      <h4 className="mt-2 font-semibold">{node.label}</h4>
                      <p className="mt-2 text-xs leading-relaxed text-[var(--text-muted)]">{node.detail}</p>
                    </div>
                    {index < SYSTEM_GRAPH.length - 1 && (
                      <div className="hidden lg:block absolute left-[calc(100%+2px)] top-1/2 h-px w-[calc(0.75rem-4px)] bg-[var(--border-strong)]" />
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-6 rounded-[12px] border border-[var(--border)] bg-[var(--bg-subtle)] p-4">
                <p className="text-sm font-semibold">Runtime flow graph</p>
                <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">
                  {RUNTIME_GRAPH.map((step, index) => (
                    <div key={step} className="flex items-center gap-2">
                      <span className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-[var(--accent-strong)] text-xs font-semibold text-white">
                        {index + 1}
                      </span>
                      <span className="text-sm text-[var(--text-muted)]">{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="mt-8 grid gap-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 md:grid-cols-3">
              <div className="flex gap-3">
                <DatabaseIcon size={22} className="mt-0.5 flex-none text-[var(--accent-hover)]" />
                <p className="text-sm leading-relaxed text-[var(--text-muted)]">
                  Project state lưu trên trình duyệt để chạy local không cần database.
                </p>
              </div>
              <div className="flex gap-3">
                <WaveformIcon size={22} className="mt-0.5 flex-none text-[var(--accent-hover)]" />
                <p className="text-sm leading-relaxed text-[var(--text-muted)]">
                  Audio WAV được cache theo nội dung script và voice để dùng lại.
                </p>
              </div>
              <div className="flex gap-3">
                <MicrophoneStageIcon size={22} className="mt-0.5 flex-none text-[var(--accent-hover)]" />
                <p className="text-sm leading-relaxed text-[var(--text-muted)]">
                  Manifest tour giữ thứ tự segment, ảnh, mô tả và audio URL.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section id="demo-video" className="mx-auto max-w-[1200px] px-5 py-20">
        <div className="grid gap-8 lg:grid-cols-[0.75fr_1.25fr]">
          <Reveal>
            <SectionLabel>Demo landing flow</SectionLabel>
            <h2 className="serif mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
              Khung gắn video demo và giọng đọc giới thiệu.
            </h2>
            <p className="mt-4 leading-relaxed text-[var(--text-muted)]">
              Gắn file video walkthrough vào div bên cạnh khi có bản quay màn hình. Audio dưới đây là lời dẫn giới thiệu website và flow sử dụng AI tour.
            </p>
            <LandingAudioGuide src={LANDING_AUDIO_URL} />
          </Reveal>

          <Reveal delay={0.08}>
            <div className="rounded-2xl border border-[var(--border-strong)] bg-[var(--surface)] p-3">
              <div className="aspect-video min-h-[280px] overflow-hidden rounded-xl">
                <iframe
                  className="h-full w-full"
                  src="https://www.youtube.com/embed/jDPyOOI60EU"
                  title="Video demo"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                />
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="border-t border-[var(--border)] bg-[var(--bg-subtle)]">
        <div className="mx-auto flex max-w-[1200px] flex-col gap-5 px-5 py-14 md:flex-row md:items-center md:justify-between">
          <Reveal>
            <h2 className="serif text-3xl font-semibold tracking-tight">
              Bắt đầu từ một bộ ảnh tour.
            </h2>
            <p className="mt-2 max-w-[58ch] text-[var(--text-muted)]">
              Trọng tâm hiện tại của dự án là tạo, chỉnh sửa và phát AI tour có thuyết minh.
            </p>
          </Reveal>
          <Reveal delay={0.08}>
            <ButtonLink href="/tour">Tạo AI Tour</ButtonLink>
          </Reveal>
        </div>
      </section>

      <Footer />
    </main>
  );
}
