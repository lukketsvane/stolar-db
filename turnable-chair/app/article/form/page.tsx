"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import ArticleLayout from "../../../components/article-layout"
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Legend,
  LineChart,
  Line,
  BarChart,
  Bar,
  Cell,
} from "recharts"

interface StolItem {
  object_id: string
  title: string
  betegnelse: string
  fra_aar: number | null
  hoegde_cm: number | null
  breidde_cm: number | null
  djupn_cm: number | null
  teknikk: string
}

const PERIOD_SIZE = 50

function getPeriod(year: number): string {
  return `${Math.floor(year / PERIOD_SIZE) * PERIOD_SIZE}`
}

export default function FormArticlePage() {
  const router = useRouter()
  const [data, setData] = useState<StolItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/data/norske_stolar.json")
      .then((res) => res.json())
      .then((json) => {
        setData(json)
        setLoading(false)
      })
      .catch((err) => console.error("Feil ved lasting av data:", err))
  }, [])

  const withDims = useMemo(() => data.filter(d => d.fra_aar && d.hoegde_cm && d.breidde_cm && d.djupn_cm), [data])
  const volumeScatter = useMemo(() => withDims.map(d => ({ year: d.fra_aar!, volume: Math.round((d.hoegde_cm! * d.breidde_cm! * d.djupn_cm!) / 1000) })), [withDims])

  if (loading) return <div className="min-h-screen bg-white flex items-center justify-center font-mono text-xs uppercase tracking-widest text-gray-400">Lastar formdata...</div>

  const header = (
    <div className="max-w-4xl">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel II</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Form follows<br/>
        <span className="text-gray-200">fitness.</span>
      </h1>
      <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight mt-8">
        Mot ein evolusjonær formteori for stolen.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16 font-sans">
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">AHO</p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Formkurveanalyse</p>
        </div>
      </div>

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> Artikkelen introduserer <em>form follows fitness</em> som eit evolusjonært rammeverk for å analysere formutvikling i industridesign.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing: Problemet med &laquo;form follows function&raquo;</h2>
        <p>
          I 1896 skreiv Louis Sullivan at &laquo;form ever follows function&raquo;. Setninga vart eit aksiom. Le Corbusier radikaliserte ho i 1923: huset er <em>une machine à habiter</em>. Maskinen har ingen overflødig form; kvar detalj tener ein funksjon.
        </p>
        <p>
          Problemet er empirisk. Dersom form følger funksjon, burde alle stolar med same funksjon ha same form. Det har dei ikkje.
        </p>
      </section>

      <section className="not-prose my-32">
        <div className="bg-black p-8 md:p-12 lg:p-16 rounded-3xl shadow-2xl">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.6em] text-gray-600 mb-20 text-center">FIGUR 1: Omsluttande volum over tid</h4>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ left: 20, right: 40, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#222" />
                <XAxis dataKey="year" type="number" domain={[1200, 2020]} stroke="#444" tick={{ fontSize: 10 }} />
                <YAxis dataKey="volume" type="number" stroke="#444" tick={{ fontSize: 10 }} unit=" L" />
                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333', color: '#fff' }} />
                <Scatter data={volumeScatter} fill="#fff" fillOpacity={0.8} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section>
        <h2>2. Fitness-konvergensen</h2>
        <p>
          Figur 1 er det sentrale funnet i denne studien. Omsluttande volum viser ein tydeleg <strong>konvergens</strong> over tid.
        </p>
      </section>

      <footer className="mt-32 pt-16 border-t border-gray-100 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
        <p>&copy; 2026 Iver Raknes Finne</p>
        <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
      </footer>
    </ArticleLayout>
  )
}
