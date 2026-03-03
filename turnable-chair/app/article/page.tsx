"use client"

import { useState, useEffect, useMemo, useRef } from "react"
import { useRouter } from "next/navigation"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Legend
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
      .catch((err) => console.error("Feil ved lasting av data:", err))
  }, [])

  const geoData = useMemo(() => {
    const counts: Record<string, number> = {}
    data.forEach((item) => {
      const loc = String(item.location || "Ukjent").split(",")[0].trim()
      counts[loc] = (counts[loc] || 0) + 1
    })
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)
  }, [data])

  const materialTimeline = useMemo(() => {
    const decades: Record<string, Record<string, number>> = {}
    const keyMaterials = ["mahogni", "furu", "eik", "bjørk", "stål", "plast"]
    
    data.forEach((item) => {
      const yearStr = item.year.match(/\d{4}/)?.[0]
      if (yearStr) {
        const decade = Math.floor(parseInt(yearStr) / 25) * 25
        const decadeStr = `${decade}`
        
        if (!decades[decadeStr]) {
          decades[decadeStr] = { mahogni: 0, furu: 0, eik: 0, bjørk: 0, stål: 0, plast: 0, total: 0 }
        }
        
        decades[decadeStr].total++
        const matStr = (item.materials || "").toLowerCase()
        keyMaterials.forEach((m) => {
          if (matStr.includes(m)) {
            decades[decadeStr][m]++
          }
        })
      }
    })
    
    return Object.entries(decades)
      .map(([name, values]) => {
        const result: any = { name }
        Object.keys(values).forEach(k => {
          if (k !== 'total') {
            result[k] = Math.round((values[k] / values.total) * 100)
          }
        })
        return result
      })
      .sort((a, b) => parseInt(a.name) - parseInt(b.name))
  }, [data])

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center font-sans">
        <div className="text-xl animate-pulse text-gray-400 font-mono tracking-tighter">Lastar kvantitative data...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-32 overflow-x-hidden">
      {/* Navigasjon */}
      <nav className="fixed top-0 left-0 right-0 bg-white/90 backdrop-blur-md border-b border-gray-100 z-50 px-6 py-4 flex justify-between items-center">
        <button
          onClick={() => router.push('/')}
          className="flex items-center text-[10px] font-mono font-bold uppercase tracking-widest text-gray-400 hover:text-black transition-colors"
        >
          <svg className="w-3 h-3 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Gå til databasen
        </button>
        <div className="text-[10px] font-mono font-bold text-black tracking-[0.2em] uppercase">
          Materialhistorie 1280–2020
        </div>
      </nav>

      {/* Artikkel-header */}
      <header className="max-w-4xl mx-auto pt-48 pb-24 px-6 md:px-12">
        <p className="text-[10px] font-mono font-bold uppercase tracking-[0.4em] text-gray-300 mb-8">Forskingsartikkel</p>
        <h1 className="text-5xl md:text-8xl font-sans font-bold tracking-tighter leading-[0.9] mb-12">
          Materialhistorie i Nasjonalmuseet si stolsamling <br/>
          <span className="text-gray-300">Materialkurver som kolonialt arkiv</span>
        </h1>
        
        <div className="flex flex-col md:flex-row gap-16 border-y border-gray-100 py-12 my-12">
          <div className="flex-1">
            <p className="text-[10px] font-mono font-bold uppercase tracking-widest text-gray-400 mb-4">Forfattar</p>
            <p className="text-2xl font-sans font-bold tracking-tight leading-none">Iver Raknes Finne</p>
            <p className="text-sm text-gray-500 font-sans mt-2 leading-relaxed">
              Institutt for design, Arkitektur- og designhøgskolen i Oslo (AHO)
            </p>
          </div>
          <div className="flex-1">
            <p className="text-[10px] font-mono font-bold uppercase tracking-widest text-gray-400 mb-4">Metode</p>
            <p className="text-2xl font-sans font-bold tracking-tight leading-none font-mono">Materialkurveanalyse</p>
            <p className="text-sm text-gray-500 font-sans mt-2 leading-relaxed">
              Systematisk kvantifisering av {data.length} objekt daterte frå 1280 til 2020.
            </p>
          </div>
        </div>

        <div className="bg-gray-50 p-10 rounded-3xl border border-gray-100 italic text-xl leading-relaxed text-gray-800 font-serif">
          <strong>Samandrag:</strong> Artikkelen presenterer den fyrste systematiske kvantitative materialanalysen av Nasjonalmuseet si stolsamling. Gjennom eit nytt strukturert datasett undersøkjer studien korleis materialkurver fungerer som eit kolonialt arkiv. Hovudfunnet er <em>mahogniens boge</em>: ein materiell signatur der karibisk tropisk hardved stig dramatisk for deretter å kollapse, nesten synkront med den transatlantiske mahognihandelen.
        </div>
      </header>

      {/* Hovudtekst */}
      <article className="max-w-3xl mx-auto px-6 md:px-12 space-y-16 text-xl leading-relaxed text-gray-900">
        <section>
          <h2 className="text-4xl font-sans font-bold text-black mb-8 tracking-tight">Innleiing</h2>
          <p className="mb-8">
            I magasinet til Nasjonalmuseet i Oslo står det ein stol registrert som <strong>OK-10330A</strong>, datert til om lag 1830. Materiallista er kort: mahogni, hestetagl, furu, eik, whitewood. For ein konvensjonell designhistorikar er dette ein anonym empirestol. Men materiallista er ikkje anonym. Ho er eit komprimert verdskart.
          </p>
          <p>
            Mahognien kjem frå tropiske regnskogar i Karibia, felt av tvangsarbeidande menneske under det britiske kolonistyret. Hestetaglet knyter stolen til europeiske leverandørkjeder. Furu og eik er norske. Fem materialar frå minst tre kontinent, samla i éin norsk stol. Museumsmagasinet kan lesast som eit materialkurvediagram der kvar kurve representerer eit materiale si stiging og fall over tid.
          </p>
        </section>

        {/* Interaktiv Graf: Produksjonsgeografi */}
        <section className="py-12 full-bleed md:-mx-12">
          <div className="bg-white p-8 md:p-12 rounded-[2.5rem] border border-gray-100 shadow-sm overflow-hidden">
            <h4 className="text-[10px] font-mono font-bold uppercase tracking-[0.3em] text-gray-400 mb-10 text-center">FIGUR 1: Geografisk fordeling av produksjon (topp 10 klynger)</h4>
            <div className="h-[500px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={geoData} layout="vertical" margin={{ left: 20, right: 40 }}>
                  <CartesianGrid strokeDasharray="2 2" horizontal={false} stroke="#f5f5f5" />
                  <XAxis type="number" hide />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    width={140} 
                    tick={{ fontSize: 11, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace', fontWeight: 'bold', fill: '#000' }} 
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip 
                    cursor={{ fill: '#f9f9f9' }}
                    contentStyle={{ borderRadius: '12px', border: '1px solid #eee', boxShadow: '0 10px 30px rgba(0,0,0,0.05)', fontFamily: 'ui-monospace, monospace', fontSize: '12px' }}
                  />
                  <Bar dataKey="value" fill="#000" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-8 text-sm text-gray-500 font-sans text-center px-12 italic leading-relaxed">
              Analysen viser ei kraftig geografisk klynging i Sunnmøre og Oslo-regionen, noko som reflekterer Noreg si industrielle møbelhistorie.
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-4xl font-sans font-bold text-black mb-8 tracking-tight">Mahogni som kolonialhistorisk objekt</h2>
          <p className="mb-8">
            Naval Stores Act frå 1721 var den utløysande faktoren for mahogni sin dominans i europeisk møbelhandverk. Lova fjerna importtoll på tømmer frå britiske koloniar i Amerika. Noreg mottok mahogni som ein sekundærmarknad gjennom britisk reeksport.
          </p>
          <p>
            Hovudfunnet i denne studien er <strong>mahogniens boge</strong>. Mahogni er fråverande før 1700, stig dramatisk til ein topp på 86 % av alle registrerte stolar i perioden 1825–1849, for deretter å kollapse. Denne kurva er ein materiell biografi om den transatlantiske slaveriøkonomien innbygd i eit norsk museumsmagasin.
          </p>
        </section>

        {/* Interaktiv Graf: MaterialTimeline */}
        <section className="py-12 full-bleed md:-mx-12">
          <div className="bg-black p-8 md:p-16 rounded-[3rem] shadow-2xl relative">
            <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:20px_20px]" />
            <h4 className="text-[10px] font-mono font-bold uppercase tracking-[0.5em] text-gray-500 mb-12 text-center">FIGUR 2: Materialkurver (Temporal analyse i %)</h4>
            <div className="h-[550px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={materialTimeline} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#222" />
                  <XAxis dataKey="name" stroke="#444" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666' }} />
                  <YAxis stroke="#444" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666' }} unit="%" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', color: '#fff', borderRadius: '8px', fontFamily: 'ui-monospace, monospace', fontSize: '12px' }}
                  />
                  <Legend verticalAlign="top" height={50} iconType="circle" wrapperStyle={{ paddingBottom: '30px', fontFamily: 'ui-monospace, monospace', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.1em' }} />
                  <Area type="monotone" dataKey="mahogni" stackId="1" stroke="#fff" fill="#fff" fillOpacity={0.9} />
                  <Area type="monotone" dataKey="furu" stackId="1" stroke="#888" fill="#444" fillOpacity={0.8} />
                  <Area type="monotone" dataKey="stål" stackId="1" stroke="#666" fill="#222" fillOpacity={0.7} />
                  <Area type="monotone" dataKey="plast" stackId="1" stroke="#444" fill="#111" fillOpacity={0.6} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-4xl font-sans font-bold text-black mb-8 tracking-tight">Norsk materiell dobbeltheit</h2>
          <p className="mb-8">
            Når materialkurvene for norskproduserte stolar vert analyserte separat, framtrer eit distinkt mønster: ein systematisk hybriditet. Norske stolmakarar adopterte koloniale materialar som statusmarkørar på overflata, men opprettheldt lokale materialar som furu og bjørk i den berande strukturen.
          </p>
          <p>
            Dette fenomenet, som eg kallar <strong>materiell dobbeltheit</strong>, gjer den norske stolen til eit kompromissposisjon mellom global prestisje og lokal ressursbruk. Stolen er kolonialt finert: eit lokalt møbel med ein importert estetisk hud.
          </p>
        </section>

        <section className="border-t border-gray-100 pt-16">
          <h2 className="text-4xl font-sans font-bold text-black mb-8 tracking-tight">Konklusjon</h2>
          <div className="space-y-8 text-gray-600 italic font-serif">
            <p>
              Materialkurveanalyse gjer designobjekt lesbare som geopolitisk historie. Nasjonalmuseet sitt magasin fungerer som eit kolonialt arkiv der kvar stol ber vitne om globale materialkrinslop.
            </p>
            <p>
              Avstanden mellom ein gárastol frå 1280 og ein empirestol frå 1830 er avstanden mellom ein lokal og ein global materialøkonomi. Å kvantifisere denne avstanden er ei naudsynt oppgåve for designhistoria.
            </p>
          </div>
        </section>
      </article>

      {/* Referansar */}
      <footer className="max-w-3xl mx-auto py-24 px-6 md:px-12 border-t border-gray-100 mt-24">
        <p className="text-[10px] font-mono font-bold uppercase tracking-[0.4em] text-gray-400 mb-10">Utvalde referansar</p>
        <div className="space-y-6 text-sm font-sans text-gray-500 leading-relaxed">
          <p>Anderson, J. L. (2012). <em>Mahogany: The costs of luxury in early America</em>. Harvard University Press.</p>
          <p>Bowett, A. (2012). <em>Woods in British furniture-making 1400–1900</em>. Oblong.</p>
          <p>Ingold, T. (2007). Materials against materiality. <em>Archaeological Dialogues</em>, 14(1), 1–16.</p>
          <p>Moretti, F. (2005). <em>Graphs, Maps, Trees: Abstract Models for Literary History</em>. Verso.</p>
        </div>
        <div className="mt-20 pt-12 border-t border-gray-50 text-center">
           <p className="text-[9px] font-mono font-bold text-gray-300 uppercase tracking-widest">&copy; 2026 Iver Raknes Finne &bull; AHO</p>
        </div>
      </footer>
    </div>
  )
}
