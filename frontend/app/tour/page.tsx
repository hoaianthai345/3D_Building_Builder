"use client";

import { type DragEvent as ReactDragEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeftIcon, ArrowUpIcon, ArrowDownIcon, TrashIcon, ImagesIcon,
  PlayIcon, PauseIcon, CaretLeftIcon, CaretRightIcon, ArrowCounterClockwiseIcon, SparkleIcon,
} from "@phosphor-icons/react";
import {
  type IndustryTone, type StopDescribe, type Tour, type TourManifest,
  INDUSTRY_LABELS, VISION_TPL,
} from "@/lib/types";
import { PanoramaViewer } from "@/components/PanoramaViewer";

const API_BASE_ENV = process.env.NEXT_PUBLIC_API_URL?.trim();
const STATIC_MODE = API_BASE_ENV === "static";
const API_BASE = STATIC_MODE
  ? ""
  : (API_BASE_ENV || "http://127.0.0.1:8000").replace(/\/$/, "");

type RawStop = {
  id: string;
  src: string;
  file?: File;
  kind: "photo" | "panorama";
  source: "file" | "url" | "sample";
  remoteUrl?: string;
};

type TourWithAudio = Tour & {
  audio?: Record<string, string>;
  audioErrors?: Record<string, string>;
  audioGeneratedAt?: string;
  manifest?: TourManifest;
  routeSignature?: string;
};

type TourProject = {
  id: string;
  name: string;
  industry: IndustryTone;
  stops: RawStop[];
  savedTour?: TourWithAudio | null;
  updatedAt: string;
};

type LlmProvider = "gemini" | "openai" | "claude" | "groq";
type LoadingState = {
  title: string;
  detail: string;
  progress: number;
};
type ProjectStoreStatus = "checking" | "local" | "supabase" | "error";

const PROJECT_STORAGE_KEY = "scene-describer-tour-projects-v1";
const MAX_SOURCE_IMAGE_MB = 80;
const TARGET_UPLOAD_IMAGE_MB = 7.5;
const DEFAULT_TTS_VOICE = "Ngọc Lan";
const LLM_MODEL_OPTIONS: Record<LlmProvider, string[]> = {
  gemini: ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"],
  openai: ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
  claude: ["claude-sonnet-4-6", "claude-sonnet-4-5", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
  groq: [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
  ],
};
const LLM_MODEL_DEFAULTS: Record<LlmProvider, string> = {
  gemini: LLM_MODEL_OPTIONS.gemini[0],
  openai: LLM_MODEL_OPTIONS.openai[0],
  claude: LLM_MODEL_OPTIONS.claude[0],
  groq: LLM_MODEL_OPTIONS.groq[0],
};

const INTRO: Record<IndustryTone, (n: string, c: number) => string> = {
  real_estate: (n, c) => `Xin chào và chào mừng quý khách đến với ${n || "dự án"}. Mời quý khách cùng tham quan ${c} không gian nổi bật.`,
  retail: (n, c) => `Chào mừng đến với ${n || "không gian"}. Mời bạn dạo qua ${c} khu vực ấn tượng.`,
  exhibition: (n, c) => `Chào mừng bạn đến với ${n || "triển lãm"}. Hành trình gồm ${c} điểm dừng đang chờ khám phá.`,
};
const OUTRO: Record<IndustryTone, (n: string) => string> = {
  real_estate: (n) => `Cảm ơn quý khách đã tham quan ${n || "dự án"}. Hẹn gặp lại tại không gian thực tế.`,
  retail: (n) => `Cảm ơn bạn đã dạo qua ${n || "không gian"}. Chúc bạn có trải nghiệm thật thú vị.`,
  exhibition: (n) => `Cảm ơn bạn đã đồng hành tại ${n || "triển lãm"}. Hẹn gặp lại.`,
};

function narrate(d: StopDescribe): string {
  const hi = d.highlights.slice(0, 3).map((h) => `Điểm nổi bật: ${h.replace(/\.$/, "")}.`).join(" ");
  return `${d.title}. ${d.description} ${hi}`.trim();
}

async function detectKind(src: string): Promise<"photo" | "panorama"> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img.width / img.height > 1.7 ? "panorama" : "photo");
    img.onerror = () => resolve("photo");
    img.src = src;
  });
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) reject(new Error("Không nén được ảnh."));
      else resolve(blob);
    }, type, quality);
  });
}

async function compressImageFile(file: File): Promise<{ file: File; src: string }> {
  if (!file.type.startsWith("image/")) {
    throw new Error(`${file.name} không phải là file ảnh.`);
  }
  if (file.size > MAX_SOURCE_IMAGE_MB * 1024 * 1024) {
    throw new Error(`${file.name} lớn hơn ${MAX_SOURCE_IMAGE_MB}MB. Hãy dùng ảnh nguồn nhỏ hơn.`);
  }

  const objectUrl = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error(`Không đọc được ảnh ${file.name}.`));
      img.src = objectUrl;
    });

    const isPanorama = image.width / image.height > 1.7;
    let maxEdge = isPanorama ? 3072 : 1920;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Trình duyệt không hỗ trợ xử lý ảnh.");

    let blob: Blob | null = null;
    for (const quality of [0.82, 0.72, 0.62]) {
      const scale = Math.min(1, maxEdge / Math.max(image.width, image.height));
      canvas.width = Math.max(1, Math.round(image.width * scale));
      canvas.height = Math.max(1, Math.round(image.height * scale));
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      blob = await canvasToBlob(canvas, "image/jpeg", quality);
      if (blob.size <= TARGET_UPLOAD_IMAGE_MB * 1024 * 1024) break;
      maxEdge = Math.max(1280, Math.round(maxEdge * 0.75));
    }
    if (!blob || blob.size > TARGET_UPLOAD_IMAGE_MB * 1024 * 1024) {
      throw new Error(`${file.name} vẫn quá lớn sau khi nén. Hãy dùng ảnh nhỏ hơn hoặc giảm độ phân giải.`);
    }
    const compressed = new File(
      [blob],
      file.name.replace(/\.[^.]+$/, "") + ".jpg",
      { type: "image/jpeg", lastModified: Date.now() },
    );
    return { file: compressed, src: await fileToDataUrl(compressed) };
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

function cleanStopsForStorage(stops: RawStop[]): RawStop[] {
  return stops.map(({ file, ...rest }) => rest);
}

