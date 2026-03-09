"use client"

import type React from "react"
import { useState, useEffect, useMemo, Suspense, useCallback } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import FrameScrubber from "../components/frame-scrubber"
import ModelViewer from "../components/model-viewer"
import { Search, Filter, X, ChevronRight, ChevronLeft, ExternalLink, Maximize2 } from "lucide-react"

interface ChairItem {
  id: string
  symbol: string
  number: string
  name: string
  title: string
  text: string
  specs: string
  producer: string
  year: string
  materials: string
  techniques: string
  inventoryNr: string
  location: string
  acquisition: string
  description: string
  classification: string
  nmUrl: string
  height?: number
  width?: number
  depth?: number
  seatHeight?: number
  has3d?: boolean
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
  const [allData, setAllData] = useState<ChairItem[]>([])
  const [filteredData, setFilteredData] = useState<ChairItem[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedMaterial, setSelectedMaterial] = useState<string>("Alle")
  const [currentItem, setCurrentItem] = useState<ChairItem | null>(null)
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('3d')
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [has3dModel, setHas3dModel] = useState(false)

  useEffect(() => {
    fetch("/data/norske_stolar.json")
      .then(res => res.json())
      .then(data => {
        const uniqueMap = new Map();
        data.forEach((item: any) => {
          if (!uniqueMap.has(item.object_id)) {
            uniqueMap.set(item.object_id, {
              id: item.object_id,
              symbol: item.object_id.split("-")[0],
              number: item.object_id.split("-")[1],
              name: item.betegnelse || "Stol",
              title: item.title,
              text: item.betegnelse,
              specs: item.maal,
              producer: item.produsent,
              year: item.datering,
              materials: item.materialar,
              techniques: item.teknikk,
              inventoryNr: item.object_id,
              location: item.produksjonsstad,
              acquisition: item.erverving,
              description: item.beskriving,
              classification: item.klassifikasjon,
              nmUrl: item.nasjonalmuseet_url,
              height: item.hoegde_cm,
              width: item.breidde_cm,
              depth: item.djupn_cm,
              seatHeight: item.setehoegde_cm,
              has3d: false
            });
          }
        });
        const mapped = Array.from(uniqueMap.values());
        setAllData(mapped);
        setFilteredData(mapped);
      })
      .catch(err => console.error("Error loading database:", err))
  }, [])

  useEffect(() => {
    if (currentItem) {
      fetch(`/api/model/${currentItem.id}`, { method: 'HEAD' })
        .then(res => {
          setHas3dModel(res.ok);
          setViewMode(res.ok ? '3d' : '2d');
        })
        .catch(() => {
          setHas3dModel(false);
          setViewMode('2d');
        });
    }
  }, [currentItem]);

  useEffect(() => {
    const itemId = searchParams.get("item")
    if (itemId) {
      const item = allData.find(d => d.id === itemId)
      if (item) setCurrentItem(item)
    } else {
      setCurrentItem(null)
    }
  }, [searchParams, allData])

