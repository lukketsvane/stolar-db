"use client"

import type React from "react"
import { useState, useEffect, useMemo, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import FrameScrubber from "../components/frame-scrubber"
import ModelViewer from "../components/model-viewer"
import { Search, Filter, X, ChevronRight, ChevronLeft } from "lucide-react"

interface ChairItem {
  id: string
  symbol: string
  number: string
  name: string
  frames?: string[]
  thumb?: string
  text: string
  specs: string
  producer: string
  year: string
  materials: string
  techniques: string
  inventoryNr: string
  location: string
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

  useEffect(() => {
    // Load the full enriched database
    fetch("/data/norske_stolar.json")
      .then(res => res.json())
      .then(data => {
        // Map the flat JSON structure to our ChairItem interface
        const mapped: ChairItem[] = data.map((item: any) => ({
          id: item.object_id,
          symbol: item.object_id.split("-")[0],
          number: item.object_id.split("-")[1],
          name: item.title,
          thumb: `/NM_stolar/${item.object_id}/${item.object_id}.png`, // Tentative path
          text: item.betegnelse,
          specs: item.maal,
          producer: item.produsent,
          year: item.datering,
          materials: item.materialar,
          techniques: item.teknikk,
          inventoryNr: item.object_id,
          location: item.produksjonsstad,
          has3d: true // We assume 3D exists if it's in this filtered list
        }))
        setAllData(mapped)
        setFilteredData(mapped)
      })
      .catch(err => console.error("Error loading full database:", err))
  }, [])

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
      result = result.filter(item => 
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }
    if (selectedMaterial !== "Alle") {
      result = result.filter(item => item.materials?.includes(selectedMaterial))
    }
    setFilteredData(result)
  }, [searchQuery, selectedMaterial, allData])

  const groupedChairs = useMemo(() => {
    const groups: Record<string, ChairItem[]> = {}
    filteredData.forEach(item => {
      const c = getCentury(item.year)
      if (!groups[c]) groups[c] = []
      groups[c].push(item)
    })
    return groups
  }, [filteredData])

  const materials = useMemo(() => {
    const set = new Set<string>(["Alle"])
    allData.forEach(item => {
      if (item.materials) {
        item.materials.split(",").forEach(m => set.add(m.trim()))
      }
    })
    return Array.from(set).slice(0, 20) // Limit for UI
  }, [allData])

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
          src={`/bg-uniform black/${item.id}.png`} 
          onError={(e) => (e.currentTarget.src = "/placeholder.svg")}
          alt={item.name} 
          className="max-w-full max-h-[70%] object-contain group-hover:scale-110 transition-transform duration-700" 
        />
        <div className="text-black font-sans font-black text-[8px] mt-2 uppercase tracking-tighter text-center line-clamp-1">
          {formatName(item.name)}
        </div>
      </div>
    </div>
  )

  if (currentItem) {
    return (
      <div className="min-h-screen bg-white text-black flex flex-col lg:flex-row overflow-hidden">
        {/* Detail View UI (Toggleable Sidebar) */}
        <div className="lg:flex-1 flex flex-col relative h-screen">
          <nav className="absolute top-8 left-8 right-8 z-50 flex justify-between items-center pointer-events-none">
            <button onClick={() => router.push("/")} className="pointer-events-auto bg-white/80 backdrop-blur px-4 py-2 rounded-full font-mono font-black uppercase text-[10px] tracking-widest border border-black/5 hover:bg-black hover:text-white transition-all">
              &larr; Lukk
            </button>
            <div className="flex gap-2 pointer-events-auto bg-gray-100/80 backdrop-blur p-1 rounded-full">
              <button onClick={() => setViewMode('2d')} className={`px-4 py-1 rounded-full text-[9px] font-mono font-black uppercase transition-all ${viewMode === '2d' ? 'bg-black text-white' : 'text-gray-400'}`}>2D</button>
              <button onClick={() => setViewMode('3d')} className={`px-4 py-1 rounded-full text-[9px] font-mono font-black uppercase transition-all ${viewMode === '3d' ? 'bg-black text-white' : 'text-gray-400'}`}>3D</button>
            </div>
          </nav>

          <div className="flex-1 flex items-center justify-center bg-white">
            <div className="w-full aspect-square max-w-[85vh]">
              {viewMode === '3d' ? (
                <ModelViewer chairId={currentItem.id} />
              ) : (
                <div className="w-full h-full flex items-center justify-center p-12">
                  <img src={`/bg-uniform black/${currentItem.id}.png`} className="max-w-full max-h-full object-contain" />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Info Sidebar */}
        {isSidebarOpen && (
          <aside className="lg:w-[450px] border-l border-gray-100 bg-gray-50 p-8 lg:p-16 overflow-y-auto h-screen relative">
            <button onClick={() => setIsSidebarOpen(false)} className="hidden lg:block absolute top-8 right-8 text-gray-300 hover:text-black transition-colors">
              <X size={20} />
            </button>
            <div className="space-y-12">
              <section>
                <div className="font-mono text-[10px] text-gray-400 uppercase tracking-widest mb-4">{currentItem.id}</div>
                <h1 className="text-4xl font-sans font-black tracking-tighter uppercase leading-none">{formatName(currentItem.name)}</h1>
                <p className="font-mono text-gray-400 text-xs font-bold uppercase tracking-widest mt-4">{currentItem.year}</p>
              </section>
              <div className="grid grid-cols-1 gap-y-8 border-t border-gray-100 pt-12">
                {[
                  { label: "Material", val: currentItem.materials },
                  { label: "Teknikk", val: currentItem.techniques },
                  { label: "Produsent", val: currentItem.producer },
                  { label: "Stad", val: currentItem.location }
                ].map(f => f.val && (
                  <div key={f.label}>
                    <h3 className="font-mono font-black text-[9px] uppercase tracking-[0.2em] text-gray-300 mb-2">{f.label}</h3>
                    <p className="text-sm font-bold text-black">{f.val}</p>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-black font-sans selection:bg-black selection:text-white">
      {/* Header & Search */}
      <header className="fixed top-0 left-0 right-0 bg-white/90 backdrop-blur-md z-50 border-b border-black/5 px-6 md:px-12 py-6 flex flex-col md:flex-row justify-between items-center gap-6">
        <h1 className="font-sans font-black text-2xl tracking-tighter uppercase italic">Stolar.</h1>
        <div className="flex items-center gap-4 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-300" size={14} />
            <input 
              type="text" 
              placeholder="Søk i samlinga..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-50 border-none rounded-full py-2 pl-10 pr-4 text-xs font-mono focus:ring-1 focus:ring-black outline-none transition-all"
            />
          </div>
          <div className="flex gap-2">
            {[ "I", "II", "III", "IV", "V" ].map((n, i) => (
              <button 
                key={n}
                onClick={() => router.push(i === 0 ? "/article" : i === 1 ? "/article/form" : i === 2 ? "/article/form-klassifikasjon" : i === 3 ? "/article/fff-rammeverk" : "/article/kappe")}
                className="w-8 h-8 rounded-full border border-black/5 flex items-center justify-center font-mono font-black text-[10px] hover:bg-black hover:text-white transition-all"
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="max-w-[1800px] mx-auto px-6 md:px-12 pt-40 pb-40">
        {/* Filters */}
        <div className="flex overflow-x-auto gap-4 mb-16 no-scrollbar pb-4 border-b border-black/5">
          {materials.map(m => (
            <button 
              key={m}
              onClick={() => setSelectedMaterial(m)}
              className={`whitespace-nowrap px-4 py-1.5 rounded-full font-mono text-[9px] font-black uppercase tracking-widest transition-all ${selectedMaterial === m ? 'bg-black text-white' : 'bg-gray-100 text-gray-400 hover:text-black'}`}
            >
              {m}
            </button>
          ))}
        </div>

        <div className="space-y-32">
          {Object.entries(groupedChairs).sort(([a], [b]) => a.localeCompare(b)).map(([century, chairs]) => (
            <section key={century}>
              <div className="flex items-baseline justify-between border-b border-black/10 pb-4 mb-8">
                <h2 className="font-mono font-black text-3xl tracking-tighter">{century}</h2>
                <span className="font-mono text-xs font-bold text-gray-300 uppercase tracking-widest">{chairs.length} stolar</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 border-t border-l border-black/10">
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
