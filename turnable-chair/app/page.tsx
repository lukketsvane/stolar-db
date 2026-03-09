"use client"

import type React from "react"
import { useState, useEffect, useMemo, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import FrameScrubber from "../components/frame-scrubber"
import ModelViewer from "../components/model-viewer"

interface ChairItem {
  id: string
  symbol: string
  number: string
  name: string
  frames?: string[]
  thumb?: string
  source?: string
  text: string
  specs: string
  producer: string
  year: string
  materials: string
  techniques: string
  classification: string
  inventoryNr: string
  acquisition: string
  photo: string
  location: string
}

const formatName = (s: string) => {
  if (!s) return ""
  return s.split(/\s+/).map(w => w ? w[0].toUpperCase() + w.slice(1).toLowerCase() : w).join(" ")
}

const getCentury = (yearStr: string) => {
  if (!yearStr) return "Ukjent"
  const match = yearStr.match(/\d{4}/)
  if (!match) return "Ukjent"
  const year = parseInt(match[0])
  return `${Math.floor(year / 100) * 100}-talet`
}

function HomeContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [galleryData, setGalleryData] = useState<ChairItem[]>([])
  const [currentItem, setCurrentItem] = useState<ChairItem | null>(null)
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('3d')

  useEffect(() => {
    fetch("/data/chairs.json", { cache: "no-store" })
      .then(res => res.json())
      .then(data => {
        console.log("Loaded gallery data:", data.length, "items")
        setGalleryData(data)
      })
      .catch(err => console.error("Feil ved lasting av stolar:", err))
  }, [])

  useEffect(() => {
    const itemId = searchParams.get("item")
    if (itemId) {
      const item = galleryData.find(d => d.id === itemId)
      if (item) {
        console.log("Selected item:", item.name)
        setCurrentItem(item)
      }
    } else {
      setCurrentItem(null)
    }
  }, [searchParams, galleryData])

  const groupedChairs = useMemo(() => {
    const groups: Record<string, ChairItem[]> = {}
    galleryData.forEach(item => {
      const c = getCentury(item.year)
      if (!groups[c]) groups[c] = []
      groups[c].push(item)
    })
    return groups
  }, [galleryData])

  const renderGridItem = (item: ChairItem | null, i: number) => {
    if (!item) return <div key={`empty-${i}`} className="aspect-square border-black/5 bg-gray-50/30" style={{ borderWidth: "0.5px" }} />

    return (
      <div 
        key={item.id}
        onClick={() => router.push(`/?item=${item.id}`)}
        className="relative aspect-square border-black/20 cursor-pointer bg-white group hover:bg-gray-50 transition-all duration-300"
        style={{ borderWidth: "0.5px" }}
      >
        <div className="absolute top-1 left-1 font-mono font-bold text-[7px] lg:text-[9px] text-black/40">{item.symbol}</div>
        <div className="absolute top-1 right-1 font-mono font-bold text-[7px] lg:text-[9px] text-black/40">{item.number}</div>
        
        <div className="flex flex-col items-center justify-center h-full p-2">
          <div className="flex-1 flex items-center justify-center w-full overflow-hidden">
            {item.thumb ? (
              <img src={item.thumb} alt={item.name} className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform duration-500" />
            ) : (
              <div className="w-full h-full bg-gray-100 flex items-center justify-center text-[8px] text-gray-400">Inga bilete</div>
            )}
          </div>
          <div className="text-black font-sans font-bold text-[7px] lg:text-[9px] mt-1 truncate w-full text-center uppercase tracking-tighter group-hover:text-black">
            {formatName(item.name)}
          </div>
        </div>
      </div>
    )
  }

  if (currentItem) {
    return (
      <div className="min-h-screen bg-white text-black flex flex-col lg:flex-row overflow-hidden">
        {/* Mobile Nav */}
        <div className="lg:hidden fixed top-0 left-0 right-0 z-50 p-4 flex justify-between items-center bg-white/80 backdrop-blur-md">
          <button onClick={() => router.push("/")} className="font-mono font-black uppercase text-[10px]">&larr; Tilbake</button>
          <div className="flex gap-3">
            <button onClick={() => router.push("/article")} className="font-mono font-black uppercase text-[10px]">I</button>
            <button onClick={() => router.push("/article/form")} className="font-mono font-black uppercase text-[10px]">II</button>
            <button onClick={() => router.push("/article/form-klassifikasjon")} className="font-mono font-black uppercase text-[10px]">III</button>
            <button onClick={() => router.push("/article/fff-rammeverk")} className="font-mono font-black uppercase text-[10px]">IV</button>
            <button onClick={() => router.push("/article/kappe")} className="font-mono font-black uppercase text-[10px]">V</button>
          </div>
        </div>

        {/* Desktop Sidebar Info */}
        <div className="hidden lg:flex flex-col fixed top-12 left-12 z-40 pointer-events-none">
          <div className="font-mono font-black text-8xl leading-none tracking-tighter">{currentItem.symbol}</div>
          <div className="font-mono font-black text-4xl mt-2 tracking-tighter">{currentItem.number}</div>
          <div className="font-sans font-black text-xl mt-4 max-w-xs uppercase leading-tight">{formatName(currentItem.name)}</div>
        </div>

        <div className="hidden lg:flex fixed top-8 right-12 z-50 gap-6 items-center">
          <div className="flex bg-gray-100 p-1 rounded-full mr-4">
            <button 
              onClick={() => setViewMode('2d')}
              className={`px-3 py-1 text-[9px] font-mono font-black uppercase tracking-widest rounded-full transition-all ${viewMode === '2d' ? 'bg-black text-white shadow-sm' : 'text-gray-400 hover:text-black'}`}
            >
              2D
            </button>
            <button 
              onClick={() => setViewMode('3d')}
              className={`px-3 py-1 text-[9px] font-mono font-black uppercase tracking-widest rounded-full transition-all ${viewMode === '3d' ? 'bg-black text-white shadow-sm' : 'text-gray-400 hover:text-black'}`}
            >
              3D
            </button>
          </div>
          <button onClick={() => router.push("/")} className="font-mono font-black uppercase text-[10px] tracking-widest hover:line-through">Lukk</button>
          <div className="h-4 w-px bg-gray-200" />
          <button onClick={() => router.push("/article")} className="font-mono font-black uppercase text-[10px] tracking-widest hover:line-through">I</button>
          <button onClick={() => router.push("/article/form")} className="font-mono font-black uppercase text-[10px] tracking-widest hover:line-through">II</button>
          <button onClick={() => router.push("/article/form-klassifikasjon")} className="font-mono font-black uppercase text-[10px] tracking-widest hover:line-through">III</button>
          <button onClick={() => router.push("/article/fff-rammeverk")} className="font-mono font-black uppercase text-[10px] tracking-widest hover:line-through">IV</button>
          <button onClick={() => router.push("/article/kappe")} className="font-mono font-black uppercase text-[10px] tracking-widest hover:line-through">V</button>
        </div>

        {/* Main View (2D or 3D) */}
        <div className="flex-1 flex items-center justify-center bg-white relative">
          <div 
            id="main-view-container"
            className="w-full aspect-square max-w-[85vh] relative"
          >
            {viewMode === '3d' ? (
              <ModelViewer chairId={currentItem.id} />
            ) : (
              currentItem.frames && currentItem.frames.length > 0 ? (
                <FrameScrubber frames={currentItem.frames} fallback={currentItem.thumb} />
              ) : (
                <img src={currentItem.thumb} className="w-full h-full object-contain" />
              )
            )}
          </div>
        </div>

        {/* Metadata Sidebar */}
        <div className="lg:w-[450px] border-l border-gray-100 bg-gray-50/50 p-8 lg:p-16 overflow-y-auto h-screen">
          <div className="space-y-12 py-20 lg:py-0">
            <section>
              <h1 className="text-4xl font-sans font-black tracking-tighter uppercase leading-none mb-4">{formatName(currentItem.name)}</h1>
              <p className="font-mono text-gray-400 text-xs font-bold uppercase tracking-widest">{currentItem.year}</p>
            </section>

            <section className="space-y-4">
              <h2 className="font-mono font-black text-[10px] uppercase tracking-[0.3em] text-gray-300">Skildring</h2>
              <p className="text-lg font-serif leading-relaxed text-gray-800">{currentItem.text || "Skildring kjem snart..."}</p>
            </section>

            <div className="grid grid-cols-1 gap-y-8 border-t border-gray-100 pt-12">
              {[
                { label: "Mål", val: currentItem.specs, mono: true },
                { label: "Materialar", val: currentItem.materials },
                { label: "Teknikkar", val: currentItem.techniques },
                { label: "Stad", val: currentItem.location },
                { label: "Inventarnr", val: currentItem.inventoryNr, mono: true },
                { label: "Produsent", val: currentItem.producer }
              ].map(f => f.val && (
                <div key={f.label}>
                  <h3 className="font-mono font-black text-[9px] uppercase tracking-[0.2em] text-gray-300 mb-2">{f.label}</h3>
                  <p className={`text-sm font-bold ${f.mono ? 'font-mono' : 'font-sans'} text-black`}>{f.val}</p>
                </div>
              ))}
            </div>

            {currentItem.source && (
              <a href={currentItem.source} target="_blank" className="block pt-12 font-mono font-black text-[10px] uppercase tracking-widest hover:line-through">
                Sjå hos Nasjonalmuseet ↗
              </a>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-black font-sans selection:bg-black selection:text-white pb-40">
      <nav className="fixed top-8 right-8 z-50 flex gap-6 items-center">
        <div className="flex gap-4">
          <button onClick={() => router.push('/article')} className="font-mono font-black text-xs uppercase tracking-widest hover:line-through">I</button>
          <button onClick={() => router.push('/article/form')} className="font-mono font-black text-xs uppercase tracking-widest hover:line-through">II</button>
          <button onClick={() => router.push('/article/form-klassifikasjon')} className="font-mono font-black text-xs uppercase tracking-widest hover:line-through">III</button>
          <button onClick={() => router.push('/article/fff-rammeverk')} className="font-mono font-black text-xs uppercase tracking-widest hover:line-through">IV</button>
          <button onClick={() => router.push('/article/kappe')} className="font-mono font-black text-xs uppercase tracking-widest hover:line-through">V</button>
        </div>
      </nav>

      <div className="max-w-[1800px] mx-auto px-6 md:px-12 lg:px-24 pt-32 lg:pt-48">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between mb-20 lg:mb-32 gap-8">
          <h1 className="font-sans font-black text-6xl lg:text-[10rem] leading-[0.8] tracking-tighter">
            Norske<br/>stolar.
          </h1>
          <div className="flex flex-col items-start lg:items-end">
            <div className="font-mono font-black text-4xl lg:text-6xl tracking-tighter leading-none">
              {galleryData.length > 0 ? galleryData.length : ""}
            </div>
            <div className="font-mono text-xs uppercase tracking-widest font-bold text-gray-400 mt-2">Objekt i samlinga</div>
          </div>
        </div>
        
        {galleryData.length === 0 ? (
          <div className="py-20 text-center font-mono text-gray-200"></div>
        ) : (
          <div className="space-y-32">
            {Object.entries(groupedChairs).sort(([a], [b]) => a.localeCompare(b)).map(([century, chairs]) => (
              <section key={century}>
                <div className="flex items-baseline justify-between border-b border-black/10 pb-4 mb-8">
                  <h2 className="font-mono font-black text-3xl tracking-tighter">{century}</h2>
                  <span className="font-mono text-sm font-bold text-gray-300 uppercase tracking-widest">{chairs.length} stolar</span>
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 border-t border-l border-black/10">
                  {chairs.map((item, i) => renderGridItem(item, i))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-white"></div>}>
      <HomeContent />
    </Suspense>
  )
}
