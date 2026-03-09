"use client";

import { useEffect, useState } from "react";

interface ModelViewerProps {
  chairId: string;
}

export default function ModelViewer({ chairId }: ModelViewerProps) {
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [hasError, setHasError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Load the mapping file
    fetch("/data/model_map.json")
      .then(res => res.json())
      .then(map => {
        if (map[chairId]) {
          setModelUrl(map[chairId]);
        } else {
          setHasError(true);
        }
      })
      .catch(() => setHasError(true));

    // Register model-viewer
    import("@google/model-viewer").then(() => {
      setIsLoaded(true);
    });
  }, [chairId]);

  if (hasError) {
    return (
      <div className="w-full h-full bg-white flex flex-col items-center justify-center">
        <div className="text-[10px] font-mono text-gray-300 uppercase tracking-widest">3D-modell ikkje tilgjengeleg</div>
      </div>
    );
  }

  if (!isLoaded || !modelUrl) {
    return (
      <div className="w-full h-full bg-white flex items-center justify-center">
        <div className="font-mono text-[10px] text-gray-200 animate-pulse">Laster 3D...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-white flex flex-col items-center justify-center relative">
      <model-viewer
        src={modelUrl}
        alt={`3D model of chair ${chairId}`}
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
        onerror={() => setHasError(true)}
      ></model-viewer>
    </div>
  );
}