function makeProject(name = "Tour mới"): TourProject {
  return {
    id: `tour-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    name,
    industry: "real_estate",
    stops: [],
    savedTour: null,
    updatedAt: new Date().toISOString(),
  };
}

type Segment = {
  id: string;
  text: string;
  image: string;
  kind: string;
  describe?: StopDescribe;
  label: string;
  audioUrl?: string;
};

function segmentsFromTour(tour: TourWithAudio): Segment[] {
  if (tour.stops.length === 0) return [];
  const first = tour.stops[0], last = tour.stops[tour.stops.length - 1];
  const audio = tour.audio || {};
  const introId = "intro";
  const outroId = "outro";
  return [
    { id: introId, text: tour.intro, image: first.image, kind: first.kind, label: "Mở đầu", audioUrl: audio[introId] },
    ...tour.stops.map((s, i) => {
      const id = `stop:${s.id}`;
      return {
        id,
        text: s.narration,
        image: s.image,
        kind: s.kind,
        describe: s.describe,
        label: `Điểm ${i + 1}`,
        audioUrl: audio[id],
      };
    }),
    { id: outroId, text: tour.outro, image: last.image, kind: last.kind, label: "Kết", audioUrl: audio[outroId] },
  ];
}

function buildTourManifest(tour: TourWithAudio, audio: Record<string, string> = tour.audio || {}): TourManifest {
  const steps = segmentsFromTour({ ...tour, audio }).map((segment, index) => ({
    id: segment.id,
    label: segment.label,
    source_stop_id: segment.id.startsWith("stop:") ? segment.id.slice(5) : undefined,
    sequence: index + 1,
    image: segment.image,
    kind: segment.kind,
    has_audio: Boolean(audio[segment.id]),
  }));
  return {
    version: "tour-manifest-v1",
    project_name: tour.project_name || "Tour tham quan 3D",
    total_segments: steps.length,
    audio_segments: steps.filter((step) => step.has_audio).length,
    final_segment_id: steps.length ? steps[steps.length - 1].id : "",
    steps,
    created_at: new Date().toISOString(),
  };
}

function routeSignature(projectName: string, industry: IndustryTone, stops: RawStop[]): string {
  return JSON.stringify({
    name: projectName.trim() || "Tour tham quan 3D",
    industry,
    stops: stops.map((stop, index) => ({
      index,
      id: stop.id,
      src: stop.src,
      kind: stop.kind,
      source: stop.source,
      remoteUrl: stop.remoteUrl || "",
    })),
  });
}

function tourAudioStats(tour?: TourWithAudio | null) {
  if (!tour) return { done: 0, total: 0 };
  const total = tour.manifest?.total_segments || segmentsFromTour(tour).length;
  const done = tour.manifest?.audio_segments ?? Object.keys(tour.audio || {}).length;
  return { done, total };
}

function formatUpdatedAt(value?: string) {
  if (!value) return "";
  try {
    return new Intl.DateTimeFormat("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return "";
  }
}

function savedTourMatchesCurrentRoute(tour: TourWithAudio | null | undefined, signature: string) {
  if (!tour) return false;
  return !tour.routeSignature || tour.routeSignature === signature;
}

export default function TourPage() {
  const [projects, setProjects] = useState<TourProject[]>([]);
  const [activeProjectId, setActiveProjectId] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const [stops, setStops] = useState<RawStop[]>([]);
  const [projectName, setProjectName] = useState("");
  const [industry, setIndustry] = useState<IndustryTone>("real_estate");
  const [urlInput, setUrlInput] = useState("");
  const [tour, setTour] = useState<TourWithAudio | null>(null);
  const [draftTour, setDraftTour] = useState<TourWithAudio | null>(null);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [llmProvider, setLlmProvider] = useState<LlmProvider>("gemini");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [llmModels, setLlmModels] = useState<string[]>(LLM_MODEL_OPTIONS.gemini);
  const [llmModelsSource, setLlmModelsSource] = useState<"default" | "provider">("default");
  const [llmModelsLoading, setLlmModelsLoading] = useState(false);
  const [llmModelsError, setLlmModelsError] = useState<string | null>(null);
  const [llmModel, setLlmModel] = useState(LLM_MODEL_DEFAULTS.gemini);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState<LoadingState | null>(null);
  const [projectStoreStatus, setProjectStoreStatus] = useState<ProjectStoreStatus>("checking");
  const [projectStoreMessage, setProjectStoreMessage] = useState("Đang kiểm tra Supabase...");
  const remoteSaveTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const remoteProjectStoreEnabled = useRef(!STATIC_MODE);

  function queueRemoteProjectSave(project: TourProject) {
    if (STATIC_MODE || !remoteProjectStoreEnabled.current) return;
    clearTimeout(remoteSaveTimers.current[project.id]);
    remoteSaveTimers.current[project.id] = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/tour-projects/${encodeURIComponent(project.id)}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ project }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(typeof body?.detail === "string" ? body.detail : `Supabase ${res.status}`);
        }
        setProjectStoreStatus("supabase");
        setProjectStoreMessage("Đã đồng bộ dự án lên Supabase.");
      } catch (exc) {
        setProjectStoreStatus("error");
        setProjectStoreMessage(exc instanceof Error ? exc.message : "Không đồng bộ được Supabase.");
      }
    }, 700);
  }

  async function deleteRemoteProject(id: string) {
    if (STATIC_MODE || !remoteProjectStoreEnabled.current) return;
    clearTimeout(remoteSaveTimers.current[id]);
    try {
      const res = await fetch(`${API_BASE}/api/tour-projects/${encodeURIComponent(id)}`, { method: "DELETE" });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(typeof body?.detail === "string" ? body.detail : `Supabase ${res.status}`);
      }
      setProjectStoreStatus("supabase");
      setProjectStoreMessage("Đã xóa dự án trên Supabase.");
    } catch (exc) {
      setProjectStoreStatus("error");
      setProjectStoreMessage(exc instanceof Error ? exc.message : "Không xóa được project trên Supabase.");
    }
  }

  function persistProjects(next: TourProject[], syncRemote = true) {
    try {
      localStorage.setItem(PROJECT_STORAGE_KEY, JSON.stringify(next));
    } catch {
      setError("Không lưu được dự án vào trình duyệt. Ảnh có thể quá lớn; hãy dùng ít ảnh hơn hoặc ảnh nhỏ hơn.");
    }
    if (syncRemote) {
      next.forEach(queueRemoteProjectSave);
    }
  }

  async function hydrateRemoteProjects() {
    if (STATIC_MODE) {
      remoteProjectStoreEnabled.current = false;
      setProjectStoreStatus("local");
      setProjectStoreMessage("Chế độ static: dự án lưu trong trình duyệt.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/tour-projects`);
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(typeof body?.detail === "string" ? body.detail : `Supabase ${res.status}`);
      }
      if (!body?.configured) {
        remoteProjectStoreEnabled.current = false;
        setProjectStoreStatus("local");
        setProjectStoreMessage("Supabase chưa cấu hình, đang lưu localStorage.");
        return;
      }
      remoteProjectStoreEnabled.current = true;
      const remoteProjects = Array.isArray(body.projects)
        ? body.projects.filter((p: unknown): p is TourProject => Boolean(p && typeof p === "object" && (p as TourProject).id))
        : [];
      setProjectStoreStatus("supabase");
      if (remoteProjects.length === 0) {
        setProjectStoreMessage("Supabase đã kết nối, chưa có project đã lưu.");
        return;
      }
      setProjectStoreMessage(`Đã tải ${remoteProjects.length} project từ Supabase.`);
      setProjects(remoteProjects);
      setActiveProjectId(remoteProjects[0].id);
      setProjectName(remoteProjects[0].name);
      setIndustry(remoteProjects[0].industry);
      setStops(remoteProjects[0].stops || []);
      setTour(null);
      setDraftTour(null);
      localStorage.setItem(PROJECT_STORAGE_KEY, JSON.stringify(remoteProjects));
    } catch (exc) {
      setProjectStoreStatus("error");
      setProjectStoreMessage(exc instanceof Error ? exc.message : "Không tải được project từ Supabase.");
    }
  }

  useEffect(() => {
    let loaded: TourProject[] = [];
    try {
      loaded = JSON.parse(localStorage.getItem(PROJECT_STORAGE_KEY) || "[]");
    } catch {
      loaded = [];
    }
    if (loaded.length === 0) loaded = [makeProject()];
    setProjects(loaded);
    setActiveProjectId(loaded[0].id);
    setProjectName(loaded[0].name);
    setIndustry(loaded[0].industry);
    setStops(loaded[0].stops || []);
    setHydrated(true);
    void hydrateRemoteProjects();
  }, []);

  useEffect(() => {
    if (!hydrated || !activeProjectId) return;
    setProjects((current) => {
      const next = current.map((p) => (
        p.id === activeProjectId
          ? {
              ...p,
              name: projectName.trim() || "Tour chưa đặt tên",
              industry,
              stops: cleanStopsForStorage(stops),
              updatedAt: new Date().toISOString(),
            }
          : p
      ));
      persistProjects(next);
      return next;
    });
  }, [activeProjectId, hydrated, industry, projectName, stops]);

  useEffect(() => {
    function preventImageOpen(e: DragEvent) {
      e.preventDefault();
    }
    window.addEventListener("dragover", preventImageOpen);
    window.addEventListener("drop", preventImageOpen);
    return () => {
      window.removeEventListener("dragover", preventImageOpen);
      window.removeEventListener("drop", preventImageOpen);
    };
  }, []);

  function updateLlmProvider(provider: LlmProvider) {
    setLlmProvider(provider);
    setLlmModels(LLM_MODEL_OPTIONS[provider]);
    setLlmModelsSource("default");
    setLlmModelsError(null);
    setLlmModel(LLM_MODEL_DEFAULTS[provider]);
  }

  async function loadProviderModels() {
    const defaults = LLM_MODEL_OPTIONS[llmProvider];
    if (STATIC_MODE) {
      setLlmModels(defaults);
      setLlmModel(defaults[0]);
      setLlmModelsSource("default");
      setLlmModelsError("Chế độ static không gọi backend được, đang dùng danh sách mặc định.");
      return;
    }
    setLlmModelsLoading(true);
    setLlmModelsError(null);
    try {
      const res = await fetch(`${API_BASE}/api/llm/models`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ provider: llmProvider, api_key: llmApiKey.trim() }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(typeof body?.detail === "string" ? body.detail : `API ${res.status}`);
      }
      const models = Array.isArray(body?.models)
        ? body.models.filter((m: unknown): m is string => typeof m === "string" && m.trim().length > 0)
        : [];
      if (models.length === 0) throw new Error("Provider không trả model nào.");
      setLlmModels(models);
      setLlmModelsSource(body?.source === "provider" ? "provider" : "default");
      if (llmApiKey.trim() && body?.source !== "provider") {
        setLlmModelsError("Provider không trả danh sách model, đang dùng danh sách mặc định.");
      }
      setLlmModel((current) => models.includes(current) ? current : models[0]);
    } catch (exc) {
      setLlmModels(defaults);
      setLlmModel(defaults[0]);
      setLlmModelsSource("default");
      setLlmModelsError(exc instanceof Error ? exc.message : "Không tải được danh sách model.");
    } finally {
      setLlmModelsLoading(false);
    }
  }

  function llmPayload() {
    const key = llmApiKey.trim();
    if (!key) return {};
    return {
      llm_provider: llmProvider,
      llm_api_key: key,
      llm_model: llmModel.trim() || LLM_MODEL_DEFAULTS[llmProvider],
    };
  }

  function selectProject(project: TourProject) {
    setActiveProjectId(project.id);
    setProjectName(project.name);
    setIndustry(project.industry);
    setStops(project.stops || []);
    setTour(null);
    setDraftTour(null);
    setError(null);
  }

  function createProject() {
    const project = makeProject(`Tour mới ${projects.length + 1}`);
    const next = [project, ...projects];
    setProjects(next);
    persistProjects(next);
    selectProject(project);
  }

  function deleteProject(id: string) {
    const next = projects.filter((p) => p.id !== id);
    void deleteRemoteProject(id);
    if (next.length === 0) {
      const replacement = makeProject();
      setProjects([replacement]);
      persistProjects([replacement]);
      selectProject(replacement);
      return;
    }
    setProjects(next);
    persistProjects(next);
    if (id === activeProjectId) selectProject(next[0]);
  }

  async function onFiles(files: FileList | null) {
    if (!files) return;
    setError(null);
    const added: RawStop[] = [];
    const incoming = Array.from(files);
    if (incoming.length === 0) return;
    try {
      for (const [index, f] of incoming.entries()) {
        setLoading({
          title: "Đang xử lý ảnh",
          detail: `Nén ảnh ${index + 1}/${incoming.length} trước khi lưu vào tour`,
          progress: Math.round((index / incoming.length) * 100),
        });
        const prepared = await compressImageFile(f);
        added.push({
          id: `s${Date.now()}-${added.length}`,
          src: prepared.src,
          file: prepared.file,
          kind: await detectKind(prepared.src),
          source: "file",
        });
        setLoading({
          title: "Đang xử lý ảnh",
          detail: `Đã chuẩn bị ${index + 1}/${incoming.length} ảnh`,
          progress: Math.round(((index + 1) / incoming.length) * 100),
        });
      }
      setStops((s) => [...s, ...added]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(null);
    }
  }

  function onDropFiles(e: ReactDragEvent<HTMLLabelElement>) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    void onFiles(e.dataTransfer.files);
  }

  async function addUrlStop() {
    const url = urlInput.trim();
    if (!url) {
      setError("Nhập URL ảnh công khai trước khi thêm.");
      return;
    }
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      setError("URL ảnh phải bắt đầu bằng http:// hoặc https://.");
      return;
    }
    setError(null);
    setStops((s) => [
      ...s,
      {
        id: `url${Date.now()}`,
        src: url,
        remoteUrl: url,
        kind: "photo",
        source: "url",
      },
    ]);
    setUrlInput("");
    const kind = await detectKind(url);
    setStops((s) => s.map((stop) => (stop.src === url ? { ...stop, kind } : stop)));
  }

  async function addSamplePanoramas() {
    try {
      const scene = await fetch("/artifacts/sunrise-office-tower-5f-6r.json").then((r) => r.json());
      const ready = (scene.structure?.floors?.[0]?.rooms ?? [])
        .filter((r: any) => r.panorama?.status === "ready" && r.panorama?.image)
        .slice(0, 3);
      const added: RawStop[] = ready.map((r: any, i: number) => ({
        id: `pano${Date.now()}-${i}`,
        src: `/artifacts/${r.panorama.image}`,
        kind: "panorama" as const,
        source: "sample" as const,
      }));
      setStops((s) => [...s, ...added]);
    } catch {
      setError("Không tải được panorama mẫu.");
    }
  }

  function move(i: number, dir: -1 | 1) {
    setStops((s) => {
      const j = i + dir;
      if (j < 0 || j >= s.length) return s;
      const c = [...s];
      [c[i], c[j]] = [c[j], c[i]];
      return c;
    });
  }
  const remove = (id: string) => setStops((s) => s.filter((x) => x.id !== id));

  function setDraftIntro(value: string) {
    setDraftTour((current) => current ? { ...current, intro: value, audio: {}, audioErrors: undefined, manifest: undefined } : current);
  }

  function setDraftOutro(value: string) {
    setDraftTour((current) => current ? { ...current, outro: value, audio: {}, audioErrors: undefined, manifest: undefined } : current);
  }

  function setDraftStopNarration(stopId: string, value: string) {
    setDraftTour((current) => {
      if (!current) return current;
      return {
        ...current,
        audio: {},
        audioErrors: undefined,
        manifest: undefined,
        stops: current.stops.map((stop) => (
          stop.id === stopId ? { ...stop, narration: value } : stop
        )),
      };
    });
  }

  function saveGeneratedTour(nextTour: TourWithAudio) {
    const signedTour: TourWithAudio = {
      ...nextTour,
      manifest: nextTour.manifest || buildTourManifest(nextTour),
      routeSignature: routeSignature(projectName, industry, stops),
    };
    setTour(signedTour);
    setProjects((current) => {
      const next = current.map((p) => (
        p.id === activeProjectId
          ? { ...p, savedTour: signedTour, updatedAt: new Date().toISOString() }
          : p
      ));
      persistProjects(next);
      return next;
    });
  }

  async function generateAudioForTour(baseTour: Tour): Promise<TourWithAudio> {
    const audio: Record<string, string> = {};
    const audioErrors: Record<string, string> = {};
    if (STATIC_MODE) {
      const staticTour: TourWithAudio = { ...baseTour, audio };
      return { ...staticTour, manifest: buildTourManifest(staticTour, audio) };
    }
    const draft = { ...baseTour, audio };
    const segments = segmentsFromTour(draft);
    for (const [index, segment] of segments.entries()) {
      setLoading({
        title: "Đang render giọng đọc",
        detail: `Tạo WAV ${index + 1}/${segments.length}: ${segment.label}`,
        progress: 65 + Math.round((index / Math.max(segments.length, 1)) * 30),
      });
      try {
        const res = await fetch(`${API_BASE}/api/tts/generate`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ text: segment.text, voice: DEFAULT_TTS_VOICE }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(typeof body?.detail === "string" ? body.detail : `TTS ${res.status}`);
        }
        const body = (await res.json()) as { audio_url: string };
        audio[segment.id] = API_BASE ? `${API_BASE}${body.audio_url}` : body.audio_url;
      } catch (e) {
        audioErrors[segment.id] = e instanceof Error ? e.message : String(e);
      }
    }
    const withAudio: TourWithAudio = {
      ...baseTour,
      audio,
      audioGeneratedAt: new Date().toISOString(),
      audioErrors: Object.keys(audioErrors).length ? audioErrors : undefined,
    };
    return { ...withAudio, manifest: buildTourManifest(withAudio, audio) };
  }

  async function buildTour() {
    if (stops.length === 0) {
      setError("Thêm ít nhất một điểm dừng trước khi tạo tour.");
      return;
    }
    setBuilding(true);
    setError(null);
    try {
      let describes: StopDescribe[];
      if (!STATIC_MODE) {
        describes = [];
        for (const [i, s] of stops.entries()) {
          setLoading({
            title: "AI đang mô tả ảnh",
            detail: `Phân tích điểm dừng ${i + 1}/${stops.length}`,
            progress: Math.round((i / Math.max(stops.length, 1)) * 45),
          });
          let r: Response;
          if (s.remoteUrl) {
            r = await fetch(`${API_BASE}/api/describe-image-url`, {
              method: "POST",
              headers: { "content-type": "application/json" },
              body: JSON.stringify({
                url: s.remoteUrl,
                industry,
                hint: `Điểm dừng ${i + 1} trong tour ${projectName || "tham quan 3D"}`,
                ...llmPayload(),
              }),
            });
          } else {
            const blob: Blob = s.file ? s.file : await fetch(s.src).then((res) => res.blob());
            const fd = new FormData();
            fd.append("file", blob, "view.jpg");
            fd.append("industry", industry);
            fd.append("hint", `Điểm dừng ${i + 1} trong tour ${projectName || "tham quan 3D"}`);
            const llm = llmPayload();
            Object.entries(llm).forEach(([key, value]) => fd.append(key, value));
            r = await fetch(`${API_BASE}/api/describe-image`, { method: "POST", body: fd });
          }
          if (!r.ok) {
            const body = await r.json().catch(() => null);
            throw new Error(typeof body?.detail === "string" ? body.detail : `API ${r.status}`);
          }
          describes.push((await r.json()) as StopDescribe);
        }
        setLoading({
          title: "Đang viết lời dẫn tour",
          detail: "LLM đang ghép mô tả ảnh thành kịch bản hướng dẫn viên",
          progress: 50,
        });
        const tourRes = await fetch(`${API_BASE}/api/tour`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            project_name: projectName.trim() || "Tour tham quan 3D",
            industry,
            stops: stops.map((s, i) => ({
              id: s.id,
              image: s.src,
              kind: s.kind,
              describe: describes[i],
            })),
            ...llmPayload(),
          }),
        });
        if (!tourRes.ok) {
          const body = await tourRes.json().catch(() => null);
          throw new Error(typeof body?.detail === "string" ? body.detail : `API ${tourRes.status}`);
        }
        const generated = await tourRes.json() as Tour;
        setLoading({
          title: "Đã tạo script",
          detail: "Bạn có thể chỉnh lời dẫn trước khi render giọng đọc",
          progress: 100,
        });
        setDraftTour({ ...generated, audio: {}, manifest: buildTourManifest({ ...generated, audio: {} }) });
        return;
      } else {
        setLoading({
          title: "Đang tạo tour mẫu",
          detail: "Dùng mô tả mock theo ngành trong chế độ tĩnh",
          progress: 40,
        });
        describes = stops.map(() => VISION_TPL[industry]); // static fallback (mock)
      }
      const tourStops = stops.map((s, i) => ({
        id: s.id, image: s.src, kind: s.kind, describe: describes[i], narration: narrate(describes[i]),
      }));
      const generated: Tour = {
        id: "tour", project_name: projectName, industry,
        intro: INTRO[industry](projectName, stops.length),
        outro: OUTRO[industry](projectName),
        stops: tourStops,
      };
      setLoading({
        title: "Đã tạo script",
        detail: "Bạn có thể chỉnh lời dẫn trước khi render giọng đọc",
        progress: 100,
      });
      setDraftTour({ ...generated, audio: {}, manifest: buildTourManifest({ ...generated, audio: {} }) });
    } catch (e) {
      setError(
        !STATIC_MODE && e instanceof TypeError
          ? `Không kết nối được backend tại ${API_BASE}. Hãy chạy backend rồi thử lại.`
          : e instanceof Error ? e.message : String(e),
      );
    } finally {
      setBuilding(false);
      setLoading(null);
    }
  }

  async function renderDraftAudio() {
    if (!draftTour) return;
    setBuilding(true);
    setError(null);
    try {
      const withAudio = await generateAudioForTour(draftTour);
      setLoading({
        title: "Đang lưu tour",
        detail: "Lưu script đã chỉnh, manifest và audio cache",
        progress: 98,
      });
      saveGeneratedTour(withAudio);
      setDraftTour(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBuilding(false);
      setLoading(null);
    }
  }

  function previewDraft() {
    if (!draftTour) return;
    setTour({
      ...draftTour,
      manifest: draftTour.manifest || buildTourManifest(draftTour),
      routeSignature: routeSignature(projectName, industry, stops),
    });
  }

  if (tour) return <TourPlayer tour={tour} onExit={() => setTour(null)} />;

  const activeProject = projects.find((p) => p.id === activeProjectId) || null;
  const currentRouteSignature = routeSignature(projectName, industry, stops);
  const activeSavedTour = savedTourMatchesCurrentRoute(activeProject?.savedTour, currentRouteSignature)
    ? activeProject?.savedTour || null
    : null;
  const activeSavedStats = tourAudioStats(activeSavedTour);
  const staleSavedStats = tourAudioStats(activeProject?.savedTour);
  const inputCls =
    "h-11 w-full rounded-[10px] border border-[var(--border)] bg-white px-3 text-sm focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-soft)]";

  return (
    <main className="min-h-[100dvh]">
      {loading && <TourLoadingOverlay loading={loading} />}
      <div className="mx-auto max-w-[1540px] px-6 py-8 xl:px-8">
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text)]">
          <ArrowLeftIcon size={16} /> Về trang giới thiệu
        </Link>
        <h1 className="serif mt-4 text-3xl font-semibold tracking-tight">Tạo tour có thuyết minh AI</h1>
        <p className="mt-1 text-[var(--text-muted)]">
          Tải view, thêm ảnh online hoặc panorama mẫu, sắp thành lộ trình rồi để AI viết lời dẫn hướng dẫn viên.
        </p>

        <div className="mt-7 grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)] 2xl:grid-cols-[310px_minmax(440px,520px)_minmax(560px,1fr)]">
          {/* projects */}
          <aside className="h-fit rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 lg:sticky lg:top-6">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">Dự án tour</p>
                <p className="text-xs text-[var(--text-faint)]">{projects.length} dự án đã lưu</p>
              </div>
              <button
                type="button"
                onClick={createProject}
                className="rounded-[10px] bg-[var(--accent-strong)] px-3 py-2 text-xs font-medium text-white hover:bg-[var(--accent-hover)]"
              >
                Tạo mới
              </button>
            </div>
            <div
              className={`mb-3 rounded-[10px] border px-3 py-2 text-xs ${
                projectStoreStatus === "supabase"
                  ? "border-[rgba(79,122,82,0.3)] bg-[rgba(79,122,82,0.08)] text-[var(--ok)]"
                  : projectStoreStatus === "error"
                    ? "border-[rgba(181,131,47,0.3)] bg-[rgba(181,131,47,0.08)] text-[var(--warn)]"
                    : "border-[var(--border)] bg-[var(--bg-subtle)] text-[var(--text-faint)]"
              }`}
            >
              {projectStoreMessage}
            </div>
            <div className="space-y-2">
              {projects.map((project) => {
                const stats = tourAudioStats(project.savedTour);
                return (
                  <div
                    key={project.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => selectProject(project)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        selectProject(project);
                      }
                    }}
                    className={`group w-full rounded-xl border p-3 text-left transition ${
                      project.id === activeProjectId
                        ? "border-[var(--accent)] bg-[var(--accent-soft)]"
                        : "border-[var(--border)] bg-white hover:bg-[var(--bg-subtle)]"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-[var(--text)]">{project.name || "Tour chưa đặt tên"}</p>
                        <p className="mt-0.5 text-xs text-[var(--text-faint)]">
                          {INDUSTRY_LABELS[project.industry]} · {project.stops.length} điểm
                        </p>
                        <p className="mt-1 text-[11px] text-[var(--text-faint)]">
                          {project.savedTour
                            ? `Manifest đã lưu · audio ${stats.done}/${stats.total}`
                            : "Chưa generate tour"}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteProject(project.id);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            e.stopPropagation();
                            deleteProject(project.id);
                          }
                        }}
                        className="rounded p-1 text-[var(--text-faint)] opacity-100 hover:bg-white hover:text-[var(--danger)] lg:opacity-0 lg:group-hover:opacity-100"
                        aria-label={`Xóa ${project.name}`}
                      >
                        <TrashIcon size={15} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </aside>

          {/* config */}
          <div className="h-fit space-y-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium">Tên dự án tour</label>
              <input className={inputCls} value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Sunrise Office Tower" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium">Ngành (tone thuyết minh)</label>
              <select className={inputCls} value={industry} onChange={(e) => setIndustry(e.target.value as IndustryTone)}>
                {(Object.keys(INDUSTRY_LABELS) as IndustryTone[]).map((k) => (
                  <option key={k} value={k}>{INDUSTRY_LABELS[k]}</option>
                ))}
              </select>
            </div>
            <div className="rounded-[10px] border border-[var(--border)] bg-white p-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">LLM mô tả ảnh</p>
                  <p className="text-xs text-[var(--text-faint)]">
                    Không nhập key thì dùng mock AI local. Groq cần model vision như Llama 4 Scout để đọc ảnh.
                  </p>
                </div>
                <select
                  className="h-9 rounded-[10px] border border-[var(--border)] bg-white px-2 text-xs"
                  value={llmProvider}
                  onChange={(e) => updateLlmProvider(e.target.value as LlmProvider)}
                >
                  <option value="gemini">Google Gemini</option>
                  <option value="groq">Groq</option>
                  <option value="openai">OpenAI</option>
                  <option value="claude">Claude</option>
                </select>
              </div>
              <input
                className={`${inputCls} mt-3`}
                value={llmApiKey}
                onChange={(e) => setLlmApiKey(e.target.value)}
                placeholder={
                  llmProvider === "gemini" ? "GEMINI_API_KEY / GOOGLE_API_KEY"
                  : llmProvider === "openai" ? "OPENAI_API_KEY"
                  : llmProvider === "groq" ? "GROQ_API_KEY"
                  : "ANTHROPIC_API_KEY"
                }
                type="password"
                autoComplete="off"
              />
              <div className="mt-2 flex gap-2">
                <select
                  className={inputCls}
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                >
                  {llmModels.map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={loadProviderModels}
                  disabled={llmModelsLoading}
                  className="h-11 shrink-0 rounded-[10px] border border-[var(--border)] bg-white px-3 text-xs font-medium text-[var(--text)] hover:bg-[var(--bg-subtle)] disabled:cursor-wait disabled:opacity-60"
                >
                  {llmModelsLoading ? "Đang tải" : "Tải models"}
                </button>
              </div>
              <p className="mt-1.5 text-xs text-[var(--text-faint)]">
                {llmModelsSource === "provider"
                  ? "Danh sách model được tải từ provider bằng API key hiện tại."
                  : "Đang dùng danh sách model mặc định; có thể tải từ provider sau khi nhập key."}
              </p>
              {llmModelsError && (
                <p className="mt-1 text-xs text-red-600">{llmModelsError}</p>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium">Thêm view</label>
              <label
                className={`flex h-28 cursor-pointer flex-col items-center justify-center rounded-[10px] border border-dashed text-sm transition ${
                  dragActive
                    ? "border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent-hover)]"
                    : "border-[var(--border-strong)] text-[var(--text-muted)] hover:bg-[var(--bg-subtle)]"
                }`}
                onDragEnter={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setDragActive(true);
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setDragActive(true);
                }}
                onDragLeave={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (e.currentTarget === e.target) setDragActive(false);
                }}
                onDrop={onDropFiles}
              >
                <ImagesIcon size={22} />
                <span className="mt-1">{dragActive ? "Thả ảnh vào đây" : "Kéo thả hoặc bấm để tải ảnh"}</span>
                <span className="mt-0.5 text-xs text-[var(--text-faint)]">Ảnh lớn sẽ được nén tự động trước khi gọi LLM</span>
                {hydrated && (
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={(e) => onFiles(e.target.files)}
                    suppressHydrationWarning
                  />
                )}
              </label>
              <div className="mt-3">
                <label className="mb-1.5 block text-sm font-medium">Nguồn ảnh online</label>
                <div className="flex gap-2">
                  <input
                    className={inputCls}
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://example.com/lobby.jpg"
                  />
                  <button
                    type="button"
                    onClick={addUrlStop}
                    className="h-11 rounded-[10px] border border-[var(--border-strong)] px-3 text-sm text-[var(--text)] hover:bg-[var(--bg-subtle)]"
                  >
                    Thêm
                  </button>
                </div>
              </div>
              <button onClick={addSamplePanoramas} className="mt-2 w-full rounded-[10px] border border-[var(--border-strong)] py-2 text-xs text-[var(--text-muted)] hover:bg-[var(--bg-subtle)]">
                + Thêm lộ trình panorama mẫu
              </button>
            </div>
            <button
              onClick={buildTour}
              disabled={building || stops.length === 0}
              className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-[10px] bg-[var(--accent-strong)] text-sm font-medium text-white hover:bg-[var(--accent-hover)] disabled:opacity-60"
            >
              <SparkleIcon size={16} /> {building ? "Đang xử lý..." : "Tạo script tour guide"}
            </button>
            {activeProject?.savedTour && !activeSavedTour && (
              <p className="rounded-[10px] border border-[var(--border)] bg-[var(--bg-subtle)] p-3 text-xs text-[var(--text-muted)]">
                Tour đã lưu trước đó không còn khớp lộ trình hiện tại. Hãy tạo lại tour để cập nhật manifest và audio.
              </p>
            )}
            {activeSavedTour && (
              <button
                type="button"
                onClick={() => setTour(activeSavedTour)}
                className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-[10px] border border-[var(--border-strong)] text-sm font-medium text-[var(--text)] hover:bg-[var(--bg-subtle)]"
              >
                <PlayIcon size={16} /> Mở tour đã lưu ({activeSavedStats.done}/{activeSavedStats.total} audio)
              </button>
            )}
            {activeSavedTour?.manifest && (
              <div className="rounded-[10px] border border-[var(--border)] bg-white p-3 text-xs text-[var(--text-muted)]">
                <p className="font-medium text-[var(--text)]">Manifest tuyến đã lưu</p>
                <p className="mt-1">
                  {activeSavedTour.manifest.total_segments} đoạn · audio {activeSavedTour.manifest.audio_segments}/{activeSavedTour.manifest.total_segments}
                  {activeSavedTour.audioGeneratedAt ? ` · ${formatUpdatedAt(activeSavedTour.audioGeneratedAt)}` : ""}
                </p>
                {activeSavedTour.audioErrors && (
                  <p className="mt-1 text-[var(--danger)]">
                    {Object.keys(activeSavedTour.audioErrors).length} đoạn chưa tạo được WAV, player sẽ dùng giọng trình duyệt.
                  </p>
                )}
              </div>
            )}
            {activeProject?.savedTour && !activeSavedTour && staleSavedStats.total > 0 && (
              <p className="text-xs text-[var(--text-faint)]">
                Bản cũ có audio {staleSavedStats.done}/{staleSavedStats.total}, nhưng không được dùng cho lộ trình mới.
              </p>
            )}
            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
            <p className="text-xs text-[var(--text-faint)]">
              {STATIC_MODE
                ? "Chế độ tĩnh: mô tả mẫu theo ngành."
                : `Chế độ live: backend ${API_BASE} mô tả ảnh, viết lời dẫn và lưu file WAV trong /artifacts/tts.`}
            </p>
          </div>

          {/* ordered stops */}
          <div className="min-w-0 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 lg:col-start-2 2xl:col-start-auto">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">Lộ trình tham quan</p>
                <p className="text-xs text-[var(--text-faint)]">{stops.length} điểm dừng trong tour hiện tại</p>
              </div>
              {stops.length > 0 && (
                <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-medium text-[var(--accent-hover)]">
                  {stops.filter((s) => s.kind === "panorama").length} view 360
                </span>
              )}
            </div>
            {stops.length === 0 ? (
              <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-[var(--border)] text-sm text-[var(--text-faint)]">
                Chưa có view nào. Tải ảnh hoặc thêm panorama mẫu bên trái.
              </div>
            ) : (
              <ul className="grid gap-3 xl:grid-cols-2 2xl:grid-cols-1">
                {stops.map((s, i) => (
                  <li key={s.id} className="grid gap-3 rounded-xl border border-[var(--border)] bg-white p-3 sm:grid-cols-[minmax(180px,240px)_1fr]">
                    <div className="relative overflow-hidden rounded-[10px] border border-[var(--border)] bg-[var(--bg-subtle)]">
                      <span className="absolute left-2 top-2 z-10 flex h-7 w-7 items-center justify-center rounded-full bg-white/90 text-xs font-semibold text-[var(--accent-hover)] shadow-[var(--shadow-sm)]">{i + 1}</span>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={s.src} alt="" className="aspect-[16/10] h-full min-h-[132px] w-full object-cover" />
                    </div>
                    <div className="min-w-0 self-center">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <span className="block truncate text-sm font-medium text-[var(--text)]">Điểm dừng {i + 1}</span>
                          <span className="mt-1 flex flex-wrap gap-2">
                        <span className="rounded-full bg-[var(--bg-subtle)] px-2 py-0.5 text-xs text-[var(--text-muted)]">
                          {s.kind === "panorama" ? "Ảnh 360" : "Ảnh thường"}
                        </span>
                        <span className="rounded-full bg-[var(--bg-subtle)] px-2 py-0.5 text-xs text-[var(--text-faint)]">
                          {s.source === "url" ? "online" : s.source === "sample" ? "mẫu" : "upload"}
                        </span>
                          </span>
                        </div>
                        <span className="flex items-center gap-1">
                          <button onClick={() => move(i, -1)} className="rounded p-1 hover:bg-[var(--bg-subtle)]" aria-label="Đưa điểm dừng lên"><ArrowUpIcon size={16} /></button>
                          <button onClick={() => move(i, 1)} className="rounded p-1 hover:bg-[var(--bg-subtle)]" aria-label="Đưa điểm dừng xuống"><ArrowDownIcon size={16} /></button>
                          <button onClick={() => remove(s.id)} className="rounded p-1 text-[var(--danger)] hover:bg-[var(--bg-subtle)]" aria-label="Xóa điểm dừng"><TrashIcon size={16} /></button>
                        </span>
                      </div>
                      <p className="mt-3 text-xs leading-relaxed text-[var(--text-faint)]">
                        Preview lớn hơn để kiểm tra bố cục ảnh trước khi AI viết lời dẫn.
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {draftTour && (
            <div className="min-w-0 lg:col-start-2 2xl:col-span-2 2xl:col-start-2">
              <ScriptEditor
                tour={draftTour}
                disabled={building}
                onIntroChange={setDraftIntro}
                onOutroChange={setDraftOutro}
                onStopNarrationChange={setDraftStopNarration}
                onPreview={previewDraft}
                onRenderAudio={renderDraftAudio}
                onDiscard={() => setDraftTour(null)}
              />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function ScriptEditor({
  tour,
  disabled,
  onIntroChange,
  onOutroChange,
  onStopNarrationChange,
  onPreview,
  onRenderAudio,
  onDiscard,
}: {
  tour: TourWithAudio;
  disabled: boolean;
  onIntroChange: (value: string) => void;
  onOutroChange: (value: string) => void;
  onStopNarrationChange: (stopId: string, value: string) => void;
  onPreview: () => void;
  onRenderAudio: () => void;
  onDiscard: () => void;
}) {
  const textareaCls =
    "min-h-36 w-full resize-y rounded-[10px] border border-[var(--border)] bg-white px-3 py-2 text-sm leading-relaxed focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-soft)]";
  return (
    <section className="rounded-2xl border border-[var(--accent)] bg-[var(--accent-soft)] p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-base font-semibold text-[var(--text)]">Chỉnh lời dẫn và preview ảnh</p>
          <p className="mt-1 text-sm text-[var(--text-muted)]">Xem ảnh từng điểm dừng ở kích thước lớn, sửa text rồi render WAV bằng giọng nữ.</p>
        </div>
        <button
          type="button"
          onClick={onDiscard}
          disabled={disabled}
          className="h-10 rounded-[10px] border border-[var(--border-strong)] bg-white px-3 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-subtle)] disabled:opacity-60"
        >
          Bỏ draft
        </button>
      </div>

      <div className="mt-5 space-y-4">
        <label className="block rounded-xl border border-[var(--border)] bg-white/70 p-4">
          <span className="mb-2 block text-sm font-medium text-[var(--text)]">Mở đầu</span>
          <textarea className={textareaCls} value={tour.intro} onChange={(e) => onIntroChange(e.target.value)} />
        </label>
        {tour.stops.map((stop, index) => (
          <div key={stop.id} className="grid gap-4 rounded-xl border border-[var(--border)] bg-white p-4 xl:grid-cols-[minmax(320px,42%)_1fr]">
            <div className="min-w-0">
              <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-subtle)]">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={stop.image} alt={stop.describe.title} className="aspect-[16/10] min-h-[220px] w-full object-cover" />
              </div>
              <div className="mt-3">
                <p className="text-sm font-semibold text-[var(--text)]">Điểm {index + 1}: {stop.describe.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-[var(--text-muted)]">{stop.describe.description}</p>
                {stop.describe.highlights.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {stop.describe.highlights.slice(0, 4).map((highlight) => (
                      <span key={highlight} className="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-xs text-[var(--accent-hover)]">
                        {highlight}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <label className="block min-w-0">
              <span className="mb-2 block text-sm font-medium text-[var(--text)]">Lời dẫn điểm dừng</span>
              <textarea
                className={`${textareaCls} min-h-[260px]`}
                value={stop.narration}
                onChange={(e) => onStopNarrationChange(stop.id, e.target.value)}
              />
            </label>
          </div>
        ))}
        <label className="block rounded-xl border border-[var(--border)] bg-white/70 p-4">
          <span className="mb-2 block text-sm font-medium text-[var(--text)]">Kết</span>
          <textarea className={textareaCls} value={tour.outro} onChange={(e) => onOutroChange(e.target.value)} />
        </label>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onRenderAudio}
          disabled={disabled}
          className="inline-flex h-11 flex-1 min-w-[220px] items-center justify-center gap-2 rounded-[10px] bg-[var(--accent-strong)] px-4 text-sm font-medium text-white hover:bg-[var(--accent-hover)] disabled:opacity-60"
        >
          <SparkleIcon size={16} /> Render giọng nữ & lưu tour
        </button>
        <button
          type="button"
          onClick={onPreview}
          disabled={disabled}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-[10px] border border-[var(--border-strong)] bg-white px-4 text-sm text-[var(--text)] hover:bg-[var(--bg-subtle)] disabled:opacity-60"
        >
          <PlayIcon size={16} /> Xem trước
        </button>
      </div>
    </section>
  );
}

function TourLoadingOverlay({ loading }: { loading: LoadingState }) {
  const progress = Math.max(0, Math.min(100, loading.progress));
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-5 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-2xl border border-white/45 bg-white p-5 shadow-[0_24px_80px_rgba(0,0,0,.28)]">
        <div className="flex items-center gap-4">
          <div className="relative h-12 w-12 flex-none">
            <div className="absolute inset-0 rounded-full border-4 border-[var(--accent-soft)]" />
            <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-[var(--accent-strong)]" />
            <SparkleIcon className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[var(--accent-hover)]" size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-[var(--text)]">{loading.title}</p>
            <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">{loading.detail}</p>
          </div>
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-[var(--bg-subtle)]">
          <div
            className="h-full rounded-full bg-[var(--accent-strong)] transition-[width] duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-right text-xs text-[var(--text-faint)]">{progress}%</p>
      </div>
    </div>
  );
}

function TourPlayer({ tour, onExit }: { tour: TourWithAudio; onExit: () => void }) {
  const segments = useMemo<Segment[]>(() => {
    return segmentsFromTour(tour);
  }, [tour]);
  const manifest = useMemo(() => {
    return tour.manifest || buildTourManifest(tour);
  }, [tour]);

  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [audioMode, setAudioMode] = useState<"idle" | "loading" | "vieneu" | "browser" | "error">("idle");
  const seg = segments[idx];
  const idxRef = useRef(idx);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  idxRef.current = idx;

  const advance = useCallback(() => {
    if (idxRef.current < segments.length - 1) setIdx((i) => i + 1);
    else setPlaying(false);
  }, [segments.length]);

  const stopAudio = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    window.speechSynthesis?.cancel();
  }, []);

  const speakBrowser = useCallback((text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      setAudioMode("error");
      return;
    }
    const synth = window.speechSynthesis;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "vi-VN";
    const vi = synth.getVoices().find((v) => v.lang?.toLowerCase().startsWith("vi"));
    if (vi) u.voice = vi;
    u.rate = 1.0;
    u.onend = advance;
    setAudioMode("browser");
    synth.speak(u);
  }, [advance]);

  useEffect(() => {
    stopAudio();
    if (!playing || typeof window === "undefined") return undefined;

    let cancelled = false;
    async function playSavedAudio() {
      if (seg.audioUrl) {
        try {
          if (cancelled) return;
          const audio = new Audio(seg.audioUrl);
          audioRef.current = audio;
          audio.onended = advance;
          audio.onerror = () => {
            if (!cancelled) speakBrowser(seg.text);
          };
          setAudioMode("loading");
          await audio.play();
          setAudioMode("vieneu");
          return;
        } catch {
          if (cancelled) return;
        }
      }
      speakBrowser(seg.text);
    }

    playSavedAudio();
    return () => {
      cancelled = true;
      stopAudio();
    };
  }, [idx, playing, seg.audioUrl, seg.text, advance, speakBrowser, stopAudio]);

  function toggle() {
    if (playing) setPlaying(false);
    else setPlaying(true);
  }
  const go = (d: -1 | 1) => setIdx((i) => Math.min(Math.max(i + d, 0), segments.length - 1));
  function restart() { setIdx(0); setPlaying(false); setAudioMode("idle"); }

  const audioLabel =
    audioMode === "vieneu" ? "Đang phát VieNeu-TTS đã lưu" :
    audioMode === "loading" ? "Đang tải audio đã lưu" :
    audioMode === "browser" ? "Giọng trình duyệt dự phòng" :
    audioMode === "error" ? "Không phát được giọng" :
    seg.audioUrl ? "Audio đã lưu, bấm Phát" : "Chưa có audio lưu, dùng giọng trình duyệt";

  return (
    <main className="relative h-[100dvh] overflow-hidden bg-black text-white">
      <div className="absolute inset-0">
        {seg.kind === "panorama" ? (
          <PanoramaViewer image={seg.image} />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={seg.image} alt="" className="h-full w-full object-cover" />
        )}
      </div>
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,rgba(0,0,0,.58),rgba(0,0,0,.12)_48%,rgba(0,0,0,.44)),linear-gradient(180deg,rgba(0,0,0,.48),rgba(0,0,0,0)_34%,rgba(0,0,0,.62))]" />

      <div className="pointer-events-none absolute inset-0 flex flex-col justify-between p-4 md:p-6">
        <div className="flex items-start justify-between gap-4">
          <button
            onClick={() => { stopAudio(); onExit(); }}
            className="pointer-events-auto inline-flex items-center gap-1.5 rounded-full border border-white/25 bg-black/35 px-4 py-2 text-sm text-white shadow-[0_18px_50px_rgba(0,0,0,.25)] backdrop-blur hover:bg-black/50"
          >
            <ArrowLeftIcon size={16} /> Sửa tour
          </button>
          <div className="rounded-full border border-white/20 bg-black/35 px-4 py-2 text-sm text-white/85 shadow-[0_18px_50px_rgba(0,0,0,.25)] backdrop-blur">
            {seg.label} · {idx + 1}/{segments.length}
          </div>
        </div>

        <div className="grid items-end gap-4 lg:grid-cols-[minmax(320px,520px)_1fr]">
          <section className="pointer-events-auto rounded-2xl border border-white/18 bg-black/48 p-5 shadow-[0_24px_70px_rgba(0,0,0,.35)] backdrop-blur-md md:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/70">
              {INDUSTRY_LABELS[tour.industry]} · {tour.project_name || "Tour"} · {audioLabel}
            </p>
            <h2 className="serif mt-2 text-2xl font-semibold tracking-tight text-white md:text-3xl">
              {seg.describe?.title || seg.label}
            </h2>
            <p className="mt-3 max-h-[30dvh] overflow-auto pr-1 text-sm leading-relaxed text-white/82 md:text-base">
              {seg.text}
            </p>
            {seg.describe && (
              <ul className="mt-4 grid gap-2">
                {seg.describe.highlights.slice(0, 4).map((h, i) => (
                  <li key={i} className="flex gap-2 text-sm text-white/90">
                    <SparkleIcon size={16} className="mt-0.5 flex-none text-[#a9c2ff]" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <div className="pointer-events-auto justify-self-stretch rounded-2xl border border-white/18 bg-black/42 p-3 shadow-[0_24px_70px_rgba(0,0,0,.35)] backdrop-blur-md lg:max-w-[520px] lg:justify-self-end">
            <div className="mb-3 flex gap-1.5">
              {segments.map((s, i) => (
                <button
                  key={`${s.label}-${i}`}
                  onClick={() => setIdx(i)}
                  className={`h-1.5 flex-1 rounded-full ${i <= idx ? "bg-white" : "bg-white/25"}`}
                  aria-label={`Tới ${s.label}`}
                />
              ))}
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => go(-1)} disabled={idx === 0} className="flex h-11 w-11 items-center justify-center rounded-full border border-white/25 bg-white/10 text-white disabled:opacity-40"><CaretLeftIcon size={18} /></button>
              <button onClick={toggle} className="flex h-12 flex-1 items-center justify-center gap-2 rounded-full bg-white text-sm font-semibold text-black hover:bg-white/90">
                {playing ? <><PauseIcon size={17} /> Tạm dừng</> : <><PlayIcon size={17} /> Phát thuyết minh</>}
              </button>
              <button onClick={() => go(1)} disabled={idx === segments.length - 1} className="flex h-11 w-11 items-center justify-center rounded-full border border-white/25 bg-white/10 text-white disabled:opacity-40"><CaretRightIcon size={18} /></button>
              <button onClick={restart} className="flex h-11 w-11 items-center justify-center rounded-full border border-white/25 bg-white/10 text-white"><ArrowCounterClockwiseIcon size={18} /></button>
            </div>
            <p className="mt-2 text-center text-xs text-white/58">
              Ưu tiên VieNeu-TTS qua backend. Nếu model chưa cài, hệ thống tự dùng giọng trình duyệt.
            </p>
            <div className="mt-3 max-h-[22dvh] overflow-auto rounded-xl border border-white/12 bg-black/20 p-2">
              <p className="mb-2 px-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-white/55">
                Manifest tuyến
              </p>
              <div className="grid gap-1.5">
                {manifest.steps.map((step, i) => (
                  <button
                    key={step.id}
                    type="button"
                    onClick={() => setIdx(i)}
                    className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs ${
                      i === idx ? "bg-white text-black" : "bg-white/8 text-white/76 hover:bg-white/14"
                    }`}
                  >
                    <span className={`flex h-5 w-5 flex-none items-center justify-center rounded-full text-[10px] ${
                      i === idx ? "bg-black text-white" : "bg-white/12 text-white"
                    }`}>
                      {step.sequence}
                    </span>
                    <span className="min-w-0 flex-1 truncate">{step.label}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] ${
                      step.has_audio
                        ? i === idx ? "bg-black/10 text-black" : "bg-emerald-400/18 text-emerald-100"
                        : i === idx ? "bg-black/10 text-black/70" : "bg-white/10 text-white/50"
                    }`}>
                      {step.has_audio ? "WAV" : "Fallback"}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
