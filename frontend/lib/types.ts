// Mirrors builder/schemas.py SceneBundle (contract v1.0). Keep field names in sync.

export type SpaceType = "office" | "residential" | "retail" | "mixed" | "education";

export interface GenerateInput {
  project_name: string;
  space_type: SpaceType;
  description: string;
  target_audience: string;
  floors: number | null;
  rooms_per_floor: number | null;
  occupancy: number | null;
}

export interface BuildingSpec {
  space_type: SpaceType;
  floors: number;
  rooms_per_floor: number;
  occupancy: number;
  footprint_w: number;
  footprint_d: number;
  floor_height: number;
  layout_hint: string;
  palette: string;
}

export interface DescriberOutput {
  title: string;
  summary: string;
  highlights: string[];
  digitization_tips: string[];
}

export interface ModelInfo {
  glb: string;
  backend: string;
  tri_count: number;
  size_kb: number;
}

export interface RunMeta {
  llm_provider: string;
  build_ms: number;
  created_at: string;
}

export interface Panorama {
  prompt: string;
  image: string;
  status: string; // "pending" | "ready"
}

export interface Room {
  id: string;
  name: string;
  type: string;
  x: number;
  z: number;
  w: number;
  d: number;
  area: number;
  description: string;
  panorama?: Panorama | null;
}

export interface Floor {
  index: number;
  name: string;
  elevation: number;
  rooms: Room[];
}

export interface Structure {
  floors: Floor[];
  room_types: string[];
}

export interface SceneBundle {
  id: string;
  version: string;
  input: GenerateInput;
  spec: BuildingSpec;
  describer: DescriberOutput;
  model: ModelInfo;
  meta: RunMeta;
  structure?: Structure | null;
}

export const ROOM_TYPE_LABELS: Record<string, string> = {
  reception: "Lễ tân",
  meeting: "Phòng họp",
  open_work: "Khu làm việc mở",
  manager: "Quản lý",
  service: "Kỹ thuật / Dịch vụ",
  apartment: "Căn hộ",
  shop: "Gian hàng",
  fnb: "Khu F&B",
  classroom: "Phòng học",
  lab: "Phòng thực hành",
  office: "Văn phòng",
  default: "Phòng",
};

export const ROOM_TYPE_COLORS: Record<string, string> = {
  reception: "#cdd9f5",
  meeting: "#9db4e8",
  open_work: "#dfe6f6",
  manager: "#b6c6ee",
  service: "#e3e0d6",
  apartment: "#dfe6f6",
  shop: "#cdd9f5",
  fnb: "#ecdcc4",
  classroom: "#d7e3d6",
  lab: "#cfe0e6",
  office: "#dfe6f6",
  default: "#dde2ea",
};

export interface ArtifactIndex {
  version: string;
  scenes: string[];
}

// ---- Guided tour (AI vision describe + narrated walkthrough) -------------- //
export type IndustryTone = "real_estate" | "retail" | "exhibition";

export const INDUSTRY_LABELS: Record<IndustryTone, string> = {
  real_estate: "Bất động sản",
  retail: "Bán lẻ",
  exhibition: "Triển lãm",
};

export interface StopDescribe {
  title: string;
  description: string;
  highlights: string[];
}

export interface TourStop {
  id: string;
  image: string;
  kind: string; // photo | panorama
  describe: StopDescribe;
  narration: string;
}

export interface Tour {
  id: string;
  project_name: string;
  industry: IndustryTone;
  intro: string;
  stops: TourStop[];
  outro: string;
  created_at?: string;
}

export interface TourManifestStep {
  id: string;
  label: string;
  source_stop_id?: string;
  sequence: number;
  image: string;
  kind: string;
  has_audio: boolean;
}

export interface TourManifest {
  version: string;
  project_name: string;
  total_segments: number;
  audio_segments: number;
  final_segment_id: string;
  steps: TourManifestStep[];
  created_at: string;
}

// Client-side fallback (static mode, no backend): mirrors builder/llm/mock.py.
export const VISION_TPL: Record<IndustryTone, StopDescribe> = {
  real_estate: {
    title: "Không gian sống đẳng cấp, sẵn sàng để cảm nhận",
    description:
      "Bước vào không gian này, khách hàng cảm nhận ngay sự thoáng đãng và chỉn chu trong từng đường nét. Ánh sáng tự nhiên cùng vật liệu hoàn thiện tạo cảm giác sang trọng mà vẫn ấm cúng, rất phù hợp cho nhu cầu an cư và đầu tư.",
    highlights: [
      "Bố cục mở tối ưu công năng và tầm nhìn",
      "Ánh sáng tự nhiên dồi dào suốt cả ngày",
      "Vật liệu hoàn thiện cao cấp, bền đẹp theo thời gian",
      "Vị trí và tiện ích thuận tiện cho cuộc sống hiện đại",
    ],
  },
  retail: {
    title: "Mặt bằng bán lẻ thu hút, tối ưu trải nghiệm mua sắm",
    description:
      "Không gian được tổ chức để dẫn dắt dòng khách mượt mà, tối đa hóa khả năng trưng bày và tương tác với sản phẩm. Ánh sáng và bố cục làm nổi bật điểm nhấn thương hiệu, khuyến khích khách dừng lại lâu hơn.",
    highlights: [
      "Luồng di chuyển dẫn khách qua các điểm trưng bày chính",
      "Khu vực điểm nhấn làm nổi bật sản phẩm chủ lực",
      "Ánh sáng tôn lên màu sắc và chất liệu hàng hóa",
      "Mặt tiền và lối vào thu hút khách qua đường",
    ],
  },
  exhibition: {
    title: "Không gian triển lãm dẫn dắt hành trình khám phá",
    description:
      "Không gian được thiết kế cho một hành trình tham quan có chủ đích: luồng di chuyển rõ ràng, ánh sáng định hướng sự chú ý vào hiện vật, và các điểm dừng tạo nhịp cảm xúc cho người xem.",
    highlights: [
      "Luồng tham quan mạch lạc, dẫn dắt theo câu chuyện",
      "Ánh sáng trưng bày làm nổi bật hiện vật",
      "Điểm dừng tạo nhịp và khoảng lặng cho trải nghiệm",
      "Không gian linh hoạt cho nhiều loại nội dung trưng bày",
    ],
  },
};

export const SPACE_LABELS: Record<SpaceType, string> = {
  office: "Văn phòng",
  residential: "Tòa nhà ở",
  retail: "Bán lẻ",
  mixed: "Hỗn hợp",
  education: "Giáo dục",
};
