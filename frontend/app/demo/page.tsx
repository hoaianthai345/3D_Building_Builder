"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  ArrowLeftIcon,
  SparkleIcon,
  ListChecksIcon,
  ScanIcon,
  CubeIcon,
} from "@phosphor-icons/react";
import { ModelViewer } from "@/components/ModelViewer";
import {
  type ArtifactIndex,
  type SceneBundle,
  type SpaceType,
  SPACE_LABELS,
} from "@/lib/types";

const Explorer = dynamic(() => import("@/components/Explorer").then((m) => m.Explorer), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--bg-subtle)] text-sm text-[var(--text-faint)]">
      Đang tải trình xem 3D...
    </div>
  ),
});

const API_BASE = process.env.NEXT_PUBLIC_API_URL; // set -> live backend; unset -> static

type FormState = {
  project_name: string;
  space_type: SpaceType;
  description: string;
  target_audience: string;
  floors: string;
  rooms_per_floor: string;
  occupancy: string;
};

const EMPTY_FORM: FormState = {
  project_name: "",
  space_type: "office",
  description: "",
  target_audience: "",
  floors: "",
  rooms_per_floor: "",
  occupancy: "",
};

function num(value: string): number | null {
  const n = parseInt(value, 10);
  return Number.isFinite(n) ? n : null;
}

function nearest(scenes: SceneBundle[], form: FormState): SceneBundle | null {
  if (scenes.length === 0) return null;
  const sameType = scenes.filter((s) => s.spec.space_type === form.space_type);
  const pool = sameType.length ? sameType : scenes;
  const f = num(form.floors) ?? 0;
  const r = num(form.rooms_per_floor) ?? 0;
  return [...pool].sort(
    (a, b) =>
      Math.abs(a.spec.floors - f) + Math.abs(a.spec.rooms_per_floor - r) -
      (Math.abs(b.spec.floors - f) + Math.abs(b.spec.rooms_per_floor - r)),
  )[0];
}

