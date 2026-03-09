"use client";

import { useEffect } from "react";

interface ModelViewerProps {
  chairId: string;
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      "model-viewer": any;
    }
  }
}

export default function ModelViewer({ chairId }: ModelViewerProps) {
  useEffect(() => {
    // Dynamically import model-viewer only on the client
    import("@google/model-viewer");
  }, []);

  return (
    <div className="w-full h-full bg-gray-50 flex flex-col items-center justify-center relative group">
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
        style={{ width: "100%", height: "100%", "--poster-color": "transparent" } as any}
        loading="lazy"
      ></model-viewer>
    </div>
  );
}
