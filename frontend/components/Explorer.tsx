"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, useGLTF, Environment, Lightformer, ContactShadows } from "@react-three/drei";
import * as THREE from "three";
import {
  type SceneBundle,
  type Room,
  ROOM_TYPE_LABELS,
  ROOM_TYPE_COLORS,
} from "@/lib/types";
import { PanoramaViewer } from "./PanoramaViewer";
import { XIcon } from "@phosphor-icons/react";

// interior node -> floor index; null for exterior shell / non-floor nodes
function floorOf(name: string): number | null {
  let m: RegExpMatchArray | null;
  if ((m = name.match(/^room_(\d+)_/))) return Number(m[1]);
  if ((m = name.match(/^wall_room_(\d+)_/))) return Number(m[1]);
  if ((m = name.match(/^floorplate_(\d+)/))) return Number(m[1]);
  return null;
}

type ViewState = {
  explode: number;
  activeFloor: number | null;
  section: boolean;
  sectionX: number;
  selectedId: string | null;
  showShell: boolean;
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
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      if (mesh.name.includes("glass")) {
        // tinted curtain-wall glass: reflective when an env map is present, but a
        // blue base + slight emissive keeps it reading as glass even without one
        mesh.material = new THREE.MeshPhysicalMaterial({
          color: new THREE.Color("#7799d6"),
          metalness: 0.0,
          roughness: 0.42,
          envMapIntensity: 0.9,
          clearcoat: 0.35,
          clearcoatRoughness: 0.2,
          emissive: new THREE.Color("#1a335f"),
          emissiveIntensity: 0.18,
        });
      } else {
        const m = (mesh.material as THREE.Material).clone() as THREE.MeshStandardMaterial;
        if ("envMapIntensity" in m) m.envMapIntensity = 1.0;
        mesh.material = m;
      }
      mesh.userData.origY = mesh.position.y;
      mesh.userData.floor = floorOf(mesh.name);
      mesh.userData.isRoom = /^room_\d+_/.test(mesh.name);
      mesh.userData.isShell = mesh.name.startsWith("shell_");
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
    const interiorShown =
      !view.showShell || view.explode > 0.02 || view.activeFloor != null;
    for (const o of meshes) {
      const mat = o.material as THREE.MeshStandardMaterial;
      mat.clippingPlanes = view.section ? [plane] : [];

      if (o.userData.isShell) {
        o.visible = view.showShell && view.explode < 0.02 && view.activeFloor == null;
        continue;
      }

      const f = o.userData.floor as number | null;
      const idx = typeof f === "number" ? f : 0;
      const targetY = o.userData.origY + idx * gap * view.explode;
      o.position.y += (targetY - o.position.y) * 0.22;

      o.visible = view.activeFloor != null ? f === view.activeFloor : interiorShown;

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
  const footprint = Math.max(bundle.spec.footprint_w, bundle.spec.footprint_d);
  const artifactsBase = glbUrl.replace(/\/[^/]+\.glb$/, "");
  const [panoRoom, setPanoRoom] = useState<Room | null>(null);
  const [view, setView] = useState<ViewState>({
    explode: 0,
    activeFloor: null,
    section: false,
    sectionX: 0,
    selectedId: null,
    showShell: true,
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
        shadows
        dpr={[1, 2]}
        camera={{ position: [totalH * 1.6 + 8, totalH + 6, totalH * 1.8 + 10], fov: 42 }}
        onPointerMissed={() => setView((v) => ({ ...v, selectedId: null }))}
      >
        <color attach="background" args={["#eef0f3"]} />
        <ambientLight intensity={0.5} />
        <directionalLight
          castShadow
          position={[totalH * 0.8 + 12, totalH * 1.6 + 22, totalH * 0.5 + 14]}
          intensity={2.4}
          shadow-mapSize={[2048, 2048]}
          shadow-camera-near={1}
          shadow-camera-far={totalH * 4 + 80}
          shadow-camera-left={-(footprint * 2 + totalH)}
          shadow-camera-right={footprint * 2 + totalH}
          shadow-camera-top={totalH * 1.6 + 24}
          shadow-camera-bottom={-12}
          shadow-bias={-0.0004}
        />
        <Environment resolution={256}>
          <Lightformer intensity={2.4} position={[0, totalH, -totalH]} scale={[totalH * 2, totalH, 1]} />
          <Lightformer intensity={0.9} position={[-totalH, totalH * 0.6, totalH]} scale={[totalH, totalH, 1]} />
          <Lightformer intensity={0.9} position={[totalH, totalH * 0.6, totalH]} scale={[totalH, totalH, 1]} />
          <Lightformer form="ring" intensity={1.1} color="#fff3e6" position={[0, totalH * 1.5, 0]} scale={totalH} />
        </Environment>
        <Suspense fallback={null}>
          <BuildingModel
            url={glbUrl}
            floorHeight={bundle.spec.floor_height}
            floors={floors}
            view={view}
            onPick={(id) => setView((v) => ({ ...v, selectedId: id }))}
          />
        </Suspense>
        <ContactShadows
          position={[0, 0.04, 0]}
          scale={footprint * 4}
          blur={2.4}
          opacity={0.5}
          far={totalH}
        />
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
        <div className="flex items-center justify-between">
          <label className="font-medium text-[var(--text)]">Vỏ ngoài</label>
          <button
            onClick={() => setView((v) => ({ ...v, showShell: !v.showShell }))}
            className={`rounded-full px-2 py-0.5 text-[11px] ${
              view.showShell
                ? "bg-[var(--accent-strong)] text-white"
                : "border border-[var(--border-strong)] text-[var(--text-muted)]"
            }`}
          >
            {view.showShell ? "Hiện" : "Ẩn"}
          </button>
        </div>

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
