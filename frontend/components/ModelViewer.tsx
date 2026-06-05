"use client";

import { useEffect } from "react";

// Wraps Google's <model-viewer> web component. The module is imported on the
// client only (it registers the custom element and is large), so it stays out of
// the server bundle and below the hero's critical path.
export function ModelViewer({
  src,
  alt,
  className,
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  useEffect(() => {
    import("@google/model-viewer");
  }, []);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const MV: any = "model-viewer";
  return (
    <MV
      src={src}
      alt={alt}
      camera-controls
      auto-rotate
      auto-rotate-delay={800}
      rotation-per-second="18deg"
      interaction-prompt="none"
      shadow-intensity="0.6"
      exposure="1.05"
      camera-orbit="35deg 72deg auto"
      className={className}
      style={{ width: "100%", height: "100%", backgroundColor: "var(--bg-subtle)" }}
    />
  );
}
