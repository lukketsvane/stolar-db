"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import ArticleNav from "../../../components/article-nav"
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
  datering: string
  fra_aar: number | null
  til_aar: number | null
  produksjonsstad: string
  produsent: string
  materialar: string
  teknikk: string
  dekorteknikk: string
  maal: string
  hoegde_cm: number | null
  breidde_cm: number | null
  djupn_cm: number | null
  setehoegde_cm: number | null
}

const PERIOD_SIZE = 50

function getPeriod(year: number): string {
  return `${Math.floor(year / PERIOD_SIZE) * PERIOD_SIZE}`
}

function normalizeType(betegnelse: string): string {
  const b = betegnelse.toLowerCase()
  if (b.includes("sofa")) return "Sofa"
  if (b.includes("lenestol") || b.includes("hvilestol") || b.includes("bibliotek")) return "Lenestol"
  if (b.includes("armstol") || b.includes("stolpestol") || b.includes("kongestol")) return "Armstol"
  if (b.includes("krakk") || b.includes("skammel") || b.includes("taburett")) return "Krakk"
  if (b.includes("gyngestol")) return "Gyngestol"
  if (b.includes("barnestol")) return "Barnestol"
  if (b.includes("kanapé")) return "Kanapé"
  if (b.includes("stol")) return "Stol"
  return "Anna"
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

  // Items with full 3D dimensions
  const withDims = useMemo(() =>
    data.filter(d => d.fra_aar && d.hoegde_cm && d.breidde_cm && d.djupn_cm),
  [data])

  // Figure 1: Volume convergence scatter
  const volumeScatter = useMemo(() =>
    withDims.map(d => ({
      year: d.fra_aar!,
      volume: Math.round((d.hoegde_cm! * d.breidde_cm! * d.djupn_cm!) / 1000),
      name: d.title,
      id: d.object_id,
    })).sort((a, b) => a.year - b.year),
  [withDims])

  // Figure 2: Technique frequency stacked area
  const techniqueTimeline = useMemo(() => {
    const keyTechniques = ["Polstring", "Tapping", "Dreiing", "Beising", "Relieffskjæring", "Profilering", "Formbøying", "Laminering", "Finering", "Lakkering"]
    const periods: Record<string, Record<string, number>> = {}

    data.forEach(item => {
      if (!item.fra_aar || !item.teknikk) return
      const period = getPeriod(item.fra_aar)
      if (!periods[period]) {
        periods[period] = { total: 0 }
        keyTechniques.forEach(t => periods[period][t] = 0)
      }
      periods[period].total++
      const techs = item.teknikk.split(";").map(t => t.trim())
      keyTechniques.forEach(kt => {
        if (techs.some(t => t.toLowerCase() === kt.toLowerCase())) {
          periods[period][kt]++
        }
      })
    })

    return Object.entries(periods)
      .map(([name, vals]) => {
        const result: Record<string, string | number> = { name }
        keyTechniques.forEach(kt => {
          result[kt] = vals.total > 0 ? Math.round((vals[kt] / vals.total) * 100) : 0
        })
        return result
      })
      .sort((a, b) => parseInt(a.name as string) - parseInt(b.name as string))
  }, [data])

  // Figure 3: Dimensional ratios over time
  const dimensionRatios = useMemo(() => {
    const periods: Record<string, { hws: number[], hds: number[] }> = {}
    withDims.forEach(d => {
      const period = getPeriod(d.fra_aar!)
      if (!periods[period]) periods[period] = { hws: [], hds: [] }
      periods[period].hws.push(d.hoegde_cm! / d.breidde_cm!)
      periods[period].hds.push(d.hoegde_cm! / d.djupn_cm!)
    })
    return Object.entries(periods)
      .map(([name, { hws, hds }]) => ({
        name,
        "H/B": Math.round((hws.reduce((a, b) => a + b, 0) / hws.length) * 100) / 100,
        "H/D": Math.round((hds.reduce((a, b) => a + b, 0) / hds.length) * 100) / 100,
        n: hws.length,
      }))
      .sort((a, b) => parseInt(a.name) - parseInt(b.name))
  }, [withDims])

  // Figure 4: Chair type distribution over time
  const typeDistribution = useMemo(() => {
    const types = ["Armstol", "Stol", "Lenestol", "Sofa", "Krakk", "Anna"]
    const periods: Record<string, Record<string, number>> = {}

    data.forEach(item => {
      if (!item.fra_aar || !item.betegnelse) return
      const century = `${Math.floor(item.fra_aar / 100) * 100}`
      if (!periods[century]) {
        periods[century] = {}
        types.forEach(t => periods[century][t] = 0)
      }
      const type = normalizeType(item.betegnelse)
      const key = types.includes(type) ? type : "Anna"
      periods[century][key]++
    })

    return Object.entries(periods)
      .map(([name, vals]) => ({ name, ...vals }))
      .sort((a, b) => parseInt(a.name) - parseInt(b.name))
  }, [data])

  // Figure 5: Height distribution by century
  const heightDistribution = useMemo(() => {
    const centuries: Record<string, number[]> = {}
    withDims.forEach(d => {
      const century = `${Math.floor(d.fra_aar! / 100) * 100}`
      if (!centuries[century]) centuries[century] = []
      centuries[century].push(d.hoegde_cm!)
    })
    return Object.entries(centuries)
      .map(([name, heights]) => ({
        name,
        Snitt: Math.round(heights.reduce((a, b) => a + b, 0) / heights.length),
        Min: Math.round(Math.min(...heights)),
        Maks: Math.round(Math.max(...heights)),
        n: heights.length,
      }))
      .sort((a, b) => parseInt(a.name) - parseInt(b.name))
  }, [withDims])

  // Volume stats by period for inline text
  const volumeStats = useMemo(() => {
    const periods: Record<string, number[]> = {}
    volumeScatter.forEach(d => {
      const period = getPeriod(d.year)
      if (!periods[period]) periods[period] = []
      periods[period].push(d.volume)
    })
    return Object.entries(periods).map(([name, vols]) => {
      const mean = vols.reduce((a, b) => a + b, 0) / vols.length
      const std = Math.sqrt(vols.reduce((s, v) => s + (v - mean) ** 2, 0) / vols.length)
      return { period: name, mean: Math.round(mean), std: Math.round(std), min: Math.min(...vols), max: Math.max(...vols), n: vols.length }
    }).sort((a, b) => parseInt(a.period) - parseInt(b.period))
  }, [volumeScatter])

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center font-mono text-[10px] uppercase tracking-widest text-gray-400">
        Lastar formdata...
      </div>
    )
  }

  const totalWithDims = withDims.length
  const yearSpan = data.filter(d => d.fra_aar).map(d => d.fra_aar!)
  const minYear = Math.min(...yearSpan)
  const maxYear = Math.max(...yearSpan)

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      {/* Navigasjon */}
      <ArticleNav />

      {/* Artikkel-header */}
      <header className="max-w-7xl mx-auto pt-48 pb-32 px-6 md:px-12 lg:px-24">
        <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel II</p>
        <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Form follows<br/>
          <span className="text-gray-200">fitness.</span>
        </h1>
        <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight max-w-3xl mt-8">
          Mot ein evolusjonær formteori for stolen.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16">
          <div>
            <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed max-w-xs">
              Arkitektur- og designhøgskolen i Oslo (AHO)
            </p>
          </div>
          <div>
            <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Formkurveanalyse</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Kvantitativ analyse av dimensjonar over 740 år med stoldesign.
            </p>
          </div>
        </div>

        <div className="max-w-2xl bg-gray-50 p-8 md:p-12 lg:p-16 rounded-2xl md:rounded-[2rem] border border-gray-100 italic text-base md:text-xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> Artikkelen introduserer <em>form follows fitness</em> som eit evolusjonært rammeverk for å analysere formutvikling i industridesign. Gjennom eit datasett på {data.length} norskproduserte stolar &mdash; {totalWithDims} med fulle tredimensjonale mål &mdash; kvantifiserer studien tre formvariablar over {maxYear - minYear} år: omsluttande volum, proporsjonar og teknikk-regime. Hovudfunnet er <em>fitness-konvergensen</em>: ein empirisk demonstrerbar tendens der stolars omsluttande volum konvergerer mot eit felles dimensjonsområde etter industrialiseringa, trass i aukande stilistisk divergens. Mot Le Corbusier sin maskinanalogi og Sullivan sitt «form follows function» argumenterer artikkelen for at form ikkje er determinert av funksjon, men selektert av fitness &mdash; ei tilpassing til samtidige materielle, økonomiske, ergonomiske og kulturelle miljø.
        </div>
      </header>

      {/* Artikkel-tekst */}
      <article className="max-w-2xl mx-auto px-6 md:px-12 lg:px-24 space-y-12 text-base md:text-lg leading-relaxed text-gray-900 font-serif">

        {/* 1. INNLEIING */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">1. Innleiing: Problemet med &laquo;form follows function&raquo;</h2>
          <p className="mb-12">
            I 1896 skreiv Louis Sullivan at &laquo;form ever follows function&raquo;. Setninga vart eit aksiom. Le Corbusier radikaliserte ho i 1923: huset er <em>une machine a habiter</em> &mdash; ein maskin til a bu i. Maskinen har ingen overflodig form; kvar detalj tener ein funksjon. Designhistoria etter Le Corbusier har oscillert mellom a akseptere dette premisset og a reagere mot det, men sjeldan a erstatte det med eit meir presist alternativ.
          </p>
          <p className="mb-12">
            Problemet er empirisk. Dersom form folger funksjon, burde alle stolar med same funksjon &mdash; a sitje pa &mdash; ha same form. Det har dei ikkje. Nasjonalmuseet si samling av {data.length} norskproduserte stolar, som spenner fra {minYear} til {maxYear}, inneheld ei enorm formvariasjon: fra den massive Garastolen i furu til Harry Bertoia sin Diamond Chair i sveist stal. Begge tener same grunnfunksjon. Formene er radikalt ulike. &laquo;Form follows function&raquo; kan ikkje forklare denne variasjonen.
          </p>
          <p className="mb-12">
            Le Corbusier sitt maskinparadigme har eit djupare problem. Ein maskin er designa; han er ikkje tilpassa. Skilnaden er avgjerande. Ein designa gjenstand vert skapt av ein intensjon som realiserer ein plan. Ein tilpassa gjenstand vert forma av eit miljo som selekterer mellom variantar. Darwin sin evolusjonsteori handlar ikkje om design, men om <em>fitness</em>: den differensielle overlevinga av variantar i eit gjeve miljo.
          </p>
          <p>
            Denne artikkelen introduserer <em>form follows fitness</em> som eit rammeverk med tre premiss: (1) Form er ikkje determinert av funksjon &mdash; same funksjon produserer mange formar. (2) Form er selektert av fitness &mdash; dei formene som overlever er dei best tilpassa eit komplekst miljo av seleksjonstrykk. (3) Fitness er kvantifiserbar &mdash; gjennom systematisk maling av formvariablar over tid kan ein identifisere konvergensar og seleksjonslandskap empirisk.
          </p>
        </section>

        {/* 2. DATASETT OG METODE */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">2. Datasett og metode</h2>
          <p className="mb-12">
            Datasettet byggjer pa Nasjonalmuseet sin digitale katalog og omfattar {data.length} norskproduserte stolar daterte fra {minYear} til {maxYear}. Av desse har {totalWithDims} objekt fulle tredimensjonale mal (hogde, breidde, djupn), noko som gjer det mogleg a kalkulere omsluttande volum &mdash; ein robust og universelt tilgjengeleg formvariabel som kvantifiserer kor mykje rom stolen okkuperer.
          </p>
          <p className="mb-12">
            Metoden har tre steg. Fyrst: <em>dimensjonsanalyse</em> &mdash; omsluttande volum (hogde &times; breidde &times; djupn) og proporsjonar (hogde/breidde-ratio, hogde/djupn-ratio) vert kalkulerte for kvart objekt. Deretter: <em>teknikkdekomposisjon</em> &mdash; kvar stol sine registrerte teknikkar vert splitta og kvantifiserte per tidsperiode for a identifisere teknikk-regime. Til slutt: <em>typologisk kartlegging</em> &mdash; betegnelsar vert normaliserte til hovudtypar (Armstol, Stol, Lenestol, Sofa) og plotta over tid.
          </p>
          <p>
            Tilnaerminga er inspirert av Franco Moretti sitt omgrep <em>distant reading</em> og Lev Manovich sin <em>cultural analytics</em> &mdash; a lese ikkje ein stol, men hundrevis, og la monstre som er usynlege i enkeltobjektet bli synlege i aggregatet.
          </p>
        </section>

        {/* FIGUR 1: Volume convergence scatter plot */}
        <section className="py-12 full-bleed">
          <div className="bg-black p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#333_1px,transparent_1px)] [background-size:30px_30px]" />
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.6em] text-gray-600 mb-20 text-center">FIGUR 1: Omsluttande volum over tid (n={totalWithDims})</h4>
            <div className="h-[300px] md:h-[600px]">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ left: 20, right: 40, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#222" />
                  <XAxis
                    dataKey="year"
                    type="number"
                    domain={[1200, 2020]}
                    stroke="#444"
                    tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666', fontWeight: '900' }}
                    name="Ar"
                  />
                  <YAxis
                    dataKey="volume"
                    type="number"
                    stroke="#444"
                    tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666', fontWeight: '900' }}
                    name="Volum"
                    unit=" L"
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', color: '#fff', borderRadius: '0px', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                    formatter={(value: number, name: string) => {
                      if (name === "Volum") return [`${value} liter`, 'Volum']
                      return [value, name]
                    }}
                    labelFormatter={(label) => `${label}`}
                  />
                  <Scatter data={volumeScatter} fill="#fff" fillOpacity={0.8} r={4}>
                    {volumeScatter.map((entry, i) => (
                      <Cell key={i} fill={entry.volume > 500 ? '#fff' : '#888'} fillOpacity={entry.volume > 500 ? 1 : 0.6} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-500 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Spreiinga minkar dramatisk etter industrialiseringa. Moderne stolar konvergerer mot 100-300 liter.
            </p>
          </div>
        </section>

        {/* 3. FITNESS-KONVERGENSEN */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">3. Fitness-konvergensen</h2>
          <p className="mb-12">
            Figur 1 er det sentrale funnet i denne studien. Omsluttande volum &mdash; hogde gonger breidde gonger djupn, uttrykt i liter &mdash; viser ein tydeleg <strong>konvergens</strong> over tid. Fra ein stor spreiing i tidlege periodar, der massive middelalderstolar og kompakte krakkar sameksisterer, mot eit smalare band etter om lag 1850.
          </p>
          <p className="mb-12">
            Tala er eintydige. {volumeStats.length > 0 && <>I dei tidlegaste periodane (for 1700) spenner volumet fra {volumeStats[0]?.min} til {volumeStats[0]?.max} liter. I perioden rundt 1850 er spreiinga framleis stor, men etter 1900 konvergerer stolane mot eit band pa om lag 100&ndash;300 liter.</>} Denne konvergensen er ikkje ein reduksjon av kreativitet &mdash; det er eit uttrykk for auka seleksjonstrykk.
          </p>
          <p className="mb-12">
            Monsteret er ein designhistorisk parallell til <em>konvergent evolusjon</em> i biologi: nar ulike organismar utviklar liknande kroppsformar fordi dei er tilpassa same miljo. I stolens tilfelle er &laquo;miljoet&raquo; eit sett av seleksjonstrykk: menneskekroppens dimensjonar (ergonomisk trykk), produksjonseffektivitet (okonomisk trykk), transportlogistikk (logistisk trykk) og romleg integrering i standardiserte bustadar (arkitektonisk trykk).
          </p>
          <p>
            Desse trykka produserer ein konvergens mot ein felles <em>fitness-topp</em> &mdash; eit dimensjonsomrade som er optimalt for alle desse kriteria samstundes. Stolen vert ikkje designa mot ein form; han vert selektert mot eit miljo.
          </p>
        </section>

        {/* FIGUR 2: Technique frequency stacked area */}
        <section className="py-12 full-bleed">
          <div className="bg-gray-50 p-12 lg:p-24 rounded-[4rem] border border-gray-100 overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 2: Teknikk-regime over tid (% av stolar per {PERIOD_SIZE}-arsperiode)</h4>
            <div className="h-[600px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={techniqueTimeline}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#e5e5e5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} />
                  <YAxis tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} unit="%" />
                  <Tooltip
                    contentStyle={{ borderRadius: '0px', border: '1px solid #000', boxShadow: 'none', fontFamily: 'ui-monospace, monospace', fontSize: '11px', fontWeight: '900' }}
                  />
                  <Legend verticalAlign="top" height={60} iconType="square" wrapperStyle={{ paddingBottom: '20px', fontFamily: 'ui-monospace, monospace', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.15em', fontWeight: '900' }} />
                  <Area type="stepAfter" dataKey="Polstring" stackId="1" stroke="#000" fill="#000" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Tapping" stackId="1" stroke="#333" fill="#222" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Dreiing" stackId="1" stroke="#555" fill="#444" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Beising" stackId="1" stroke="#777" fill="#666" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Relieffskjæring" stackId="1" stroke="#999" fill="#888" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Profilering" stackId="1" stroke="#aaa" fill="#999" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Formbøying" stackId="1" stroke="#bbb" fill="#aaa" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Laminering" stackId="1" stroke="#ccc" fill="#bbb" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Finering" stackId="1" stroke="#ddd" fill="#ccc" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="Lakkering" stackId="1" stroke="#eee" fill="#ddd" fillOpacity={1} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-400 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Polstring dominerer fra 1700. Dreiing og tapping er tidlege teknikkar. Formboying og laminering kjem etter 1900.
            </p>
          </div>
        </section>

        {/* 4. TEKNIKK SOM FORMSPRAK */}
        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">4. Teknikk som formsprak</h2>
          <p className="mb-12">
            Figur 2 avdekkjer tre distinkte <strong>teknikk-regime</strong> i den norske stolhistoria. Kvart regime definerer eit sett av formelle moglegheiter &mdash; kva formar som er tenkjelege og realiserbare med den tilgjengelege teknologien.
          </p>
          <div className="space-y-16 my-16 border-l-4 border-black pl-12">
            <div>
              <h3 className="font-sans font-black text-lg uppercase tracking-tight mb-3">I. Det subtraktive regimet (1200&ndash;1700)</h3>
              <p className="text-xl leading-relaxed text-gray-700">
                Dreiing, tapping, relieffskjaering, gjennombrutt utskjaering. Forma vert skapt ved a fjerne materiale &mdash; a dreie, skjaere, bore. Resultatet er monumentale, tunge stolar med massivt trevirke. Kvar detalj er skoren for hand. Formspenstet er avgrensa av det menneskeleg arm kan skjaere ut av eit tre-emne.
              </p>
            </div>
            <div>
              <h3 className="font-sans font-black text-lg uppercase tracking-tight mb-3">II. Det additive regimet (1700&ndash;1900)</h3>
              <p className="text-xl leading-relaxed text-gray-700">
                Polstring, beising, fernissering, forgylling. Forma vert skapt ved a leggje til &mdash; polstring over tremmen, beis over overflata, gullblad over treskurd. Resultatet er lettare konstruksjonar med komplekse overflater. Stolen vert eit samansett objekt av tre, tekstil, taglfyll og overflatebehandling.
              </p>
            </div>
            <div>
              <h3 className="font-sans font-black text-lg uppercase tracking-tight mb-3">III. Det transformative regimet (1900&ndash;2005)</h3>
              <p className="text-xl leading-relaxed text-gray-700">
                Formboying, laminering, lakkering, finering. Forma vert skapt ved a transformere materialet sjolv &mdash; a boye tre med damp, a laminere kryssfiner i pressformer. Resultatet er stolar med kurver og former som er umoglege i massivt tre. Materialets grenser vert overskridne gjennom industriell prosessering.
              </p>
            </div>
          </div>
          <p>
            Kvart teknikk-regime produserer eit distinkt formsprak. Dreiing gjev sylindriske element og vertikale aksiar. Polstring gjev mjuke volum og horisontale flater. Formboying gjev kurver og kontinuerlege liner. Teknikken er ikkje berre eit middel til a realisere ein form &mdash; teknikken <em>er</em> formspraket.
          </p>
        </section>

        {/* FIGUR 3: Dimensional ratios */}
        <section className="py-12 full-bleed">
          <div className="bg-white p-12 lg:p-24 rounded-[4rem] border border-gray-100 shadow-sm overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 3: Proporsjonar over tid (snitt hogde/breidde og hogde/djupn per {PERIOD_SIZE}-arsperiode)</h4>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dimensionRatios} margin={{ left: 20, right: 40 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#e5e5e5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} />
                  <YAxis tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} domain={[0, 'auto']} />
                  <Tooltip
                    contentStyle={{ borderRadius: '0px', border: '1px solid #000', boxShadow: 'none', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                    formatter={(value: number, name: string) => {
                      return [`${value}`, name]
                    }}
                  />
                  <Legend verticalAlign="top" height={40} wrapperStyle={{ fontFamily: 'ui-monospace, monospace', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: '900' }} />
                  <Line type="monotone" dataKey="H/B" stroke="#000" strokeWidth={3} dot={{ fill: '#000', r: 5 }} name="Hogde / Breidde" />
                  <Line type="monotone" dataKey="H/D" stroke="#999" strokeWidth={2} dot={{ fill: '#999', r: 4 }} strokeDasharray="5 5" name="Hogde / Djupn" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-400 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Proporsjonane stabiliserer seg etter 1800 &mdash; stolen finn sin ergonomiske likevekt.
            </p>
          </div>
        </section>

        {/* 5. TYPOLOGISK EVOLUSJON */}
        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">5. Typologisk evolusjon</h2>
          <p className="mb-12">
            Figur 4 avdekkjer ein typologisk evolusjon som folger ein klar logikk. I dei eldste periodane dominerer <strong>Armstolen</strong> &mdash; den massive, monumentale stolen med armlene, berekna for hovdingar og kyrkjeleiarar. Armstolen er ikkje ein kvardagsmobel; han er eit maktteikn.
          </p>
          <p className="mb-12">
            Fra 1700 tek <strong>Stol</strong> &mdash; den armlause, lettare varianten &mdash; over som den dominerande typen. Denne overgangen er ikkje tilfeldig. Ho korrelerer med framveksten av borgarleg selskapsliv, der stolar vart arrangerte i rekker, ikkje som enkelttronar. Den armlause stolen tek mindre plass, kan stablast og er billegare a produsere.
          </p>
          <p className="mb-12">
            Etter 1900 kjem den typologiske <em>divergensen</em>. <strong>Lenestol</strong>, <strong>Sofa</strong>, <strong>Gyngestol</strong> og spesialiserte variantar eksploderer i tal. Denne diversifiseringa er ein direkte konsekvens av industrialiseringa: nar produksjonskostnadene fell, vert det mogleg a designe stolar for spesifikke brukssituasjonar. Stolen differensierer seg &mdash; ikkje fordi funksjonen krev det, men fordi fitness-landskapet diversifiserer seg.
          </p>
          <p>
            I biologien kallar ein dette <em>adaptiv radiasjon</em>: nar ein artslinje plutseleg fann tilgang til mange tomme nisjar og diversifiserte raskt. Stolens adaptive radiasjon skjer etter 1900, nar industrielle produksjonsmetodar opnar nye formelle og ekonomiske nisjar som tidlegare var utilgjengelege.
          </p>
        </section>

        {/* FIGUR 4: Chair type distribution */}
        <section className="py-12 full-bleed">
          <div className="bg-black p-12 lg:p-24 rounded-[4rem] shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#333_1px,transparent_1px)] [background-size:30px_30px]" />
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.6em] text-gray-600 mb-20 text-center">FIGUR 4: Typologisk fordeling per hundre-ar</h4>
            <div className="h-[500px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={typeDistribution}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#222" />
                  <XAxis dataKey="name" stroke="#444" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666', fontWeight: '900' }} />
                  <YAxis stroke="#444" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fill: '#666', fontWeight: '900' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', color: '#fff', borderRadius: '0px', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                  />
                  <Legend verticalAlign="top" height={60} iconType="square" wrapperStyle={{ paddingBottom: '20px', fontFamily: 'ui-monospace, monospace', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.15em', fontWeight: '900' }} />
                  <Bar dataKey="Armstol" stackId="a" fill="#fff" />
                  <Bar dataKey="Stol" stackId="a" fill="#aaa" />
                  <Bar dataKey="Lenestol" stackId="a" fill="#666" />
                  <Bar dataKey="Sofa" stackId="a" fill="#444" />
                  <Bar dataKey="Krakk" stackId="a" fill="#333" />
                  <Bar dataKey="Anna" stackId="a" fill="#222" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-500 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Adaptiv radiasjon: fra armstol-dominans til typologisk mangfald etter industrialiseringa.
            </p>
          </div>
        </section>

        {/* 6. MATERIELL FORM */}
        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">6. Materiell form: Korleis stoffet bestemmer strukturen</h2>
          <p className="mb-12">
            I den <a href="/article" className="underline hover:no-underline">fyrste artikkelen i denne serien</a> analyserte eg materialkurvene i Nasjonalmuseet si stolsamling og identifiserte fire materialregime: det lokale treregime, den tidlege importfasen, det koloniale regimet og det industrielle regimet. Kvart materialregime avgrensar ikkje berre kva stolen er <em>laga av</em>, men kva former som er <em>mogleg</em>.
          </p>
          <p className="mb-12">
            Massiv furu og eik (det lokale treregime) avgrensar forma til det som kan hoggast, dreiast og tappast. Resultatet er rette liner, sylindriske element og tunge proporsjonar. Mahogni (det koloniale regimet) er eit finare trevirke som toler tunnare dimensjonar og meir detaljert treskurd &mdash; forma vert lettare og meir dekorert, men framleis avgrensa av massivt trevirke sin strukturelle logikk.
          </p>
          <p className="mb-12">
            Kryssfiner og formboygd tre (det industrielle regimet) sprengar desse grensene. Nar treet kan boyast i kurver og laminatlag kan pressast i former, vert det mogleg a skape stolar med kontinuerlege flater, tynne profilar og organiske kurver. Alvar Aalto, Charles og Ray Eames og norske Westnofa-designarar utforska alle dette nye formspraket.
          </p>
          <p>
            Materialet determinerer ikkje forma, men det <em>avgrensar moglegheitsrommet</em>. Innanfor kvart materialregime er formvariasjonen stor, men visse formar er umoglege utan visse material. Form folger ikkje funksjon &mdash; form folger materialets moglegheiter, avgrensa av teknikk og selektert av fitness.
          </p>
        </section>

        {/* FIGUR 5: Height distribution */}
        <section className="py-12 full-bleed">
          <div className="bg-gray-50 p-12 lg:p-24 rounded-[4rem] border border-gray-100 overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 5: Hogdefordeling per hundre-ar (snitt, min, maks i cm)</h4>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={heightDistribution} margin={{ left: 20, right: 40 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#e5e5e5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} />
                  <YAxis tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} unit=" cm" />
                  <Tooltip
                    contentStyle={{ borderRadius: '0px', border: '1px solid #000', boxShadow: 'none', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                    formatter={(value: number, name: string) => [`${value} cm`, name]}
                  />
                  <Legend verticalAlign="top" height={40} wrapperStyle={{ fontFamily: 'ui-monospace, monospace', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: '900' }} />
                  <Bar dataKey="Maks" fill="#ddd" radius={0} barSize={30} name="Maks" />
                  <Bar dataKey="Snitt" fill="#000" radius={0} barSize={30} name="Snitt" />
                  <Bar dataKey="Min" fill="#999" radius={0} barSize={30} name="Min" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-400 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Hogda konvergerer: spreiinga mellom min og maks minkar over tid.
            </p>
          </div>
        </section>

        {/* 7. DISKUSJON */}
        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">7. Diskusjon: Kvifor Le Corbusier tok feil</h2>
          <p className="mb-12">
            Le Corbusier sitt maskinparadigme impliserer at design er ein <em>deterministisk</em> prosess: identifiser funksjonen, deduser forma. Men dataa viser at same funksjon (a sitje) produserer hundrevis av ulike formar over {maxYear - minYear} ar. Forma er ikkje determinert; ho er selektert. Maskinen er feil metafor. Organismen er riktigare.
          </p>
          <p className="mb-12">
            Daniel Dennett argumenterte for at Darwin si ide &mdash; seleksjon utan design &mdash; er universell. Ho gjeld overalt der det finst variasjon, arv og differensiell reproduksjon. Alle tre er til stades i designhistoria: formvariasjonen er enorm, stolar kopierer og vidareutviklar tidlegare formar, og nokre formar overlever medan andre doyr ut. <em>Form follows fitness</em> er ikkje ein metafor &mdash; det er ein strukturell parallell.
          </p>
          <p className="mb-12">
            Det storste funnet &mdash; at omsluttande volum konvergerer etter industrialiseringa &mdash; er direkte bevis mot den postmoderne relativismen som hevdar at alle formar er like gyldige. Dei er ikkje det. Industrialiseringa innforte nye seleksjonstrykk som eliminerte mange tidlegare gyldige formar og belonna dei som passa inn i det nye miljoet.
          </p>
          <p>
            Samstundes aukar den stilistiske divergensen, noko som viser at fitness ikkje er det same som uniformitet. Innanfor det konvergerte dimensjonsomradet er formvariasjonen framleis enorm. Organismen er tilpassa miljoet &mdash; men mange ulike organismar kan vere tilpassa same miljo. Konvergensen er ikkje ein reduksjon av kreativitet; ho er eit uttrykk for at kreativiteten opererer innanfor eit fitness-landskap som vert meir presist definert av industrielle, ergonomiske og okonomiske krefter.
          </p>
        </section>

        {/* 8. KONKLUSJON */}
        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
            <p>
              Denne artikkelen har introdusert <em>form follows fitness</em> som eit evolusjonaert rammeverk for designhistorie og kvantifisert formvariablar over {maxYear - minYear} ar med stoldesign. Tre hovudfunn melder seg.
            </p>
            <p>
              For det fyrste: <strong className="not-italic text-black">Fitness-konvergensen.</strong> Stolars omsluttande volum konvergerer mot eit felles dimensjonsomrade etter industrialiseringa &mdash; eit empirisk funn som verken funksjonalismen eller postmodernismen kan forklare. Funksjonalismen predikerer ein eintydig optimal form (feil: variasjonen er for stor). Postmodernismen predikerer ingen konvergens (feil: konvergensen er dokumenterbar). <em>Form follows fitness</em> predikerer konvergens <em>med</em> vedvarande variasjon innanfor det konvergerte omradet &mdash; noko som er eksakt det dataa viser.
            </p>
            <p>
              For det andre: <strong className="not-italic text-black">Teknikk-regime.</strong> Tre distinkte teknikk-regime &mdash; subtraktivt, additivt, transformativt &mdash; definerer kvar sin formelle moglegheitsrom. Kvart regime produserer eit distinkt formsprak som avgrensar kva stolar som er tenkjelege.
            </p>
            <p>
              For det tredje: <strong className="not-italic text-black">Typologisk radiasjon.</strong> Fraa armstol-dominans til ein typologisk mangfald som eksploderer etter industrialiseringa &mdash; ein designhistorisk parallell til adaptiv radiasjon i biologi.
            </p>
            <p className="text-black not-italic font-sans font-black text-3xl leading-tight tracking-tight">
              Le Corbusier sin maskinanalogi er ikkje berre utdatert &mdash; ho er falsifisert av dataa. Form er ikkje determinert av funksjon; form er selektert av fitness.
            </p>
          </div>
        </section>
      </article>

      {/* Referansar */}
      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Corbusier, Le (1923). <em className="normal-case tracking-normal">Vers une architecture.</em> Cres.</p>
          <p>Darwin, C. (1859). <em className="normal-case tracking-normal">On the Origin of Species.</em> John Murray.</p>
          <p>Dawkins, R. (1986). <em className="normal-case tracking-normal">The Blind Watchmaker.</em> Longman.</p>
          <p>Dennett, D. C. (1995). <em className="normal-case tracking-normal">Darwin's Dangerous Idea.</em> Simon & Schuster.</p>
          <p>Finne, I. R. (2026). <em className="normal-case tracking-normal">Materialhistorie: Kolonialt arkiv.</em> AHO Working Paper.</p>
          <p>Manovich, L. (2020). <em className="normal-case tracking-normal">Cultural Analytics.</em> MIT Press.</p>
          <p>Moretti, F. (2005). <em className="normal-case tracking-normal">Graphs, Maps, Trees: Abstract Models for Literary History.</em> Verso.</p>
          <p>Pye, D. (1968). <em className="normal-case tracking-normal">The Nature and Art of Workmanship.</em> Cambridge University Press.</p>
          <p>Steadman, P. (2008). <em className="normal-case tracking-normal">The Evolution of Designs.</em> Routledge.</p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case tracking-normal">Lippincott's Magazine,</em> 57, 403-409.</p>
          <p>Thompson, D. W. (1917). <em className="normal-case tracking-normal">On Growth and Form.</em> Cambridge University Press.</p>
        </div>

        <div className="mt-20 pt-12 border-t border-gray-100">
          <p className="text-[10px] font-mono font-black uppercase tracking-[0.3em] text-gray-300 mb-8">Sjaa ogsa</p>
          <button
            onClick={() => router.push('/article')}
            className="text-lg font-sans font-black tracking-tight hover:line-through transition-all"
          >
            Del I: Materialhistorie. Kolonialt arkiv. &rarr;
          </button>
        </div>

        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhogskolen i Oslo</p>
        </div>
      </footer>
    </div>
  )
}