  useEffect(() => {
    let result = allData
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(item => 
        item.name.toLowerCase().includes(q) ||
        item.id.toLowerCase().includes(q) ||
        item.producer?.toLowerCase().includes(q) ||
        item.title?.toLowerCase().includes(q)
      )
    }
    if (selectedMaterial !== "Alle") {
      result = result.filter(item => item.materials?.includes(selectedMaterial))
    }
    setFilteredData(result)
  }, [searchQuery, selectedMaterial, allData])

  const navigateTo = useCallback((direction: 'next' | 'prev') => {
    if (!currentItem) return
    const currentIndex = filteredData.findIndex(item => item.id === currentItem.id)
    if (currentIndex === -1) return
    let nextIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1
    if (nextIndex >= filteredData.length) nextIndex = 0
    if (nextIndex < 0) nextIndex = filteredData.length - 1
    router.push(`/?item=${filteredData[nextIndex].id}`)
  }, [currentItem, filteredData, router])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!currentItem) return
      if (e.key === 'ArrowRight') navigateTo('next')
      if (e.key === 'ArrowLeft') navigateTo('prev')
      if (e.key === 'Escape') router.push('/')
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentItem, navigateTo, router])

  const groupedChairs = useMemo(() => {
    const groups: Record<string, ChairItem[]> = {}
    filteredData.forEach(item => {
      const c = getCentury(item.year)
      if (!groups[c]) groups[c] = []
      groups[c].push(item)
    })
    return groups
  }, [filteredData])

  const renderGridItem = (item: ChairItem) => (
    <div 
      key={item.id}
      onClick={() => router.push(`/?item=${item.id}`)}
      className="relative aspect-square border-black/10 cursor-pointer bg-white group hover:bg-gray-50 transition-all duration-300 overflow-hidden"
      style={{ borderWidth: "0.5px" }}
    >
      <div className="absolute top-1 left-1 font-mono font-bold text-[7px] text-black/20">{item.id}</div>
      <div className="flex flex-col items-center justify-center h-full p-4">
        <img 
          src={`/api/image/${item.id}`}
          onError={(e) => (e.currentTarget.src = "/placeholder.svg")}
          alt={item.name} 
          className="max-w-full max-h-[75%] object-contain group-hover:scale-110 transition-transform duration-700" 
        />
        <div className="mt-2 text-center">
          <div className="text-black font-sans font-black text-[8px] uppercase tracking-tighter line-clamp-1">
            {formatName(item.name)}
          </div>
          <div className="text-gray-300 font-mono text-[6px] uppercase tracking-widest mt-0.5">
            {item.year}
          </div>
        </div>
      </div>
    </div>
  )

  if (currentItem) {
    return (
      <div className="min-h-screen bg-white text-black flex flex-col lg:flex-row overflow-hidden">
        <div className="lg:flex-1 flex flex-col relative h-screen bg-white">
          <nav className="absolute top-8 left-8 right-8 z-50 flex justify-between items-center pointer-events-none">
            <button onClick={() => router.push("/")} className="pointer-events-auto bg-white/90 backdrop-blur px-5 py-2.5 rounded-full font-mono font-black uppercase text-[10px] tracking-widest border border-black/5 shadow-sm hover:bg-black hover:text-white transition-all">
              &larr; Galleri
            </button>
            {has3dModel && (
              <div className="flex gap-1 pointer-events-auto bg-gray-100/90 backdrop-blur p-1 rounded-full shadow-inner border border-black/5">
                <button onClick={() => setViewMode('2d')} className={`px-5 py-1.5 rounded-full text-[9px] font-mono font-black uppercase transition-all ${viewMode === '2d' ? 'bg-white text-black shadow-sm' : 'text-gray-400 hover:text-black'}`}>2D</button>
                <button onClick={() => setViewMode('3d')} className={`px-5 py-1.5 rounded-full text-[9px] font-mono font-black uppercase transition-all ${viewMode === '3d' ? 'bg-white text-black shadow-sm' : 'text-gray-400 hover:text-black'}`}>3D</button>
              </div>
            )}
          </nav>

          <div className="flex-1 flex items-center justify-center relative">
            <div className="w-full h-full max-w-[90vh] max-h-[90vh] p-12">
              {viewMode === '3d' ? (
                <ModelViewer chairId={currentItem.id} />
              ) : (
                <img src={`/api/image/${currentItem.id}`} className="w-full h-full object-contain animate-in fade-in zoom-in-95 duration-700" />
              )}
            </div>
          </div>

          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-4 z-50">
            <button onClick={() => navigateTo('prev')} className="bg-white/90 backdrop-blur p-4 rounded-full border border-black/5 shadow-sm hover:bg-black hover:text-white transition-all">
              <ChevronLeft size={18} />
            </button>
            <button onClick={() => navigateTo('next')} className="bg-white/90 backdrop-blur p-4 rounded-full border border-black/5 shadow-sm hover:bg-black hover:text-white transition-all">
              <ChevronRight size={18} />
            </button>
          </div>
        </div>

        <aside className="lg:w-[500px] border-l border-gray-100 bg-white p-8 lg:p-16 overflow-y-auto h-screen relative scroll-smooth selection:bg-black selection:text-white">
          <div className="max-w-md mx-auto space-y-16">
            <section>
              <div className="font-mono text-[10px] text-gray-300 uppercase tracking-[0.3em] mb-6 flex justify-between items-center">
                <span>{currentItem.id}</span>
                {!isSidebarOpen && <button onClick={() => setIsSidebarOpen(true)}><Maximize2 size={14}/></button>}
              </div>
              <h1 className="text-5xl font-sans font-black tracking-tighter uppercase leading-[0.9] mb-8">{formatName(currentItem.name)}</h1>
              {currentItem.title && currentItem.title !== currentItem.name && (
                <p className="text-xl font-serif italic text-gray-500 mb-8 leading-tight">{currentItem.title}</p>
              )}
              <div className="flex gap-4">
                <span className="bg-black text-white font-mono text-[9px] font-black px-3 py-1 uppercase tracking-widest">{currentItem.year}</span>
                <span className="border border-black/10 font-mono text-[9px] font-black px-3 py-1 uppercase tracking-widest text-gray-400">{currentItem.location?.split(",")[0]}</span>
              </div>
            </section>

            {currentItem.description && (
              <section className="border-t border-gray-50 pt-12">
                <h3 className="font-mono font-black text-[10px] uppercase tracking-[0.2em] text-gray-300 mb-6">Skildring</h3>
                <p className="text-base font-serif leading-relaxed text-gray-800">{currentItem.description}</p>
              </section>
            )}

            <section className="space-y-10 border-t border-gray-50 pt-12">
              {[
                { label: "Designar / Produsent", val: currentItem.producer },
                { label: "Materialar", val: currentItem.materials },
                { label: "Teknikk", val: currentItem.techniques },
                { label: "Klassifikasjon", val: currentItem.classification },
                { label: "Erverving", val: currentItem.acquisition }
              ].map(f => f.val && (
                <div key={f.label}>
                  <h3 className="font-mono font-black text-[9px] uppercase tracking-[0.2em] text-gray-300 mb-3">{f.label}</h3>
                  <p className="text-sm font-bold tracking-tight text-black uppercase">{f.val}</p>
                </div>
              ))}
            </section>

            {(currentItem.height || currentItem.width || currentItem.depth) && (
              <section className="border-t border-gray-50 pt-12">
                <h3 className="font-mono font-black text-[10px] uppercase tracking-[0.2em] text-gray-300 mb-6">Mål</h3>
                <div className="grid grid-cols-2 gap-4 font-mono text-[11px]">
                  {currentItem.height && <div className="flex justify-between border-b border-gray-50 pb-2"><span className="text-gray-400">Høgde</span><span className="font-black">{currentItem.height} cm</span></div>}
                  {currentItem.width && <div className="flex justify-between border-b border-gray-50 pb-2"><span className="text-gray-400">Breidde</span><span className="font-black">{currentItem.width} cm</span></div>}
                  {currentItem.depth && <div className="flex justify-between border-b border-gray-50 pb-2"><span className="text-gray-400">Djupn</span><span className="font-black">{currentItem.depth} cm</span></div>}
                  {currentItem.seatHeight && <div className="flex justify-between border-b border-gray-50 pb-2"><span className="text-gray-400">Setehøgde</span><span className="font-black">{currentItem.seatHeight} cm</span></div>}
                </div>
                <p className="text-[9px] text-gray-300 mt-4 italic">{currentItem.specs}</p>
              </section>
            )}

            <section className="pt-12">
              <a 
                href={currentItem.nmUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center w-full border border-black/5 p-6 hover:bg-gray-50 transition-all group"
              >
                <img src="/nasjonalmuseet_logo.jpg" alt="Nasjonalmuseet" className="h-8 w-auto object-contain opacity-80 group-hover:opacity-100 transition-opacity" />
              </a>
            </section>
          </div>
        </aside>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-black font-sans selection:bg-black selection:text-white">
      <header className="fixed top-0 left-0 right-0 bg-white/95 backdrop-blur-md z-50 border-b border-black/5 px-6 md:px-12 py-6 flex flex-col md:flex-row justify-between items-center gap-6">
        <h1 className="font-sans font-black text-3xl tracking-tighter uppercase italic">Stolar.</h1>
        <div className="flex items-center gap-4 w-full md:w-auto">
          <div className="relative flex-1 md:w-80">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300" size={16} />
            <input 
              type="text" 
              placeholder="Søk i objektdata..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-50 border-none rounded-full py-3 pl-12 pr-6 text-xs font-mono focus:ring-1 focus:ring-black outline-none transition-all"
            />
          </div>
          <div className="flex gap-2">
            {[ "I", "II", "III", "IV", "V" ].map((n, i) => (
              <button 
                key={n}
                onClick={() => router.push(i === 0 ? "/article" : i === 1 ? "/article/form" : i === 2 ? "/article/form-klassifikasjon" : i === 3 ? "/article/fff-rammeverk" : "/article/kappe")}
                className="w-10 h-10 rounded-full border border-black/5 flex items-center justify-center font-mono font-black text-xs hover:bg-black hover:text-white transition-all shadow-sm"
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="max-w-[2000px] mx-auto px-6 md:px-12 pt-48 pb-40">
        <div className="space-y-40">
          {Object.entries(groupedChairs).sort(([a], [b]) => a.localeCompare(b)).map(([century, chairs]) => (
            <section key={century}>
              <div className="flex items-baseline justify-between border-b border-black/10 pb-6 mb-12">
                <h2 className="font-mono font-black text-4xl tracking-tighter">{century}</h2>
                <span className="font-mono text-sm font-bold text-gray-300 uppercase tracking-[0.2em]">{chairs.length} objekt</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-12 border-t border-l border-black/10">
                {chairs.map(renderGridItem)}
              </div>
            </section>
          ))}
        </div>
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
