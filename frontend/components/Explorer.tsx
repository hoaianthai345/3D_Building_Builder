"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import {
  type SceneBundle,
  type Room,
  ROOM_TYPE_LABELS,
  ROOM_TYPE_COLORS,
} from "@/lib/types";
import { PanoramaViewer } from "./PanoramaViewer";
import { XIcon } from "@phosphor-icons/react";

// name -> floor index ("roof" for the cap, null for nothing structural)
function floorOf(name: string): number | "roof" | null {
  let m: RegExpMatchArray | null;
  if ((m = name.match(/^room_(\d+)_/))) return Number(m[1]);
  if ((m = name.match(/^wall_room_(\d+)_/))) return Number(m[1]);
  if ((m = name.match(/^floorplate_(\d+)/))) return Number(m[1]);
  if (name === "roof") return "roof";
  return null;
}

type ViewState = {
  explode: number;
  activeFloor: number | null;
  section: boolean;
  sectionX: number;
  selectedId: string | null;
};

function BuildingModel({
  url,
  floorHeight,
  floors,
  view,
  onPick,
}: {
  url: string;
  floorHeight: number;
  floors: number;
  view: ViewState;
  onPick: (id: string | null) => void;
}) {
  const gltf = useGLTF(url);
  const { gl } = useThree();

  const { scene, meshes } = useMemo(() => {
    const s = gltf.scene.clone(true);
    const list: THREE.Mesh[] = [];
    s.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      mesh.material = (mesh.material as THREE.Material).clone();
      mesh.userData.origY = mesh.position.y;
      mesh.userData.floor = floorOf(mesh.name);
      mesh.userData.isRoom = /^room_\d+_/.test(mesh.name);
      list.push(mesh);
    });
    return { scene: s, meshes: list };
  }, [gltf, url]);

  const plane = useMemo(() => new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0), []);

  useEffect(() => {
    gl.localClippingEnabled = true;
  }, [gl]);

  useFrame(() => {
    const gap = floorHeight * 1.15;
    plane.constant = view.sectionX;
    for (const o of meshes) {
      const f = o.userData.floor as number | "roof" | null;
      const idx = f === "roof" ? floors : typeof f === "number" ? f : 0;
      const targetY = o.userData.origY + idx * gap * view.explode;
      o.position.y += (targetY - o.position.y) * 0.22;

      o.visible =
        view.activeFloor == null ? true : f === view.activeFloor || f === null;

      const mat = o.material as THREE.MeshStandardMaterial;
      mat.clippingPlanes = view.section ? [plane] : [];
      if (o.userData.isRoom && mat.emissive) {
        const sel = o.name === view.selectedId;
        mat.emissive.setHex(sel ? 0x1f4fc4 : 0x000000);
        mat.emissiveIntensity = sel ? 0.45 : 0;
      }
    }
  });

  return (
    <primitive
      object={scene}
      onPointerDown={(e: any) => {
        e.stopPropagation();
        onPick(e.object?.userData?.isRoom ? e.object.name : null);
      }}
    />
  );
}