export default function DemoPage() {
  const [scenes, setScenes] = useState<SceneBundle[]>([]);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [result, setResult] = useState<SceneBundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"static" | "live" | null>(null);

  // Load prebuilt artifacts once; seed the form + initial preview from the first.
  useEffect(() => {
    (async () => {
      try {
        const idx: ArtifactIndex = await fetch("/artifacts/index.json").then((r) => r.json());
        const loaded: SceneBundle[] = await Promise.all(
          idx.scenes.map((id) => fetch(`/artifacts/${id}.json`).then((r) => r.json())),
        );
        setScenes(loaded);
        if (loaded[0]) {
          loadInto(loaded[0]);
          setResult(loaded[0]);
        }
      } catch {
        setError("Không tải được dữ liệu mẫu. Kiểm tra thư mục /artifacts.");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadInto(s: SceneBundle) {
    setForm({
      project_name: s.input.project_name,
      space_type: s.input.space_type,
      description: s.input.description,
      target_audience: s.input.target_audience,
      floors: String(s.spec.floors),
      rooms_per_floor: String(s.spec.rooms_per_floor),
      occupancy: String(s.spec.occupancy),
    });
  }

  async function onGenerate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (API_BASE) {
        const res = await fetch(`${API_BASE}/api/generate`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            project_name: form.project_name || "Dự án chưa đặt tên",
            space_type: form.space_type,
            description: form.description,
            target_audience: form.target_audience,
            floors: num(form.floors),
            rooms_per_floor: num(form.rooms_per_floor),
            occupancy: num(form.occupancy),
          }),
        });
        if (!res.ok) throw new Error(`API trả về ${res.status}`);
        setResult(await res.json());
        setMode("live");
      } else {
        const match = nearest(scenes, form);
        if (!match) throw new Error("Chưa có dữ liệu mẫu để hiển thị.");
        setResult(match);
        setMode("static");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const glbSrc = useMemo(() => {
    if (!result) return null;
    const base = API_BASE && mode === "live" ? API_BASE : "";
    return `${base}/artifacts/${result.model.glb}`;
  }, [result, mode]);

  const inputCls =
    "h-11 w-full rounded-[10px] border border-[var(--border)] bg-white px-3 text-sm text-[var(--text)] placeholder:text-[var(--text-faint)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-soft)]";
  const labelCls = "mb-1.5 block text-sm font-medium text-[var(--text)]";

  return (
    <main className="min-h-[100dvh]">
      <div className="mx-auto max-w-[1320px] px-5 py-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
        >
          <ArrowLeftIcon size={16} /> Về trang giới thiệu
        </Link>

        <div className="mt-4">
          <h1 className="serif text-3xl font-semibold tracking-tight">Tạo mô tả và dựng 3D</h1>
          <p className="mt-1 text-[var(--text-muted)]">
            Nhập thông số, xem mô hình khối tòa nhà và phần mô tả do AI tạo.
          </p>
        </div>

        <div className="mt-7 grid gap-6 lg:grid-cols-[minmax(340px,400px)_1fr]">
          {/* Form */}
          <form
            onSubmit={onGenerate}
            className="h-fit rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5"
          >
            {scenes.length > 0 && (
              <div className="mb-5">
                <span className={labelCls}>Dự án mẫu</span>
                <div className="flex flex-wrap gap-2">
                  {scenes.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => {
                        loadInto(s);
                        setResult(s);
                        setMode(null);
                      }}
                      className="rounded-full border border-[var(--border-strong)] px-3 py-1 text-xs text-[var(--text-muted)] hover:bg-[var(--bg-subtle)] hover:text-[var(--text)]"
                    >
                      {s.input.project_name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className={labelCls} htmlFor="name">Tên dự án</label>
                <input
                  id="name"
                  className={inputCls}
                  value={form.project_name}
                  onChange={(e) => setForm({ ...form, project_name: e.target.value })}
                  placeholder="Sunrise Office Tower"
                />
              </div>

              <div>
                <label className={labelCls} htmlFor="space">Loại không gian</label>
                <select
                  id="space"
                  className={inputCls}
                  value={form.space_type}
                  onChange={(e) => setForm({ ...form, space_type: e.target.value as SpaceType })}
                >
                  {(Object.keys(SPACE_LABELS) as SpaceType[]).map((k) => (
                    <option key={k} value={k}>
                      {SPACE_LABELS[k]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelCls} htmlFor="desc">Mô tả ngắn</label>
                <textarea
                  id="desc"
                  rows={3}
                  className={`${inputCls} h-auto py-2.5`}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Tòa văn phòng 5 tầng, mỗi tầng 6 phòng, khoảng 120 người."
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className={labelCls} htmlFor="floors">Số tầng</label>
                  <input id="floors" inputMode="numeric" className={inputCls}
                    value={form.floors}
                    onChange={(e) => setForm({ ...form, floors: e.target.value })} placeholder="5" />
                </div>
                <div>
                  <label className={labelCls} htmlFor="rooms">Phòng/tầng</label>
                  <input id="rooms" inputMode="numeric" className={inputCls}
                    value={form.rooms_per_floor}
                    onChange={(e) => setForm({ ...form, rooms_per_floor: e.target.value })} placeholder="6" />
                </div>
                <div>
                  <label className={labelCls} htmlFor="occ">Số người</label>
                  <input id="occ" inputMode="numeric" className={inputCls}
                    value={form.occupancy}
                    onChange={(e) => setForm({ ...form, occupancy: e.target.value })} placeholder="120" />
                </div>
              </div>

              <div>
                <label className={labelCls} htmlFor="aud">Nhóm khách hàng mục tiêu</label>
                <input
                  id="aud"
                  className={inputCls}
                  value={form.target_audience}
                  onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
                  placeholder="Doanh nghiệp SME thuê văn phòng"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="h-11 w-full rounded-[10px] bg-[var(--accent-strong)] text-sm font-medium text-white transition hover:bg-[var(--accent-hover)] active:translate-y-[1px] disabled:opacity-60"
              >
                {loading ? "Đang tạo..." : "Tạo mô tả và dựng 3D"}
              </button>

              {error && (
                <p className="rounded-[10px] border border-[var(--danger)]/30 bg-[var(--danger)]/5 px-3 py-2 text-sm text-[var(--danger)]">
                  {error}
                </p>
              )}
              <p className="text-xs text-[var(--text-faint)]">
                {API_BASE
                  ? "Chế độ live: backend sinh mô hình và mô tả trực tiếp."
                  : "Bản demo tĩnh hiển thị dự án mẫu dựng sẵn gần nhất. Bản đầy đủ chạy backend để sinh trực tiếp."}
              </p>
            </div>
          </form>

          {/* Viewer + result */}
          <div className="space-y-6">
            <div className="h-[460px]">
              {result && result.structure && glbSrc ? (
                <Explorer bundle={result} glbUrl={glbSrc} />
              ) : (
                <div className="relative h-full overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--bg-subtle)]">
                  {glbSrc ? (
                    <ModelViewer src={glbSrc} alt={`Mô hình 3D ${result?.input.project_name ?? ""}`} />
                  ) : (
                    <div className="flex h-full flex-col items-center justify-center text-center text-[var(--text-faint)]">
                      <CubeIcon size={40} />
                      <p className="mt-2 text-sm">Nhập thông số bên trái rồi bấm Tạo.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
            {result && (
              <p className="text-xs text-[var(--text-faint)]">
                {result.model.backend === "generative"
                  ? "Mô hình AI (TRELLIS)"
                  : `${result.spec.floors} tầng x ${result.spec.rooms_per_floor} phòng`} ·{" "}
                {result.model.tri_count.toLocaleString("vi-VN")} tam giác · {result.model.size_kb} KB ·
                LLM {result.meta.llm_provider}
                {result.structure
                  ? " · Kéo để xoay, bấm phòng để xem chi tiết"
                  : " · Mô hình một khối, không có drill phòng"}
              </p>
            )}

            {result && (
              <div className="space-y-4">
                <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent-hover)]">
                    Tiêu đề
                  </p>
                  <h2 className="serif mt-2 text-2xl font-semibold tracking-tight">
                    {result.describer.title}
                  </h2>
                  <p className="mt-3 leading-relaxed text-[var(--text-muted)]">
                    {result.describer.summary}
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--accent-soft)] p-6">
                    <div className="flex items-center gap-2 text-[var(--accent-hover)]">
                      <ListChecksIcon size={20} />
                      <h3 className="font-semibold">Điểm nổi bật</h3>
                    </div>
                    <ul className="mt-3 space-y-2.5">
                      {result.describer.highlights.map((h, i) => (
                        <li key={i} className="flex gap-2 text-sm text-[var(--text)]">
                          <SparkleIcon size={16} className="mt-0.5 flex-none text-[var(--accent)]" />
                          <span>{h}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
                    <div className="flex items-center gap-2 text-[var(--accent-hover)]">
                      <ScanIcon size={20} />
                      <h3 className="font-semibold">Lưu ý số hóa 3D</h3>
                    </div>
                    <ul className="mt-3 space-y-2.5">
                      {result.describer.digitization_tips.map((t, i) => (
                        <li key={i} className="flex gap-2 text-sm text-[var(--text-muted)]">
                          <span className="mt-2 h-1.5 w-1.5 flex-none rounded-full bg-[var(--accent)]" />
                          <span>{t}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
