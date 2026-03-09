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
} from "recharts"

interface ChairItem {
  id: string
  year: string
  materials: string
  location: string
}

export default function ArticleOnePage() {
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

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> Artikkelen presenterer den fyrste systematiske kvantitative materialanalysen av Nasjonalmuseet si stolsamling (n = 461), som spenner frå 1280 til 2020. Gjennom eit nytt strukturert datasett undersøkjer studien korleis materialkurver fungerer som eit kolonialt arkiv. Hovudfunnet er <em>mahogniens boge</em>: ein materiell signatur der karibisk tropisk hardved stig frå null til 86 % av alle registrerte stolar i perioden 1825–1849, for deretter å kollapse.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing</h2>
        <p>
          I magasinet til Nasjonalmuseet i Oslo står det ein stol registrert som <strong>OK-10330A</strong>, datert til om lag 1830 og produsert i Noreg. Materiallista er kort: mahogni, hestetagl, furu, eik, whitewood. Teknikkane er tapping og polstring. Stolen er 78 cm høg, 45,5 cm brei og 50 cm djup, med ei setehøgd på 47,5 cm. For ein konvensjonell designhistorikar er dette ein anonym empirestol utan tilskriven snikkar, ein av many i eit museum som tel over 50 000 objekt. Men materiallista er ikkje anonym. Ho er eit komprimert verdskart.
        </p>
        <p>
          Mahognien kjem frå tropiske regnskogar i Karibia eller Mellom-Amerika, felt av tvangsarbeidande menneske under det britiske kolonistyret og frakta over Atlanterhavet som ei vare i eit handelsnettverk som omsette sukker, slavar og tømmer i same rørsle (Anderson, 2012). Hestetaglet, brukt som polstringsmateriale, knyter stolen til europeiske leverandørkjeder for animalske fiber. Furu og eik er norske: dei veks i skogane som omgir snekkarverkstaden. Og whitewood, eit uspesifisert lyst treslag brukt som blindtre under mahognioverflata, er det usynlege fundamentet som held den koloniale fasaden oppe. Fem materialar frå minst tre kontinent, samla i éin norsk stol.
        </p>
        <p>
          Denne artikkelen tek utgangspunkt i ein enkel observasjon: Dersom kvar stol i ei museumssamling ber ei slik materialliste, og dersom ein kan strukturere desse listene som kvantitative data, då er det mogleg å lese museumsmagasinet som eit materialkurvediagram der kvar kurve representerer eit materiale si stiging og fall over tid. Metoden eg kallar <em>materialkurveanalyse</em> er ikkje ny i prinsippet — Moretti (2005) sin <em>distant reading</em> og Manovich (2020) sin <em>cultural analytics</em> har demonstrert verdien av kvantifisering i humaniora — men han er ikkje tidlegare systematisk brukt på museumssamlingar av brukskunst.
        </p>
        <p>Spesifikt stillar artikkelen tre forskingspørsmål:</p>
        <ol>
          <li>Korleis fordeler materialar seg over tid i Nasjonalmuseet si stolsamling, og kva historiske prosessar gjer desse fordelingane synlege?</li>
          <li>I kva grad fungerer mahogni sin materialkurve som ein proxy for norsk deltaking i den transatlantiske koloniøkonomien?</li>
          <li>Finst det ein systematisk <em>materiell dobbeltheit</em> i norskproduserte stolar, der importerte og lokale materialar sameksisterer i same objekt?</li>
        </ol>
      </section>

      <section>
        <h2>2. Forskingsgjennomgang</h2>
        <h3>2.1 Materialitet og tingteori</h3>
        <p>
          Materialitet som analytisk kategori har gjennomgått ei radikal omvurdering dei siste tre tiåra. Appadurai (1986) og Kopytoff (1986) etablerte at ting har sosiale biografiar som endrar seg når dei flyttar seg mellom kontekstar. Ingold (2007) kritiserte det han kalla <em>materials against materiality</em> — tendensen til å abstrahere materialar til diskursive kategoriar i staden for å studere dei som aktive, transformerande stoff. Bennett (2010) utvida dette til ein <em>vibrant materialism</em> der ting har agens uavhengig av menneskeleg intensjon. Pels (2002) argumenterte for at objekt medierer sosiale relasjonar gjennom sin materielle konfigurasjon, ikkje berre gjennom sin symbolverdi.
        </p>
        <p>
          For designhistorie har denne vendinga konsekvensar. Dersom materialar er aktive aktørar, då er eit materialval ikkje berre eit estetisk eller økonomisk val, men ein posisjonering i eit nettverk av utvinning, transport, handel og makt. Mahogni i ein norsk stol frå 1830 er ikkje berre ein trevariant; det er ein kondensert kolonirelasjon.
        </p>

        <h3>2.2 Kvantitative metodar i kulturhistoria</h3>
        <p>
          Moretti (2005, 2013) demonstrerte at kvantifisering av store tekstkorpus — det han kalla <em>distant reading</em> — avdekte mønster som er usynlege på nivået av enkeltverket. Manovich (2020) utvida dette til visuell kultur. Drucker (2014) påpeika at visualiseringsmetodar ikkje er nøytrale representasjonar, men <em>generative</em> — dei produserer kunnskap gjennom sine visuelle konvensjonar.
        </p>

        <h3>2.3 Norsk designhistorie</h3>
        <p>
          Norsk designhistorie har tradisjonelt vore skriven som ein kvalitativ disiplin fokusert på individuelle designarar og ikoniske objekt. Wildhagen (1988) si breie oversikt over norsk kunsthåndverk og design under industrikulturen, Opstad (2005) si jubileumsbok for Kunstindustrimuseet, og Halén (2003) og Wickman (2006) sine komparative skandinaviske studiar representerer denne tradisjonen. Kvantitative materialtilnærmingar er fråverande i denne litteraturen.
        </p>
      </section>

      <section>
        <h2>3. Metode og datasett</h2>
        <h3>3.1 Datainnsamling</h3>
        <p>
          Datasettet er bygd i to lag. Det fyrste laget er ei programmatisk uthenting av alle objekt klassifiserte som "stol" i Nasjonalmuseet si DigitaltMuseum-samling via KulturIT sitt API (2024). Uthentinga resulterte i 461 unike stol-objekt med metadata inkludert objekt-ID, tittel, datering, produksjonsstad, materialliste, teknikk, dimensjonar og biletelenker.
        </p>
        <p>
          Det andre laget er eit handkurert underdatasett på 135 norskproduserte stolar, der kvar stol er supplert med 25 strukturerte metadatafelt og, der tilstrekkeleg referansemateriale finst, ein tredimensjonal modell i GLB-format. Til saman er 128 slike modellar produserte.
        </p>

        <h3>3.2 Materialkurveanalyse</h3>
        <p>
          For kvar stol i datasettet er materiallista parsa til individuelle materialar. Desse er deretter aggregerte i 25-årsperiodar basert på dateringsinformasjon. For kvar periode er kvar materialtype tald som ein binær variabel (til stades/ikkje til stades) og uttrykt som prosentdel av totalt tal stolar i perioden. Resultatet er <em>materialkurver</em>: tidsseriar som viser kvart materiale si relative hyppigheit over tid.
        </p>

        <h3>3.3 Avgrensingar</h3>
        <p>
          Datasettet speglar Nasjonalmuseet sin innkjøpspolitikk, ikkje norsk møbelproduksjon som heilskap. Museet har systematisk prioritert kunstindustrielle objekt og gjenstandar med kjend proveniens. Dateringane er i mange tilfelle estimat. Materiallister i museumskatalogar er heller ikkje standardiserte. Trass i desse avgrensingane er datasettet det største strukturerte materialdatasettet for norsk stoldesign som finst.
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
        <h2>4. Resultat</h2>
        <h3>4.1 Materialkurver: eit oversyn</h3>
        <p>
          Figur 2 viser materialkurvene for dei sju mest framtredande materialgruppene i dei 135 norskproduserte stolane. Kurva avdekkjer tre distinkte regime:
        </p>
        <ol>
          <li><strong>Det lokale regimet (1200–1700):</strong> Furu, bjørk og eik dominerer. Alle materialar er kortreiste og reflekterer ein lokal handverksøkonomi.</li>
          <li><strong>Det koloniale regimet (1700–1875):</strong> Mahogni stig dramatisk, når ein topp på 93 % i perioden 1825–1850, og kollapsar deretter. Bøk (eit europeisk importtre) følgjer eit liknande, men seinare, mønster.</li>
          <li><strong>Det industrielle regimet (1875–2005):</strong> Stål, kryssfiner og nye komposittar erstattar dei tradisjonelle materialane. Mangfaldet aukar.</li>
        </ol>

        <h3>4.2 Mahogniens boge</h3>
        <p>
          Det mest slåande enkeltfunnet er mahogni sin materialkurve. Mahogni er fråverande før 1700, stig til 93 % i perioden 1825–1850, og forsvinn nesten fullstendig etter 1875. Denne kurva er ikkje eit norsk fenomen. Ho er ein lokal manifestasjon av den transatlantiske mahognihandelen. Anderson (2012) dokumenterer korleis karibisk mahogni vart den dominerande møbeltreslaget i det britiske imperiet frå om lag 1720. Den norske kurva følgjer den britiske med ein forsinkelse på om lag 25–50 år.
        </p>
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
        <h3>4.3 Materiell dobbeltheit</h3>
        <p>
          Av dei 24 mahogni-stolane i det norskproduserte delsettet er 10 (42 %) konstruerte med ein kombinasjon av importert mahogni og lokalt tre (furu, bjørk, eik eller gran). Mahognien fungerer som overflatemateriale — ryggbrett, armlen, frontben — medan det lokale treet utgjer blindtre, bakben og berande innvendig struktur.
        </p>
        <p>
          Denne materielle dobbeltheita skil norske stolar frå britiske ekvivalentar, der mahogni typisk vert brukt gjennomgåande (Bowett, 2012). Den norske stolen er <em>kolonialt finert</em>: ein materiell strategi der globalt prestisjetømmer og lokal handverkstradisjon sameksisterer i same objekt.
        </p>

        <h3>4.4 Dimensjonsutvikling</h3>
        <p>
          Dimensjonsutviklinga i norskproduserte stolar syner ein konvergens mot standardiserte dimensjonar etter industrialiseringa. Dette vert drøfta vidare i Artikkel II.
        </p>
      </section>

      <section>
        <h2>5. Diskusjon</h2>
        <h3>5.1 Museumsmagasinet som kolonialt arkiv</h3>
        <p>
          Mahogniens boge demonstrerer at Nasjonalmuseet sitt magasin, utan intensjon, fungerer som eit kolonialt arkiv. Kvart mahogniobjekt er eit materielt bevis på norsk deltaking i den transatlantiske økonomien. At 93 % av alle registrerte norskproduserte stolar i perioden 1825–1850 inneheld mahogni, tyder på at dette ikkje er eit marginalt fenomen; det er den dominerande materielle realiteten i norsk møbelhandverk i denne æraen.
        </p>

        <h3>5.2 Materialkurveanalyse som metode</h3>
        <p>
          Materialkurveanalyse — systematisk kvantifisering av materialfordeling over tid i museumssamlingar — viser seg å vere ein produktiv metode. Styrken ligg i evna til å avdekke mønster som er usynlege på enkeltverknivå. Ingen enkelt stol fortel historia om mahogniens boge; ho vert synleg fyrst når 135 objekt vert aggregerte. Dette er ein direkte parallell til Moretti (2005) sin observasjon om at <em>distant reading</em> avdekkjer strukturar som <em>close reading</em> ikkje kan sjå.
        </p>

        <h3>5.3 Den materielle dobbeltheitens geopolitikk</h3>
        <p>
          Den norske strategien med å finere kolonialt tømmer over lokal furu er ein materiell kompromissposisjon. Noreg var ikkje ein kolonimakt, men ein perifer deltakar i kolonihandelen. Stolen OK-10330A ber dette i sin materialstruktur: mahogni utanpå, furu inni. Den koloniale relasjonen er bokstavleg innebygd i objektet.
        </p>
      </section>

      <section className="border-t-[10px] border-black pt-24">
        <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
        <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
          <p>
            Denne artikkelen har presentert tre hovudfunn. For det fyrste: Mahogniens boge er ein kvantitativ manifestasjon av den transatlantiske kolonihandelen lest gjennom eit norsk museumsmagasin. For det andre: Norskproduserte stolar opprettheld ein materiell dobbeltheit som ein materiell strategi. For det tredje: Materialkurveanalyse er ein underutnytta metode i designhistoria som kan gjere materiell kultur lesbar som geopolitisk historie.
          </p>
          <p>
            Avstanden mellom Gårastolen (1280) og empirestolen (1830) er ikkje berre tid; det er avstanden mellom ein lokal og ein global materialøkonomi. Å kvantifisere den avstanden er ei naudsynt oppgåve for designhistoria.
          </p>
        </div>
      </section>

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
