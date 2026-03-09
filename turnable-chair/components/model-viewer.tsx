"use client";

import { useEffect, useState } from "react";

interface ModelViewerProps {
  chairId: string;
}

export default function ModelViewer({ chairId }: ModelViewerProps) {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Only import on client side
    import("@google/model-viewer").then(() => {
      setIsLoaded(true);
    }).catch(err => {
      console.error("Failed to load model-viewer:", err);
    });
  }, []);

  if (!isLoaded) {
    return (
      <div className="w-full h-full bg-gray-50 flex items-center justify-center">
        <div className="font-mono text-[10px] text-gray-300 uppercase tracking-widest">Initialiserer 3D...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-white flex flex-col items-center justify-center relative group">
      {/* 3D Model Viewer */}
      <model-viewer
        src={`/api/model/${chairId}`}
        alt={`3D model of chair ${chairId}`}
        auto-rotate
        camera-controls
        shadow-intensity="1"
        environment-image="neutral"
        exposure="1"
        touch-action="pan-y"
        style={{ width: "100%", height: "100%", outline: "none" } as any}
      ></model-viewer>
    </div>
  );
}
