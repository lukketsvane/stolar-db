"use client";

import { useEffect, useState } from "react";

interface ModelViewerProps {
  src: string;
}

export default function ModelViewer({ src }: ModelViewerProps) {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Register model-viewer if not already registered
    if (!customElements.get("model-viewer")) {
      import("@google/model-viewer").then(() => {
        setIsLoaded(true);
      });
    } else {
      setIsLoaded(true);
    }
  }, []);

  if (!isLoaded) {
    return (
      <div className="w-full h-full bg-white flex items-center justify-center">
        <div className="font-mono text-[10px] text-gray-200 animate-pulse">Laster 3D...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-white flex flex-col items-center justify-center relative">
      <model-viewer
        src={src}
        alt="3D model"
        auto-rotate
        camera-controls
        disable-zoom
        disable-pan
        shadow-intensity="1"
        environment-image="neutral"
        exposure="1"
        touch-action="pan-y"
        loading="eager"
        reveal="auto"
        style={{ width: "100%", height: "100%", outline: "none" } as any}
      ></model-viewer>
    </div>
  );
}