export function Explorer({ bundle, glbUrl }: { bundle: SceneBundle; glbUrl: string }) {
  const floors = bundle.spec.floors;
  const totalH = bundle.spec.floors * bundle.spec.floor_height;
  const artifactsBase = glbUrl.replace(/\/[^/]+\.glb$/, "");
  const [panoRoom, setPanoRoom] = useState<Room | null>(null);
  const [view, setView] = useState<ViewState>({
    explode: 0,
    activeFloor: null,
    section: false,
    sectionX: 0,
    selectedId: null,
  });

  const selectedRoom: Room | null = useMemo(() => {
    if (!view.selectedId || !bundle.structure) return null;
    for (const f of bundle.structure.floors) {
      const r = f.rooms.find((rm) => rm.id === view.selectedId);
      if (r) return r;
    }
    return null;
  }, [view.selectedId, bundle.structure]);

  const activeFloorName =
    view.activeFloor != null
      ? bundle.structure?.floors[view.activeFloor]?.name ?? `Tầng ${view.activeFloor + 1}`
      : null;

  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--bg-subtle)]">
      <Canvas
        camera={{ position: [totalH * 1.6 + 8, totalH + 6, totalH * 1.8 + 10], fov: 42 }}
        onPointerMissed={() => setView((v) => ({ ...v, selectedId: null }))}
      >
        <hemisphereLight args={[0xffffff, 0xb9b4a7, 1.0]} />
        <directionalLight position={[10, 20, 8]} intensity={1.4} />
        <directionalLight position={[-8, 10, -6]} intensity={0.5} />
        <Suspense fallback={null}>
          <BuildingModel
            url={glbUrl}
            floorHeight={bundle.spec.floor_height}
            floors={floors}
            view={view}
            onPick={(id) => setView((v) => ({ ...v, selectedId: id }))}
          />
        </Suspense>
        <OrbitControls makeDefault target={[0, totalH * 0.4, 0]} maxPolarAngle={Math.PI / 2.05} />
      </Canvas>

      {/* Breadcrumb */}
      <div className="pointer-events-none absolute left-3 top-3 flex flex-wrap items-center gap-1.5 text-xs">
        <span className="rounded-full bg-white/90 px-2.5 py-1 font-medium text-[var(--text)] shadow-[var(--shadow-sm)]">
          {bundle.input.project_name}
        </span>
        {activeFloorName && (
          <>
            <span className="text-[var(--text-faint)]">/</span>
            <span className="rounded-full bg-white/90 px-2.5 py-1 text-[var(--text-muted)] shadow-[var(--shadow-sm)]">
              {activeFloorName}
            </span>
          </>
        )}
        {selectedRoom && (
          <>
            <span className="text-[var(--text-faint)]">/</span>
            <span className="rounded-full bg-[var(--accent-strong)] px-2.5 py-1 font-medium text-white shadow-[var(--shadow-sm)]">
              {selectedRoom.name}
            </span>
          </>
        )}
      </div>

      {/* Controls */}
      <div className="absolute right-3 top-3 w-52 space-y-3 rounded-xl border border-[var(--border)] bg-white/92 p-3 text-xs shadow-[var(--shadow-md)] backdrop-blur">
        <div>
          <label className="mb-1 block font-medium text-[var(--text)]">Tách tầng</label>
          <input
            type="range" min={0} max={1} step={0.01} value={view.explode}
            onChange={(e) => setView((v) => ({ ...v, explode: Number(e.target.value) }))}
            className="w-full accent-[var(--accent-strong)]"
          />
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between">
            <label className="font-medium text-[var(--text)]">Cắt lát</label>
            <button
              onClick={() => setView((v) => ({ ...v, section: !v.section }))}
              className={`rounded-full px-2 py-0.5 text-[11px] ${
                view.section
                  ? "bg-[var(--accent-strong)] text-white"
                  : "border border-[var(--border-strong)] text-[var(--text-muted)]"
              }`}
            >
              {view.section ? "Bật" : "Tắt"}
            </button>
          </div>
          {view.section && (
            <input
              type="range" min={-bundle.spec.footprint_w / 2} max={bundle.spec.footprint_w / 2}
              step={0.2} value={view.sectionX}
              onChange={(e) => setView((v) => ({ ...v, sectionX: Number(e.target.value) }))}
              className="w-full accent-[var(--accent-strong)]"
            />
          )}
        </div>

        <div>
          <label className="mb-1 block font-medium text-[var(--text)]">Tầng</label>
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setView((v) => ({ ...v, activeFloor: null, selectedId: null }))}
              className={`rounded-full px-2 py-0.5 ${
                view.activeFloor == null
                  ? "bg-[var(--accent-strong)] text-white"
                  : "border border-[var(--border-strong)] text-[var(--text-muted)]"
              }`}
            >
              Tất cả
            </button>
            {Array.from({ length: floors }).map((_, i) => (
              <button
                key={i}
                onClick={() => setView((v) => ({ ...v, activeFloor: i, selectedId: null }))}
                className={`rounded-full px-2 py-0.5 ${
                  view.activeFloor === i
                    ? "bg-[var(--accent-strong)] text-white"
                    : "border border-[var(--border-strong)] text-[var(--text-muted)]"
                }`}
              >
                {i + 1}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Room info card */}
      {selectedRoom && (
        <div className="absolute bottom-3 left-3 w-[min(20rem,calc(100%-1.5rem))] rounded-xl border border-[var(--border)] bg-white/95 p-4 shadow-[var(--shadow-md)] backdrop-blur">
          <div className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-full"
              style={{ background: ROOM_TYPE_COLORS[selectedRoom.type] ?? ROOM_TYPE_COLORS.default }}
            />
            <h3 className="font-semibold text-[var(--text)]">{selectedRoom.name}</h3>
          </div>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            {ROOM_TYPE_LABELS[selectedRoom.type] ?? "Phòng"} · {selectedRoom.area} m²
          </p>
          {selectedRoom.description && (
            <p className="mt-2 text-sm leading-relaxed text-[var(--text)]">
              {selectedRoom.description}
            </p>
          )}
          {selectedRoom.panorama?.status === "ready" && selectedRoom.panorama?.image ? (
            <button
              onClick={() => setPanoRoom(selectedRoom)}
              className="mt-3 w-full rounded-[10px] bg-[var(--accent-strong)] py-2 text-xs font-medium text-white transition hover:bg-[var(--accent-hover)]"
            >
              Bước vào (360)
            </button>
          ) : (
            <button
              disabled
              title={selectedRoom.panorama?.prompt || "Sắp có: tham quan 360 do AI dựng"}
              className="mt-3 w-full cursor-not-allowed rounded-[10px] border border-dashed border-[var(--border-strong)] py-2 text-xs text-[var(--text-faint)]"
            >
              Ảnh 360 sắp có
            </button>
          )}
        </div>
      )}

      {/* Panorama "step inside" modal */}
      {panoRoom?.panorama?.image && (
        <div className="absolute inset-0 z-50 flex flex-col bg-black/80">
          <div className="flex items-center justify-between px-4 py-3 text-white">
            <p className="text-sm font-medium">{panoRoom.name} · tham quan 360</p>
            <button
              onClick={() => setPanoRoom(null)}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-white/15 hover:bg-white/25"
              aria-label="Đóng"
            >
              <XIcon size={16} />
            </button>
          </div>
          <div className="flex-1">
            <PanoramaViewer image={`${artifactsBase}/${panoRoom.panorama.image}`} />
          </div>
        </div>
      )}
    </div>
  );
}
