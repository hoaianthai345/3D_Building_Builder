"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useTexture } from "@react-three/drei";
import { BackSide } from "three";

// Equirectangular 360 viewer for the "step inside" tour. Built on the three/R3F
// stack already in the project (no extra dependency): an inverted sphere with the
// panorama mapped on its inner face, camera at the center.
function PanoSphere({ image }: { image: string }) {
  const texture = useTexture(image);
  return (
    <mesh>
      <sphereGeometry args={[10, 64, 32]} />
      <meshBasicMaterial map={texture} side={BackSide} />
    </mesh>
  );
}

export function PanoramaViewer({ image }: { image: string }) {
  return (
    <Canvas camera={{ position: [0, 0, 0.1], fov: 75 }}>
      <Suspense fallback={null}>
        <PanoSphere image={image} />
      </Suspense>
      <OrbitControls
        enablePan={false}
        enableZoom
        minDistance={0.1}
        maxDistance={8}
        rotateSpeed={-0.4}
        zoomSpeed={0.6}
      />
    </Canvas>
  );
}
