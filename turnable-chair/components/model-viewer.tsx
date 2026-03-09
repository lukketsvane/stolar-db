"use client";

import { useEffect, useState } from "react";

interface ModelViewerProps {
  chairId: string;
}

export default function ModelViewer({ chairId }: ModelViewerProps) {
  const [hasError, setHasError] = useState(false);

  return (
    <div className="w-full h-full bg-white flex flex-col items-center justify-center relative">
      {hasError ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border border-gray-200 rounded-full flex items-center justify-center text-gray-300 font-mono text-xl">!</div>
          <div className="font-mono text-[10px] text-gray-400 uppercase tracking-widest text-center">
            Modell ikkje funne<br/>
            <span className="opacity-50">{chairId}</span>
          </div>
        </div>
      ) : (
        <model-viewer
          src={`/api/model/${chairId}`}
          alt={`3D model of chair ${chairId}`}
          auto-rotate
          camera-controls
          shadow-intensity="1"
          environment-image="neutral"
          exposure="1"
          touch-action="pan-y"
          loading="eager"
          reveal="auto"
          style={{ width: "100%", height: "100%", outline: "none" } as any}
          onerror={() => setHasError(true)}
        ></model-viewer>
      )}
    </div>
  );
}
