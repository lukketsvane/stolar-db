"use client"

import { useState, useEffect } from "react"
import ArticleLayout from "../../components/article-layout"
import Content from "./content/artikkel_1.mdx"

interface ChairItem {
  id: string
  year: string
  materials: string
  location: string
}

export default function ArticleOnePage() {
  const [data, setData] = useState<ChairItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/data/chairs.json")
      .then((res) => res.json())
      .then((json) => {
        setData(json)
        setLoading(false)
      })
      .catch((err) => console.error("Feil ved lasting av data:", err))
  }, [])

  if (loading) {
    return <div className="min-h-screen bg-white flex items-center justify-center font-mono text-xs uppercase tracking-widest text-gray-400">Lastar historikk...</div>
  }

  const header = (
    <div className="w-full">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel I</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Materialhistorie.<br/>
        <span className="text-gray-200">Kolonialt arkiv.</span>
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16 font-sans">
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">
            Institutt for design, Arkitektur- og designhøgskolen i Oslo (AHO)
          </p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Materialkurveanalyse</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed">
            Systematisk kvantifisering av materialfordeling over tid i samlinga.
          </p>
        </div>
      </div>

      <div className="mt-16 py-8 border-t border-black">
        <p className="text-xl font-serif italic leading-relaxed text-black">
          <strong>Samandrag:</strong> Artikkelen presenterer den fyrste systematiske kvantitative materialanalysen av Nasjonalmuseet si stolsamling (n = 461), som spenner frå 1280 til 2020. Gjennom eit nytt strukturert datasett undersøkjer studien korleis materialkurver fungerer som eit kolonialt arkiv. Hovudfunnet er <em>mahogniens boge</em>: ein materiell signatur der karibisk tropisk hardved stig frå null til 86 % av alle registrerte stolar i perioden 1825–1849, for deretter å kollapse.
        </p>
      </div>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <Content />
      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Anderson, J. L. (2012). <em className="normal-case">Mahogany: The Costs of Luxury in Early America.</em> Harvard University Press.</p>
          <p>Appadurai, A. (1986). <em className="normal-case">The Social Life of Things.</em> Cambridge University Press.</p>
          <p>Bennett, J. (2010). <em className="normal-case">Vibrant Matter.</em> Duke University Press.</p>
          <p>Bowett, A. (2012). <em className="normal-case">Woods in British Furniture-Making 1400-1900.</em> Oblong.</p>
          <p>Ingold, T. (2007). Materials against materiality. <em className="normal-case">Archaeological Dialogues,</em> 14(1), 1-16.</p>
          <p>Manovich, L. (2020). <em className="normal-case">Cultural Analytics.</em> MIT Press.</p>
          <p>Moretti, F. (2005). <em className="normal-case">Graphs, Maps, Trees.</em> Verso.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
