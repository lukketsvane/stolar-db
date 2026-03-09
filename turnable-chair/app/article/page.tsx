"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import ArticleLayout from "../../components/article-layout"
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
  Legend,
  LineChart,
  Line,
} from "recharts"

interface ChairItem {
  id: string
  year: string
  materials: string
  location: string
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

  const materialDiversity = useMemo(() => {
    const centuries: Record<string, { materials: Set<string>, count: number }> = {}

    data.forEach((item) => {
      const yearStr = item.year.match(/\d{4}/)?.[0]
      if (yearStr) {
        const century = `${Math.floor(parseInt(yearStr) / 50) * 50}`
        if (!centuries[century]) {
          centuries[century] = { materials: new Set(), count: 0 }
        }
        centuries[century].count++
        const mats = (item.materials || "").toLowerCase().split(/[,;]/).map(s => s.trim()).filter(Boolean)
        mats.forEach(m => centuries[century].materials.add(m))
      }
    })

    return Object.entries(centuries)
      .map(([name, val]) => ({
        name,
        unike: val.materials.size,
        stolar: val.count
      }))
      .sort((a, b) => parseInt(a.name) - parseInt(b.name))
  }, [data])

  const topMaterials = useMemo(() => {
    const counts: Record<string, number> = {}
    data.forEach(item => {
      const mats = (item.materials || "").toLowerCase().split(/[,;]/).map(s => s.trim()).filter(Boolean)
      mats.forEach(m => {
        counts[m] = (counts[m] || 0) + 1
      })
    })
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 15)
  }, [data])

  if (loading) {
    return <div className="min-h-screen bg-white flex items-center justify-center font-mono text-xs uppercase tracking-widest text-gray-400">Lastar historikk...</div>
  }

  const header = (
    <div className="max-w-4xl">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel I</p>
      <h1 className="text-6xl md:text-[10rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Materialhistorie.<br/>
        <span className="text-gray-200">Kolonialt arkiv.</span>
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16 font-sans">
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">
            Arkitektur- og designhøgskolen i Oslo (AHO)
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

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> Artikkelen presenterer den fyrste systematiske kvantitative materialanalysen av Nasjonalmuseet si stolsamling — {data.length} objekt daterte mellom 1280 og 2020. Gjennom eit nytt strukturert datasett undersøkjer studien korleis materialkurver fungerer som eit kolonialt arkiv. Hovudfunnet er <em>mahogniens boge</em>: ein materiell signatur der karibisk tropisk hardved stig dramatisk for deretter å kollapse, nesten synkront med den transatlantiske mahognihandelen.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing</h2>
        <p>
          I magasinet til Nasjonalmuseet i Oslo står det ein stol registrert som <strong>OK-10330A</strong>, datert til om lag 1830. Materiallista er kort: mahogni, hestetagl, furu, eik, whitewood. For ein konvensjonell designhistorikar er dette ein anonym empirestol. Men materiallista er ikkje anonym. Ho er eit komprimert verdskart.
        </p>
        <p>
          Mahognien kjem frå tropiske regnskogar i Karibia, felt av tvangsarbeidande menneske under det britiske kolonistyret. Hestetaglet — polstringsfyllet — vitnar om eit europeisk handverkssystem der animalske biprodukt vart omforma til komfort. Furu og eik er norske. Fem materialar frå minst tre kontinent, samla i éin norsk stol.
        </p>
        <p>
          Denne artikkelen presenterer den fyrste systematiske, kvantitative materialanalysen av Nasjonalmuseet si stolsamling. Datasettet omfattar {data.length} stolar daterte frå 1280 til 2020. Metoden eg kallar <em>materialkurveanalyse</em> kartlegg kva materialar som dominerer i kvar periode, korleis dei stig og fell, og kva desse kurvene avslører om geopolitiske maktforhold.
        </p>
      </section>

      <section>
        <h2>2. Datasett og metode</h2>
        <p>
          Datasettet er konstruert frå Nasjonalmuseet sin digitale katalog. Kvart objekt er registrert med inventarnummer, datering, produksjonsstad, materialar, teknikkar, og dimensjonar. Eg har filtrert for stolar produserte i Noreg, noko som gjev eit utval på {data.length} objekt.
        </p>
        <p>
          Metoden har tre steg. Fyrst: <em>materialtelling</em>. Deretter: <em>kurvekonstruksjon</em>. Til slutt: <em>geopolitisk lesing</em>. Ein slik metode er inspirert av Franco Moretti sitt omgrep <em>distant reading</em> — å lese ikkje éin tekst, men tusen; ikkje éin stol, men hundre.
        </p>
      </section>

      <section className="not-prose my-32">
        <div className="bg-white p-8 md:p-12 lg:p-16 rounded-3xl border border-gray-100 shadow-sm">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 1: Topp materialfrekvens</h4>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topMaterials} layout="vertical" margin={{ left: 20, right: 40 }}>
                <CartesianGrid strokeDasharray="2 2" horizontal={false} stroke="#e5e5e5" />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 10, fontFamily: 'ui-monospace', fontWeight: '900' }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#fafafa' }} contentStyle={{ borderRadius: '0px', border: '1px solid #000', fontFamily: 'ui-monospace', fontSize: '10px' }} />
                <Bar dataKey="value" fill="#000" radius={0} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section>
        <h2>3. Fire materialregime</h2>
        <p>
          Materialkurveanalysen avdekkjer fire distinkte regime i den norske stolhistoria.
        </p>
        <ul>
          <li><strong>I. Det lokale treregime (1280–1650):</strong> Furu, bjørk, eik, ask. Alt er lokalt.</li>
          <li><strong>II. Den tidlege importfasen (1650–1750):</strong> Lær, messing, tekstil, silke. Import frå kontinentet.</li>
          <li><strong>III. Det koloniale regimet (1750–1900):</strong> Mahogni, hestetagl, bøk. Direkte konsekvens av transatlantisk kolonialisme.</li>
          <li><strong>IV. Det industrielle regimet (1900–2020):</strong> Kryssfiner, stål, plast, skumgummi.</li>
        </ul>
      </section>

      <section className="not-prose my-32">
        <div className="bg-black p-8 md:p-12 lg:p-16 rounded-3xl shadow-2xl">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.6em] text-gray-600 mb-20 text-center">FIGUR 2: Mahogniens boge (% av stolar)</h4>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={materialTimeline}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#222" />
                <XAxis dataKey="name" stroke="#444" tick={{ fontSize: 10, fill: '#666' }} />
                <YAxis stroke="#444" tick={{ fontSize: 10, fill: '#666' }} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333', color: '#fff' }} />
                <Area type="stepAfter" dataKey="mahogni" stroke="#fff" fill="#fff" fillOpacity={1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section>
        <h2>4. Konklusjon</h2>
        <p>
          Nasjonalmuseet sitt magasin plasserer seg som ein perifer node i eit globalt handelsnettverk. Å opne skuffa til ein norsk empirestol er å opne eit kolonialt arkiv.
        </p>
      </section>

      <footer className="mt-32 pt-16 border-t border-gray-100 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
        <p>&copy; 2026 Iver Raknes Finne</p>
        <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
      </footer>
    </ArticleLayout>
  )
}
