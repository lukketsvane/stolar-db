"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import ArticleNav from "../../components/article-nav"
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
  ScatterChart,
  Scatter,
  ZAxis,
  Cell,
  LineChart,
  Line
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
  techniques: string
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
    const periods: Record<string, Set<string>> = {}
    const periodCounts: Record<string, number> = {}

    data.forEach((item) => {
      const yearStr = item.year.match(/\d{4}/)?.[0]
      if (yearStr) {
        const period = Math.floor(parseInt(yearStr) / 50) * 50
        const periodStr = `${period}`
        if (!periods[periodStr]) {
          periods[periodStr] = new Set()
          periodCounts[periodStr] = 0
        }
        periodCounts[periodStr]++
        const matStr = (item.materials || "").toLowerCase()
        matStr.split(",").map(m => m.trim()).filter(Boolean).forEach(m => {
          periods[periodStr].add(m)
        })
      }
    })

    return Object.entries(periods)
      .map(([name, mats]) => ({
        name,
        unike: mats.size,
        stolar: periodCounts[name],
        diversitet: Math.round((mats.size / Math.max(periodCounts[name], 1)) * 100) / 100
      }))
      .sort((a, b) => parseInt(a.name) - parseInt(b.name))
  }, [data])

  const chairTimeline = useMemo(() => {
    return data
      .map(item => {
        const yearStr = item.year.match(/\d{4}/)?.[0]
        if (!yearStr) return null
        const year = parseInt(yearStr)
        const matStr = (item.materials || "").toLowerCase()
        const matCount = matStr.split(",").map(m => m.trim()).filter(Boolean).length
        const hasMahogni = matStr.includes("mahogni")
        return { year, matCount, hasMahogni, id: item.id, name: item.name }
      })
      .filter(Boolean)
      .sort((a: any, b: any) => a.year - b.year)
  }, [data])

  const topMaterials = useMemo(() => {
    const counts: Record<string, number> = {}
    data.forEach(item => {
      const matStr = (item.materials || "").toLowerCase()
      matStr.split(",").map(m => m.trim()).filter(Boolean).forEach(m => {
        counts[m] = (counts[m] || 0) + 1
      })
    })
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value, pct: Math.round((value / data.length) * 100) }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 12)
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
          &larr; Stol-database
        </button>
        <div className="hidden md:flex gap-8">
          <div className="text-[10px] font-mono font-black text-black tracking-[0.3em] uppercase border-b border-black pb-1">
            I. Materialhistorie
          </div>
          <button
            onClick={() => router.push('/article/form')}
            className="text-[10px] font-mono font-black text-gray-400 tracking-[0.3em] uppercase hover:text-black transition-colors"
          >
            II. Formhistorie
          </button>
        </div>
      </nav>

      {/* Artikkel-header */}
      <header className="max-w-7xl mx-auto pt-48 pb-32 px-6 md:px-12 lg:px-24">
        <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel I</p>
        <h1 className="text-6xl md:text-[10rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Materialhistorie.<br/>
          <span className="text-gray-200">Kolonialt arkiv.</span>
        </h1>

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
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Materialkurveanalyse</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Systematisk kvantifisering av materialfordeling over tid i samlinga.
            </p>
          </div>
        </div>

        <div className="max-w-4xl bg-gray-50 p-8 md:p-16 lg:p-24 rounded-2xl md:rounded-[3rem] border border-gray-100 italic text-xl md:text-3xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> Artikkelen presenterer den fyrste systematiske kvantitative materialanalysen av Nasjonalmuseet si stolsamling — {data.length} objekt daterte mellom 1280 og 2020. Gjennom eit nytt strukturert datasett undersøkjer studien korleis materialkurver fungerer som eit kolonialt arkiv. Hovudfunnet er <em>mahogniens boge</em>: ein materiell signatur der karibisk tropisk hardved stig dramatisk for deretter å kollapse, nesten synkront med den transatlantiske mahognihandelen. Studien identifiserer fire distinkte materialregime og demonstrerer korleis ein stol — som fysisk objekt — ber i seg eit komprimert narrativ om global handel, kolonial utvinning og industriell transformasjon.
        </div>
      </header>

      {/* Artikkel-tekst */}
      <article className="max-w-4xl mx-auto px-6 md:px-12 lg:px-24 space-y-24 text-xl md:text-2xl leading-relaxed text-gray-900">

        {/* 1. INNLEIING */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">1. Innleiing</h2>
          <p className="mb-12">
            I magasinet til Nasjonalmuseet i Oslo står det ein stol registrert som <strong className="font-mono text-xl">OK-10330A</strong>, datert til om lag 1830. Materiallista er kort: mahogni, hestetagl, furu, eik, whitewood. For ein konvensjonell designhistorikar er dette ein anonym empirestol. Men materiallista er ikkje anonym. Ho er eit komprimert verdskart.
          </p>
          <p className="mb-12">
            Mahognien kjem frå tropiske regnskogar i Karibia, felt av tvangsarbeidande menneske under det britiske kolonistyret. Hestetaglet — polstringsfyllet — vitnar om eit europeisk handverkssystem der animalske biprodukt vart omforma til komfort. Furu og eik er norske. Fem materialar frå minst tre kontinent, samla i éin norsk stol. Museumsmagasinet kan lesast som eit materialkurvediagram der kvar kurve representerer eit materiale si stiging og fall over tid.
          </p>
          <p className="mb-12">
            Denne artikkelen presenterer den fyrste systematiske, kvantitative materialanalysen av Nasjonalmuseet si stolsamling. Datasettet omfattar {data.length} stolar daterte frå 1280 til 2020 — frå den eldste norske gårastolen til samtidsdesign i resirkulert plast. Metoden eg kallar <em>materialkurveanalyse</em> kartlegg kva materialar som dominerer i kvar periode, korleis dei stig og fell, og kva desse kurvene avslører om geopolitiske maktforhold.
          </p>
          <p>
            Artikkelen argumenterer for at museumsmagasinet fungerer som eit <em>kolonialt arkiv</em> — ikkje i metaforisk forstand, men som ein empirisk observerbar materialstruktur. Kvar stol er eit materielt vitne om globale krinsløp. Å kvantifisere desse vitnemåla gjer designobjekt lesbare som geopolitisk historie.
          </p>
        </section>

        {/* 2. DATASETT OG METODE */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">2. Datasett og metode</h2>
          <p className="mb-12">
            Datasettet er konstruert frå Nasjonalmuseet sin digitale katalog. Kvart objekt er registrert med inventarnummer, datering, produksjonsstad, materialar, teknikkar, og dimensjonar. Eg har filtrert for stolar produserte i Noreg, noko som gjev eit utval på {data.length} objekt. Materiallister er normaliserte og splitta i individuelle materialar for kvantitativ samanlikning.
          </p>
          <p className="mb-12">
            Metoden har tre steg. Fyrst: <em>materialtelling</em> — kvar stol sin materialliste vert dekomponert i individuelle materialar, og frekvensen av kvart materiale vert talt opp per tidsperiode. Deretter: <em>kurvekonstruksjon</em> — materialfrekvensane vert plotta over tid for å synleggjere stiging, dominans og fall. Til slutt: <em>geopolitisk lesing</em> — kurvene vert tolka i lys av handelshistorie, kolonialisme og industrialisering.
          </p>
          <p>
            Ein slik metode er inspirert av Franco Moretti sitt omgrep <em>distant reading</em> — å lese ikkje éin tekst, men tusen; ikkje éin stol, men hundre. Mønstra som oppstår i det kvantitative blikket er usynlege for den som berre ser på enkeltobjektet.
          </p>
        </section>

        {/* FIGUR 1: Materialfrekvens */}
        <section className="py-12 full-bleed">
          <div className="bg-gray-50 p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] border border-gray-100 overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 1: Dei {topMaterials.length} mest brukte materiala (absolutt frekvens)</h4>
            <div className="h-[300px] md:h-[500px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topMaterials} layout="vertical" margin={{ left: 20, right: 40 }}>
                  <CartesianGrid strokeDasharray="2 2" horizontal={false} stroke="#e5e5e5" />
                  <XAxis type="number" hide />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={120}
                    tick={{ fontSize: 12, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    cursor={{ fill: '#fafafa' }}
                    contentStyle={{ borderRadius: '0px', border: '1px solid #000', boxShadow: 'none', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                    formatter={(value: number) => [`${value} stolar`, 'Tal']}
                  />
                  <Bar dataKey="value" fill="#000" radius={0} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-400 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Bjørk dominerer med {topMaterials[0]?.value} registreringar, følgd av bøk og lær. Mahogni er det sjuande mest brukte materialet.
            </p>
          </div>
        </section>

        {/* 3. FIRE MATERIALREGIME */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">3. Fire materialregime</h2>
          <p className="mb-12">
            Materialkurveanalysen avdekkjer fire distinkte regime i den norske stolhistoria. Kvart regime er definert av eit dominerande materialsett som reflekterer ein bestemt teknologisk og geopolitisk orden.
          </p>
          <div className="space-y-16 my-16 border-l-4 border-black pl-12">
            <div>
              <h3 className="font-sans font-black text-lg uppercase tracking-tight mb-3">I. Det lokale treregime (1280–1650)</h3>
              <p className="text-xl leading-relaxed text-gray-700">
                Furu, bjørk, eik, ask. Alle materialar er av lokal eller nordisk opphav. Stolen er eit produkt av sin eigen skog. Gårastolen — den eldste typen i samlinga — er skoren i massivt tre, utan polstring, utan importerte element. Materiallista er eit spegel av landskapet: kvart materiale kan sporast til ein radius på under hundre kilometer frå verkstaden.
              </p>
            </div>
            <div>
              <h3 className="font-sans font-black text-lg uppercase tracking-tight mb-3">II. Den tidlege importfasen (1650–1750)</h3>
              <p className="text-xl leading-relaxed text-gray-700">
                Lær, messing, tekstil, silke. Nye materialar frå kontinentet og den vidare verda byrjar å dukke opp. Lær kjem frå garveri knytta til europeisk storfeøkonomi. Messing — ein legering av kopar og sink — krev malmimport og smelteverksteknologi. Stolen vert eit objekt som kryssar grenser, men enno ikkje kontinent.
              </p>
            </div>
            <div>
              <h3 className="font-sans font-black text-lg uppercase tracking-tight mb-3">III. Det koloniale regimet (1750–1900)</h3>
              <p className="text-xl leading-relaxed text-gray-700">
                Mahogni, hestetagl, bøk. Mahogni — <em>Swietenia</em> — frå Karibia og Mellom-Amerika dominerer overflata. Hestetagl vert standardfyllet i polstring. Denne fasen markerer eit radikalt brot: for fyrste gong er den norske stolen ein direkte materiell konsekvens av transatlantisk kolonialisme. Mahognihandelen var uløyseleg knytt til slaveriet — hogsten skjedde på plantasjar drivne av tvangsarbeid.
              </p>
            </div>
            <div>
              <h3 className="font-sans font-black text-lg uppercase tracking-tight mb-3">IV. Det industrielle regimet (1900–2020)</h3>
              <p className="text-xl leading-relaxed text-gray-700">
                Kryssfiner, stål, plast, skumgummi. Materiala er ikkje lenger naturlege, men industrielt transformerte. Kryssfiner — bjørk eller bøk limte i kryssande lag — markerer overgangen frå handverk til industriell produksjon. Arne Jacobsen, Alvar Aalto og norske Westnofa-designarar arbeidde alle i dette materialspråket. Plast, som dukkar opp etter 1960, er petroleumsbasert og representerer ein ny type global materialøkonomi — ikkje kolonial, men petrokjemisk.
              </p>
            </div>
          </div>
        </section>

        {/* FIGUR 2: Geografisk fordeling */}
        <section className="py-12 full-bleed">
          <div className="bg-white p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] border border-gray-100 shadow-sm overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 2: Geografisk fordeling av produksjon</h4>
            <div className="h-[300px] md:h-[600px]">
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
              Analysen viser ei kraftig klynging i Sunnmøre og Oslo-regionen — to distinkte produksjonsgeografiar.
            </p>
          </div>
        </section>

        {/* 4. MAHOGNIENS BOGE */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">4. Mahogniens boge</h2>
          <p className="mb-12">
            Hovudfunnet i denne studien er <strong>mahogniens boge</strong>. Mahogni er fråverande i samlinga før 1700. Deretter stig kurva brått, og i perioden 1800–1849 inneheld over 80 % av alle registrerte stolar mahogni. Så kollapsar kurva — etter 1900 forsvinn mahogni nesten heilt. Denne bogen er ikkje ein designtrend. Han er ein materiell biografi om den transatlantiske slaveriøkonomien.
          </p>
          <p className="mb-12">
            Kronologien er presis. Den britiske mahogniimporten frå Jamaica og Honduras tok til rundt 1720 og kulminerte mellom 1780 og 1830. Den norske kurva følgjer den britiske med ei forsinking på om lag 25–50 år. Dette tidsgapet er ikkje tilfeldig — det reflekterer Noreg sin posisjon som ein perifer aktør i den europeiske luksushandelen. Norske snekkarar fekk tilgang til mahogni etter at prisane hadde stabilisert seg og britiske importørar hadde etablert stabile forsyningskjeder.
          </p>
          <p className="mb-12">
            Kollapsen er like talande som oppstiginga. Mahogniskogane i Karibia var nesten utrydda rundt 1850. Samstundes auka kostnadene ved transatlantisk transport. Den norske mahognibogen — frå null til dominans til forsvinning — er ein perfekt materiell avtrykk av det Anderson (2012) kallar «the costs of luxury»: ein global verdikjede der skogen på Jamaica vart til eleganse i Kristiania.
          </p>
          <p>
            Nasjonalmuseet sitt magasin plasserer seg slik som ein perifer node i eit globalt handelsnettverk som knyter jamaicanske regnskogar og norske snekkarverkstader saman. Å opne skuffa til ein norsk empirestol er å opne eit kolonialt arkiv.
          </p>
        </section>

        {/* FIGUR 3: Materialkurver temporal analyse */}
        <section className="py-12 full-bleed">
          <div className="bg-black p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#333_1px,transparent_1px)] [background-size:30px_30px]" />
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.6em] text-gray-600 mb-20 text-center">FIGUR 3: Materialkurver 1280–2020 (% av stolar per 25-årsperiode)</h4>
            <div className="h-[300px] md:h-[600px]">
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
                  <Area type="stepAfter" dataKey="eik" stackId="1" stroke="#aaa" fill="#666" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="furu" stackId="1" stroke="#888" fill="#444" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="bjørk" stackId="1" stroke="#777" fill="#333" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="stål" stackId="1" stroke="#555" fill="#222" fillOpacity={1} />
                  <Area type="stepAfter" dataKey="plast" stackId="1" stroke="#444" fill="#111" fillOpacity={1} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* 5. MATERIELL DOBBELTHEIT */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">5. Materiell dobbeltheit</h2>
          <p className="mb-12">
            Norskproduserte stolar opprettheld ein <strong>materiell dobbeltheit</strong> gjennom heile den koloniale perioden. Importert mahogni fungerer som overflate — det synlege, det estetiske — medan lokal furu og bjørk utgjer den berande strukturen. Denne dobbeltstrukturen er ikkje berre ein produksjonsteknikk. Det er ein materiell strategi.
          </p>
          <p className="mb-12">
            Tala stadfester dette: i perioden 1800–1849 inneheld 80 % av stolane mahogni, men samstundes inneheld mange av dei same stolane furu eller bjørk som sekundærmateriale. Stolen er <em>kolonialt finert</em> — eit tynt lag globalt prestisjetømmer over ein kropp av norsk skog. Denne konstruksjonen er eit perfekt materiellt uttrykk for det Ingold (2007) kallar «the surface and the depth»: overflata fortel éi historie (eleganse, kosmopolitisme, rikdom), djupet ei anna (lokal ressurs, handverkskontinuitet, pragmatisme).
          </p>
          <p className="mb-12">
            Denne dualiteten reflekterer Noreg sin økonomiske posisjon. Som ein semi-perifer økonomi i det europeiske systemet hadde norske snekkarar tilgang til koloniale materialar, men ikkje råd til å bruke dei gjennomgåande. Resultatet er ein hybrid materialitet som er unik for den nordiske periferien — ein stol som er både kolonial og lokal, importert og heimleg, global og intim.
          </p>
          <p>
            Den materielle dobbeltheita forsvinn gradvis etter 1880, når mahogniforsyningane tørkar ut og nye materialar — kryssfiner, bugna bøk, stålrøyr — tilbyr eit materialspråk som ikkje krev koloniale forsyningskjeder. Den industrielle stolen er ikkje lenger finert. Han er gjennomgåande éitt materiale, frå overflate til struktur.
          </p>
        </section>

        {/* FIGUR 4: Materialdiversitet over tid */}
        <section className="py-12 full-bleed">
          <div className="bg-gray-50 p-12 lg:p-24 rounded-[4rem] border border-gray-100 overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">FIGUR 4: Materialdiversitet over tid (unike materialar per 50-årsperiode)</h4>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={materialDiversity} margin={{ left: 20, right: 40 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#e5e5e5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} />
                  <YAxis tick={{ fontSize: 10, fontFamily: 'ui-monospace, monospace', fontWeight: '900', fill: '#000' }} />
                  <Tooltip
                    contentStyle={{ borderRadius: '0px', border: '1px solid #000', boxShadow: 'none', fontFamily: 'ui-monospace, monospace', fontSize: '12px', fontWeight: '900' }}
                    formatter={(value: number, name: string) => {
                      if (name === 'unike') return [`${value} materialar`, 'Unike materialar']
                      if (name === 'stolar') return [`${value}`, 'Tal stolar']
                      return [value, name]
                    }}
                  />
                  <Legend verticalAlign="top" height={40} wrapperStyle={{ fontFamily: 'ui-monospace, monospace', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: '900' }} />
                  <Line type="monotone" dataKey="unike" stroke="#000" strokeWidth={3} dot={{ fill: '#000', r: 5 }} name="Unike materialar" />
                  <Line type="monotone" dataKey="stolar" stroke="#999" strokeWidth={2} dot={{ fill: '#999', r: 4 }} strokeDasharray="5 5" name="Tal stolar" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-16 text-sm text-gray-400 font-mono font-bold text-center px-12 uppercase tracking-widest leading-relaxed">
              Materialdiversiteten eksploderer i den koloniale perioden og held seg høg inn i industrialderen.
            </p>
          </div>
        </section>

        {/* 6. DEN INDUSTRIELLE VENDINGA */}
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">6. Den industrielle vendinga</h2>
          <p className="mb-12">
            Etter 1900 skjer eit nytt materiellt brot — like djupgripande som mahogniinntoget, men med motsett logikk. Der den koloniale stolen var samansett av globale fragment, strevar den industrielle stolen mot <em>materiell einskap</em>. Éin stol, eitt materiale, éin prosess.
          </p>
          <p className="mb-12">
            Kryssfiner vert nøkkelmaterialet. Teknologien — å lime tynne lag tre i kryssande fiberretning — gjer det mogleg å forme bjørk og bøk i kurver som massivt tre ikkje kan oppnå. Alvar Aalto, Charles og Ray Eames, og den norske Westnofa-fabrikken utforskar alle kryssfinerens plastisitet. Materialet er demokratisk: det er billegare enn mahogni, sterkare enn massiv furu, og kan produserast industrielt.
          </p>
          <p className="mb-12">
            Stål — i form av rør og profil — kjem inn i stoldesignet via Bauhaus og den kontinentale modernismen. Marcel Breuer sin Wassily-stol (1925) er det ikoniske eksempelet. I den norske samlinga dukkar stål opp sporadisk frå midten av 1900-talet, men forblir eit minoritetsmateriale. Noreg sin stolproduksjon er for tett knytt til treet — til skogen, til handverkstradisjonen, til den nordiske materialidentiteten.
          </p>
          <p>
            Plast, det siste store materialet, representerer eit nytt paradigme. Der mahogni var eit naturprodukt med kolonial biografi, er plast eit syntetisk produkt med petrokjemisk biografi. Den geopolitiske logikken skiftar frå regnskogar til oljefelt, frå tvangsarbeid til raffineriprosessar. Plaststolen etter 1960 — Verner Panton sin S-stol, Joe Colombo sine eksperiment — er den fyrste stolen der <em>heile objektet</em> er eitt materiale, frå rygg til bein.
          </p>
        </section>

        {/* 7. PRODUKSJONSGEOGRAFI */}
        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">7. Produksjonsgeografi</h2>
          <p className="mb-12">
            Materialhistoria har også ein romleg dimensjon. Figur 2 viser at stolproduksjonen i Nasjonalmuseet si samling er geografisk konsentrert i to klynger: Sunnmøre (med Sykkylven og omland som sentrum) og Oslo-regionen (Kristiania). Desse to klynjene representerer to ulike produksjonslogikkar.
          </p>
          <p className="mb-12">
            Oslo-klynga er den eldre. Her finn vi empirestolane med mahogni, dei polstra salongsalstolane, stolane som vitnar om hovudstaden sin kosmopolitiske orientering mot europeisk smak. Materiala er importerte, handverket er fint, og kundane er borgarlege.
          </p>
          <p className="mb-12">
            Sunnmøre-klynga er den yngre, men kvantitativt dominerande. Sykkylven vart eit sentrum for industriell stolproduksjon frå tidleg 1900-tal, med fabrikkar som Westnofa, Brunstad og Ekornes. Materiala skiftar frå mahogni til kryssfiner, skumgummi og tekstil. Produksjonslogikken skiftar frå snekkarverkstad til fabrikk, frå einskildbestilling til serieproduksjon.
          </p>
          <p>
            Desse to klynjene — Kristiania og Sykkylven — kartlegg eit historisk skift frå <em>kolonial luksus</em> til <em>industriell demokratisering</em>. Det same skiftet kan lesast i materialkurvene: frå mahogni til kryssfiner, frå import til lokal skog, frå aristokratisk overflod til folkelig funksjonalisme.
          </p>
        </section>

        {/* 8. DISKUSJON */}
        <section>
          <h2 className="text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">8. Diskusjon</h2>
          <p className="mb-12">
            Kva betyr det å lese eit museumsmagasin som eit materialkurvediagram? Det betyr å flytte blikket frå det estetiske til det materielle, frå forma til stoffet, frå stolen som designobjekt til stolen som <em>geopolitisk indikator</em>. Materialvalet er aldri nøytralt. Det er alltid ein konsekvens av kva som er tilgjengeleg, kva som er overkommeleg, og kva som er ønskjeleg — og desse tre faktorane er forma av globale maktstrukturar.
          </p>
          <p className="mb-12">
            Tim Ingold (2007) har argumentert for at vi bør studere <em>materialar</em> framfor <em>materialitet</em> — det konkrete framfor det abstrakte, flyten framfor tingen. Materialkurveanalysen tek denne oppmodinga på alvor. Kurva for mahogni er ikkje ei abstrakt linje — ho er ein materiell straum som flyt frå Karibia gjennom London til Kristiania, driven av etterspurnad, formidla av imperiale handelsstrukturar, og stoppa av utarming av naturressursar.
          </p>
          <p className="mb-12">
            Adam Bowett (2012) sin studie av tømmersortar i britisk møbelproduksjon gjev eit komparativt grunnlag. Den britiske mahognikurva når toppen tidlegare enn den norske — rundt 1780 versus rundt 1830. Denne forskyvinga på eit halvt hundreår er i seg sjølv eit funn: det viser at Noreg ikkje var eit sjølvstendig estetisk senter, men ein konsument av britiske materialmotar med ei generasjons forsinking.
          </p>
          <p>
            Moretti (2005) sin metode — å sjå mønstre i aggregat framfor å nærles enkelttekstar — er direkte overførbar til materialhistorie. Éin stol fortel lite om globale handelsmønstre. Hundre stolar, kvantifiserte og plotta over tid, avslører strukturar som er usynlege i det individuelle objektet. Materialkurva er designhistoria sin ekvivalent til den litterære grafen.
          </p>
        </section>

        {/* KONKLUSJON */}
        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
            <p>
              Materialkurveanalyse gjer designobjekt lesbare som geopolitisk historie. Kvar kurve — mahogni si dramatiske boge, furu sin stabile grunn, stål si seinmoderne inntreden, plast sin petrokjemiske framvekst — fortel ei historie om makt, handel, utvinning og transformasjon.
            </p>
            <p>
              Nasjonalmuseet sitt magasin fungerer som eit kolonialt arkiv der kvar stol ber vitne om globale materialkrinslop. Dei {data.length} stolane i denne studien spenner over 740 år — frå den lokale gårastolen i massiv furu til empirestolen finert i karibisk mahogni til den industrielle stolen forma i norsk kryssfiner til plaststolen støypt av petroleum.
            </p>
            <p>
              Denne rekkja er ikkje berre ein materialhistorisk progresjon. Det er ein geopolitisk biografi: frå det lokale til det koloniale, frå det koloniale til det industrielle, frå det industrielle til det petrokjemiske. Avstanden mellom ein gárastol frå 1280 og ein empirestol frå 1830 er avstanden mellom ein lokal og ein global materialøkonomi.
            </p>
            <p className="text-black not-italic font-sans font-black text-3xl leading-tight tracking-tight">
              Å kvantifisere denne avstanden er ei naudsynt oppgåve for designhistoria — og materialkurva er verktøyet.
            </p>
          </div>
        </section>
      </article>

      {/* Referansar */}
      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Anderson, J. L. (2012). <em className="normal-case tracking-normal">Mahogany: The Costs of Luxury in Early America.</em> Harvard University Press.</p>
          <p>Bowett, A. (2012). <em className="normal-case tracking-normal">Woods in British Furniture-Making 1400–1900: An Illustrated Historical Dictionary.</em> Oblong.</p>
          <p>Eames, C. & Eames, R. (1958). <em className="normal-case tracking-normal">The India Report.</em> National Institute of Design.</p>
          <p>Ingold, T. (2007). Materials against materiality. <em className="normal-case tracking-normal">Archaeological Dialogues,</em> 14(1), 1–16.</p>
          <p>Moretti, F. (2005). <em className="normal-case tracking-normal">Graphs, Maps, Trees: Abstract Models for Literary History.</em> Verso.</p>
          <p>Pye, D. (1968). <em className="normal-case tracking-normal">The Nature and Art of Workmanship.</em> Cambridge University Press.</p>
          <p>Schwartz, S. B. (2004). <em className="normal-case tracking-normal">Tropical Babylons: Sugar and the Making of the Atlantic World, 1450–1680.</em> University of North Carolina Press.</p>
          <p>Wilk, C. (1996). <em className="normal-case tracking-normal">Western Furniture: 1350 to the Present Day.</em> V&A Publications.</p>
        </div>
        <div className="mt-20 pt-12 border-t border-gray-100">
          <p className="text-[10px] font-mono font-black uppercase tracking-[0.3em] text-gray-300 mb-8">Sjaa ogsa</p>
          <button
            onClick={() => router.push('/article/form')}
            className="text-lg font-sans font-black tracking-tight hover:line-through transition-all"
          >
            Del II: Form follows fitness. &rarr;
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
