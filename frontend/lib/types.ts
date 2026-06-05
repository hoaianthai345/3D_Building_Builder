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

export const SPACE_LABELS: Record<SpaceType, string> = {
  office: "Văn phòng",
  residential: "Tòa nhà ở",
  retail: "Bán lẻ",
  mixed: "Hỗn hợp",
  education: "Giáo dục",
};
