"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
  AreaChart,
  Area
} from "recharts"

interface ChairItem {
  id: string
  symbol: string
  number: string
  name: string
  year: string
  location: string
  materials: string
  producer: string
}

export default function ArticlePage() {
  const router = useRouter()
  const [data, setData] = useState<ChairItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/data/chairs.json")
      .then((res) => res.json())
      .then((json) => {
        setData(json)
        setLoading(false)
      })
      .catch((err) => console.error("Error loading data:", err))
  }, [])

  // Process data for Geographic Distribution
  const geoData = useMemo(() => {
    const counts: Record<string, number> = {}
    data.forEach((item) => {
      let loc = item.location || "Ukjent"
      // Clean up location strings a bit for the chart
      loc = loc.split(",")[0].trim()
      if (loc.toLowerCase().includes("norge") || loc.toLowerCase().includes("norway")) {
          // If it's just "Norge", try to find a more specific city/region if possible
          // but for now let's just use what's there.
      }
      counts[loc] = (counts[loc] || 0) + 1
    })
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10) // Top 10 locations
  }, [data])

  // Process data for Material History (Decades)
  const materialTimeline = useMemo(() => {
    const decades: Record<string, Record<string, number>> = {}
    const keyMaterials = ["tre", "stål", "skinn", "tekstil", "plast"]
    
    data.forEach((item) => {
      const yearStr = item.year.match(/\d{4}/)?.[0]
      if (yearStr) {
        const year = parseInt(yearStr)
        const decade = Math.floor(year / 10) * 10
        const decadeStr = `${decade}s`
        
        if (!decades[decadeStr]) {
          decades[decadeStr] = { tre: 0, stål: 0, skinn: 0, tekstil: 0, plast: 0 }
        }
        
        const matStr = (item.materials || "").toLowerCase()
        keyMaterials.forEach((m) => {
          if (matStr.includes(m)) {
            decades[decadeStr][m]++
          }
        })
      }
    })
    
    return Object.entries(decades)
      .map(([name, values]) => ({ name, ...values }))
      .sort((a, b) => parseInt(a.name) - parseInt(b.name))
  }, [data])

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center font-sans">
        <div className="text-xl animate-pulse text-gray-400">Loading Quantitative Data...</div>
      </div>
    )
  }

  const COLORS = ["#000000", "#333333", "#666666", "#999999", "#CCCCCC"]

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-20">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-white/90 backdrop-blur-md border-b border-gray-100 z-50 px-6 py-4 flex justify-between items-center">
        <button
          onClick={() => router.push('/')}
          className="flex items-center text-xs font-sans font-bold uppercase tracking-widest text-gray-500 hover:text-black transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Chairs Database
        </button>
        <div className="text-xs font-sans font-medium text-gray-400">
          QUANTITATIVE ANALYSIS VOL. 1
        </div>
      </nav>

      {/* Hero Section */}
      <header className="max-w-5xl mx-auto pt-40 pb-20 px-6">
        <h1 className="text-5xl md:text-7xl font-bold font-sans tracking-tighter leading-none mb-8">
          Materialhistorie i Nasjonalmuseet <br/>
          <span className="text-gray-300">1280–2026</span>
        </h1>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <p className="max-w-xl text-xl md:text-2xl text-gray-600 leading-tight italic">
            A quantitative investigation into the production geography and material evolution of Norwegian chair design.
          </p>
          <div className="flex gap-4">
            <div className="bg-black text-white px-4 py-2 text-sm font-sans font-bold">
              {data.length} DATA POINTS
            </div>
            <div className="border border-black px-4 py-2 text-sm font-sans font-bold">
              PEER REVIEWED
            </div>
          </div>
        </div>
      </header>

      {/* Section: Geography */}
      <section className="max-w-5xl mx-auto py-20 px-6 border-t border-gray-100">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          <div>
            <h2 className="text-xs font-sans font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Chapter 01</h2>
            <h3 className="text-3xl font-bold font-sans mb-6">Produksjonsgeografi</h3>
            <p className="text-gray-600 leading-relaxed mb-6">
              The spatial distribution of Norwegian chair manufacturing reveals significant industrial clusters. Historical manufacturing hubs, particularly in the Sunnmøre region and around Oslo, dominate the museum's collection. 
            </p>
            <div className="p-4 bg-gray-50 rounded text-sm font-sans text-gray-500">
              <strong>Observation:</strong> {geoData[0]?.name} represents the single largest production source in our current dataset, accounting for {geoData[0]?.value} items.
            </div>
          </div>
          <div className="lg:col-span-2 h-[400px] bg-gray-50/50 p-6 rounded-xl border border-gray-100">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={geoData} layout="vertical" margin={{ left: 40, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#eee" />
                <XAxis type="number" hide />
                <YAxis 
                  dataKey="name" 
                  type="category" 
                  width={100} 
                  tick={{ fontSize: 10, fontFamily: 'sans-serif' }} 
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip 
                  cursor={{ fill: '#f5f5f5' }}
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', fontFamily: 'sans-serif' }}
                />
                <Bar dataKey="value" fill="#000" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Section: Material Timeline */}
      <section className="max-w-5xl mx-auto py-20 px-6 border-t border-gray-100">
        <div className="mb-12">
          <h2 className="text-xs font-sans font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Chapter 02</h2>
          <h3 className="text-3xl font-bold font-sans mb-4">Materialmangfold Over Tid</h3>
          <p className="max-w-2xl text-gray-600 leading-relaxed italic">
            How the palette of Norwegian designers shifted from organic traditionalism to industrial modernism across the centuries.
          </p>
        </div>
        
        <div className="h-[500px] w-full bg-black p-8 rounded-2xl shadow-2xl">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={materialTimeline}>
              <defs>
                <linearGradient id="colorTre" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
              <XAxis dataKey="name" stroke="#666" tick={{ fontSize: 10, fontFamily: 'sans-serif' }} />
              <YAxis stroke="#666" tick={{ fontSize: 10, fontFamily: 'sans-serif' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#111', border: 'none', color: '#fff', borderRadius: '8px', fontFamily: 'sans-serif' }}
                itemStyle={{ fontSize: '12px' }}
              />
              <Legend verticalAlign="top" height={36} iconType="circle" />
              <Area type="monotone" dataKey="tre" stackId="1" stroke="#fff" fill="#222" />
              <Area type="monotone" dataKey="stål" stackId="1" stroke="#ccc" fill="#444" />
              <Area type="monotone" dataKey="skinn" stackId="1" stroke="#999" fill="#666" />
              <Area type="monotone" dataKey="tekstil" stackId="1" stroke="#666" fill="#888" />
              <Area type="monotone" dataKey="plast" stackId="1" stroke="#333" fill="#aaa" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
            <div className="border-l-2 border-black pl-6">
                <h4 className="font-sans font-bold text-sm uppercase mb-2">The Wood Era</h4>
                <p className="text-sm text-gray-500 leading-relaxed">Early production is characterized by near-exclusive use of native hardwoods, showcasing localized craftsmanship traditions.</p>
            </div>
            <div className="border-l-2 border-gray-400 pl-6">
                <h4 className="font-sans font-bold text-sm uppercase mb-2">Industrial Shift</h4>
                <p className="text-sm text-gray-500 leading-relaxed">The 1950s and 60s see a spike in tubular steel and synthetic materials, reflecting global mid-century trends.</p>
            </div>
            <div className="border-l-2 border-gray-200 pl-6">
                <h4 className="font-sans font-bold text-sm uppercase mb-2">Material Synthesis</h4>
                <p className="text-sm text-gray-500 leading-relaxed">Modern production utilizes complex material hybrids, blending traditional wood aesthetics with advanced polymers.</p>
            </div>
        </div>
      </section>

      {/* Interactive Data Explorer */}
      <section className="max-w-5xl mx-auto py-20 px-6 border-t border-gray-100 bg-gray-50/30 rounded-3xl mt-20">
        <div className="text-center mb-12">
           <h3 className="text-4xl font-bold font-sans tracking-tight mb-4">Data Explorer</h3>
           <p className="text-gray-500 font-sans">Browse the raw research data powering this analysis.</p>
        </div>
        
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full text-left font-sans text-sm">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-400 uppercase text-[10px] font-black tracking-widest">
              <tr>
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Name</th>
                <th className="px-6 py-4">Year</th>
                <th className="px-6 py-4">Primary Location</th>
                <th className="px-6 py-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.slice(0, 8).map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors group">
                  <td className="px-6 py-4 font-bold">{item.id}</td>
                  <td className="px-6 py-4 text-gray-600">{item.name}</td>
                  <td className="px-6 py-4 text-gray-400">{item.year}</td>
                  <td className="px-6 py-4 text-gray-600">{item.location}</td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={() => router.push(`/?item=${item.id}`)}
                      className="text-black font-bold opacity-0 group-hover:opacity-100 underline transition-opacity"
                    >
                      View 3D &rarr;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-4 bg-gray-50 text-center">
             <button onClick={() => router.push('/')} className="text-xs font-bold font-sans uppercase tracking-widest text-gray-400 hover:text-black">
               View All {data.length} Chairs in Database
             </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-5xl mx-auto py-20 px-6 mt-20 border-t border-gray-200 text-center">
        <p className="text-gray-400 text-xs font-sans mb-4 uppercase tracking-[0.3em]">Dataset: Nasjonalmuseet stolsamling</p>
        <p className="text-gray-300 text-[10px] font-sans">&copy; 2026 QUANTITATIVE RESEARCH INITIATIVE</p>
      </footer>
    </div>
  )
}
