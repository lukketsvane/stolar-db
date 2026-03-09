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
      >
        <div slot="poster" className="absolute inset-0 flex items-center justify-center bg-gray-50/50 backdrop-blur-sm">
          <div className="text-[10px] font-mono font-black uppercase tracking-[0.3em] text-gray-400 animate-pulse">
            Lastar 3D-modell...
          </div>
        </div>
      </model-viewer>

      {/* Instructions Overlay */}
      <div className="absolute bottom-12 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
        <div className="bg-black/80 backdrop-blur-md text-white text-[8px] font-mono font-black px-4 py-2 uppercase tracking-[0.2em] whitespace-nowrap">
          Klikk og drag for å rotere &bull; Scroll for å zoome
        </div>
      </div>
    </div>
  );
}
