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
      <div className="min-h-screen bg-white flex items-center justify-center font-mono text-[10px] uppercase tracking-widest text-gray-400">
        Lastar kvantitative data...
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      {/* Navigasjon */}
      <nav className="fixed top-0 left-0 right-0 bg-white/90 backdrop-blur-md border-b border-gray-100 z-50 px-8 py-6 flex justify-between items-center">
        <button
          onClick={() => router.push('/')}
          className="flex items-center text-[10px] font-mono font-black uppercase tracking-widest text-black hover:line-through transition-all"
        >
          ← Stol-database
        </button>
        <div className="text-[10px] font-mono font-black text-black tracking-[0.3em] uppercase">
          Materialhistorie 1280–2020
        </div>
      </nav>

      {/* Artikkel-header */}
      <header className="max-w-5xl mx-auto pt-48 pb-32 px-8">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel</p>
        <h1 className="text-6xl md:text-[10rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Materialhistorie.<br/>
          <span className="text-gray-200">Kolonialt arkiv.</span>
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16">
          <div>
            <p className="text-[10px] font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed max-w-xs">
              Institutt for design, Arkitektur- og designhøgskolen i Oslo (AHO)
            </p>
          </div>
          <div>
            <p className="text-[10px] font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Materialkurveanalyse</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Systematisk kvantifisering av materialfordeling over tid i Nasjonalmuseet si samling.
            </p>
          </div>
        </div>

        <div className="max-w-3xl bg-gray-50 p-12 lg:p-20 rounded-[3rem] border border-gray-100 italic text-2xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> Artikkelen presenterer den fyrste systematiske kvantitative materialanalysen av Nasjonalmuseet si stolsamling. Gjennom eit nytt strukturert datasett undersøkjer studien korleis materialkurver fungerer som eit kolonialt arkiv. Hovudfunnet er <em>mahogniens boge</em>: ein materiell signatur der karibisk tropisk hardved stig dramatisk for deretter å kollapse, nesten synkront med den transatlantiske mahognihandelen.
        </div>
      </header>

      {/* Artikkel-tekst */}
      <article className="max-w-3xl mx-auto px-8 space-y-24 text-2xl leading-relaxed text-gray-900">
        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">1. Innleiing</h2>
          <p className="mb-12">
            I magasinet til Nasjonalmuseet i Oslo står det ein stol registrert som <strong className="font-mono text-xl">OK-10330A</strong>, datert til om lag 1830. Materiallista er kort: mahogni, hestetagl, furu, eik, whitewood. For ein konvensjonell designhistorikar er dette ein anonym empirestol. Men materiallista er ikkje anonym. Ho er eit komprimert verdskart.
          </p>
          <p>
            Mahognien kjem frå tropiske regnskogar i Karibia, felt av tvangsarbeidande menneske under det britiske kolonistyret. Furu og eik er norske. Fem materialar frå minst tre kontinent, samla i éin norsk stol. Museumsmagasinet kan lesast som eit materialkurvediagram der kvar kurve representerer eit materiale si stiging og fall over tid.
          </p>
        </section>

        {/* Figur 1: Geografi */}
        <section className="py-12 full-bleed">
          <div className="bg-white p-12 lg:p-24 rounded-[4rem] border border-gray-100 shadow-sm overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 1: Geografisk fordeling av produksjon</h4>
            <div className="h-[600px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={geoData} layout="vertical" margin={{ left: 20, right: 40 }}>
                  <CartesianGrid strokeDasharray="2 2" horizontal={false} stroke="#f0f0f0" />
                  <XAxis type="number" hide />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    width={160} 
                    tick={{ fontSize: 12, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} 
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip 
                    cursor={{ fill: '#fafafa' }}
                    contentStyle={{ borderRadius: '0px', border: '1px solid #000', boxShadow: 'none', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                  />
                  <Bar dataKey="value" fill="#000" radius={0} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-400 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Analysen viser ei kraftig klynging i Sunnmøre og Oslo-regionen.
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">2. Mahogniens boge</h2>
          <p className="mb-12">
            Hovudfunnet i denne studien er <strong>mahogniens boge</strong>. Mahogni er fråverande før 1700, stig dramatisk til ein topp på 86 % av alle registrerte stolar i perioden 1825–1849, for deretter å kollapse. Denne kurva er ein materiell biografi om den transatlantiske slaveriøkonomien.
          </p>
          <p>
            Den norske kurva følgjer den britiske med ei forsinking på om lag 25–50 år, og plasserer Nasjonalmuseet sitt magasin som ein perifer node i eit globalt handelsnettverk som knyter jamaicanske regnskogar og norske snekkarverkstader saman.
          </p>
        </section>

        {/* Figur 2: Temporal analyse */}
        <section className="py-12 full-bleed">
          <div className="bg-black p-12 lg:p-24 rounded-[4rem] shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#333_1px,transparent_1px)] [background-size:30px_30px]" />
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.6em] text-gray-600 mb-20 text-center">FIGUR 2: Materialkurver 1280–2020 (%)</h4>
            <div className="h-[600px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={materialTimeline}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#222" />
                  <XAxis dataKey="name" stroke="#444" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666', fontWeight: '900' }} />
                  <YAxis stroke="#444" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666', fontWeight: '900' }} unit="%" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', color: '#fff', borderRadius: '0px', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                  />
                  <Legend verticalAlign="top" height={60} iconType="square" wrapperStyle={{ paddingBottom: '40px', fontFamily: 'ui-monospace, monospace', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: '900' }} />
                  <Area type="stepAfter" dataKey="mahogni" stackId="1" stroke="#fff" fill="#fff" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="furu" stackId="1" stroke="#888" fill="#444" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="stål" stackId="1" stroke="#666" fill="#222" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="plast" stackId="1" stroke="#444" fill="#111" fillOpacity={1} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">3. Materiell dobbeltheit</h2>
          <p className="mb-12">
            Norskproduserte stolar opprettheld ein <strong>materiell dobbeltheit</strong>. Importert mahogni fungerer som overflate, medan lokal furu og bjørk utgjer den berande strukturen.
          </p>
          <p>
            Stolen er kolonialt finert: ein materiell strategi der globalt prestisjetømmer og lokal handverkstradisjon sameksisterer i same objekt. Denne hybriditeten reflekterer både økonomiske realitetar og ein spesifikt norsk materialposisjon.
          </p>
        </section>

        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
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
      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Anderson, J. L. (2012). Mahogany: The costs of luxury in early America. Harvard University Press.</p>
          <p>Bowett, A. (2012). Woods in British furniture-making 1400–1900. Oblong.</p>
          <p>Ingold, T. (2007). Materials against materiality. Archaeological Dialogues, 14(1), 1–16.</p>
          <p>Moretti, F. (2005). Graphs, Maps, Trees: Abstract Models for Literary History. Verso.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
           <p>&copy; 2026 Iver Raknes Finne</p>
           <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </div>
  )
}
