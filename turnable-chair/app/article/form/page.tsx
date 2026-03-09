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
  ZAxis,
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
  const volumeScatter = useMemo(() => withDims.map(d => ({ 
    year: d.fra_aar!, 
    volume: Math.round((d.hoegde_cm! * d.breidde_cm! * d.djupn_cm!) / 1000),
    id: d.object_id
  })), [withDims])

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
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">
            Institutt for design, Arkitektur- og designhøgskolen i Oslo (AHO)
          </p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Formkurveanalyse</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed">
            Kvantitativ analyse av dimensjonar over 740 år med stoldesign.
          </p>
        </div>
      </div>

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> Denne artikkelen introduserer <em>form follows fitness</em> som eit evolusjonært rammeverk for å analysere formutvikling i industridesign, med Nasjonalmuseet si stolsamling som empirisk grunnlag. Mot Le Corbusier sin maskinanalogi og Sullivan sitt "form follows function" set artikkelen ein tredje posisjon: form fylgjer ikkje funksjon som eit logisk resultat, men <em>fitness</em> som eit seleksjonstrykk. Hovudfunnet er <em>fitness-konvergensen</em>: ein empirisk demonstrerbar tendens der stolar frå ulike stilperiodar konvergerer mot eit felles dimensjonsområde etter industrialiseringa.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing: Problemet med "form follows function"</h2>
        <p>
          I 1896 skreiv Louis Sullivan at "form ever follows function" (Sullivan, 1896). Setninga vart eit aksiom. Le Corbusier radikaliserte ho i 1923: Huset er "une machine à habiter" — ein maskin til å bu i (Corbusier, 1923). Maskinen har ingen overflødig form; kvar detalj tener ein funksjon. Designhistoria etter Le Corbusier har oscillert mellom å akseptere dette premisset og å reagere mot det, men sjeldan å erstatte det med eit meir presist alternativ.
        </p>
        <p>
          Problemet er empirisk. Dersom form fylgjer funksjon, burde alle stolar med same funksjon — å sitje på — ha same form. Det har dei ikkje. Nasjonalmuseet si samling av 407 stolar, som spenner frå 1280 til 2019, inneheld ei enorm formvariasjon: frå den massive Gårastolen i furu til Harry Bertoia sin Diamond Chair i sværs stål. Begge tener same grunnfunksjon. Formene er radikalt ulike. "Form follows function" kan ikkje forklare denne variasjonen.
        </p>
        <p>
          Le Corbusier sitt maskinparadigme har eit djupare problem. Ein maskin er designa; han er ikkje tilpassa. Skilnaden er avgjerande. Ein tilpassa gjenstand vert forma av eit miljø som selekterer mellom variantar. Darwin (1859) sin evolusjonsteori handlar ikkje om design, men om fitness: den differensielle overlevinga av variantar i eit gjeve miljø. Dennett (1995) kalla dette "Darwin si farlege idè" — idèen om at kompleks form kan oppstå utan ein designar, gjennom kumulativ seleksjon.
        </p>
        <p>
          Eg foreslår <em>form follows fitness</em> som eit rammeverk med tre premiss:
        </p>
        <ol>
          <li><strong>Form er ikkje determinert av funksjon.</strong> Same funksjon produserer many formar. Form er underdeterminert.</li>
          <li><strong>Form er selektert av fitness.</strong> Dei formene som overlever — som vert produsert, kjøpt, brukt, samla, kanonisert — er dei som er best tilpassa eit komplekst miljø av materielle, økonomiske, ergonomiske og kulturelle seleksjonstrykk.</li>
          <li><strong>Fitness er kvantifiserbar.</strong> Gjennom systematisk måling av formvariablar over tid kan ein identifisere konvergensar, divergensar og seleksjonslandskap empirisk.</li>
        </ol>
      </section>

      <section>
        <h2>2. Forskingsgjennomgang: Evolusjon og form</h2>
        <h3>2.1 Den biologiske analogien i designhistoria</h3>
        <p>
          Analogien mellom biologisk evolusjon og designutvikling er ikkje ny. Steadman (1979, 2008) skreiv det definitive verket om biologisk analogi i arkitektur og brukskunst, og viste at analogien har vore brukt sidan 1800-talet, men sjeldan systematisk. Thompson (1917) sin <em>On Growth and Form</em> demonstrerte at biologiske formar fylgjer matematiske prinsipp.
        </p>
        <p>
          Problemet med tidlegare forsøk er at dei typisk brukar analogien metaforisk, ikkje metrisk. Å seie at "stolar evolusjonerer" er ein metafor. Å vise at stolform konvergerer mot eit målbart optimum over tid er ein empirisk påstand som kan testast. Det er denne forskjellen — frå metafor til metrikk — som denne artikkelen forsøker.
        </p>

        <h3>2.2 Computational design history</h3>
        <p>
          Manovich (2020) etablerte <em>cultural analytics</em> som ein disiplin der store kulturelle datasett vert analyserte med kvantitative metodar. Moretti (2005) si <em>distant reading</em> viste at mønster i litteraturhistoria vert synlege fyrst når enkeltverket vert bytt ut med aggregatet. Innanfor arkitektur og design har Oxman (2006, 2017) kartlagd korleis digitale verktøy transformerer både designprosessen og den teoretiske refleksjonen over form.
        </p>

        <h3>2.3 Frå "form follows function" til "form follows fitness"</h3>
        <p>
          Sullivan sin formulering og Le Corbusier sin maskinanalogi deler eit premiss: at form er <em>determinert</em> av noko anna. Pye (1968) var mellom dei fyrste som eksplisitt utfordra dette. <em>Form follows fitness</em> byggjer på Pye, men går vidare. Det er heile det selektive miljøet — marknad, estetiske normer, materialtilfang, teknologi — som selekterer kva formar som overlever. Dei formene me ser i museumssamlinga er survivors.
        </p>
      </section>

      <section>
        <h2>3. Metode: 3D-formanalyse</h2>
        <h3>3.1 Datasettet</h3>
        <p>
          Studien byggjer på det utvida datasettet frå Finne (2026a): 407 stol-objekt frå Nasjonalmuseet. Av desse har 289 objekt (71 %) tilknytte 3D-modellar i GLB-format. Dimensjonsdata er tilgjengelege for 390 objekt (96 %).
        </p>
        <h3>3.2 Formvariablar</h3>
        <ul>
          <li><strong>Omsluttande volum (bounding box volume):</strong> Produktet av høgde, breidde og djupn, uttrykt i liter.</li>
          <li><strong>Geometrisk kompleksitet:</strong> Uttrykt som filstorleiken på GLB-modellen. GLB-formatet komprimerer mesh-data proporsjonalt med topologisk kompleksitet.</li>
          <li><strong>Materialmangfald:</strong> Tal distinkte materialar per stol.</li>
        </ul>
        <h3>3.3 Fitness som seleksjonsvariabel</h3>
        <p>
          I designhistorie foreslår eg ein analog definisjon: <em>Design-fitness er sannsynet for at ein formvariant vert reprodusert, kanonisert og bevart i ein gjeven historisk kontekst.</em> Nasjonalmuseet si samling er eit fitness-landskap der kvar stol representerer eit punkt som har overlevd seleksjonstrykket.
        </p>
      </section>

      <section className="not-prose my-32">
        <div className="bg-black p-8 md:p-12 lg:p-16 rounded-3xl shadow-2xl">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.6em] text-gray-600 mb-20 text-center">FIGUR 1: Omsluttande volum over tid (liter)</h4>
          <div className="h-[500px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ left: 20, right: 40, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#222" />
                <XAxis dataKey="year" type="number" domain={[1200, 2020]} stroke="#444" tick={{ fontSize: 10, fill: '#666' }} />
                <YAxis dataKey="volume" type="number" stroke="#444" tick={{ fontSize: 10, fill: '#666' }} unit="L" />
                <ZAxis range={[50, 50]} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#000', border: '1px solid #333', color: '#fff', fontSize: '10px' }} />
                <Scatter name="Stolar" data={volumeScatter} fill="#fff" fillOpacity={0.6} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section>
        <h2>4. Resultat</h2>
        <h3>4.1 Geometrisk kompleksitet over tid</h3>
        <p>
          GLB-filstorleik som ein proxy for geometrisk kompleksitet syner ein svak, men positiv korrelasjon mellom år og kompleksitet (r = 0,14). Spreiinga er stor, noko som tyder på at formkompleksitet ikkje er ein eintydig funksjon av tid, men av designstrategi.
        </p>
        <h3>4.2 Fitness-konvergensen: Omsluttande volum</h3>
        <p>
          Figur 1 er det sentrale funnet. Omsluttande volum viser ein tydeleg <strong>konvergens</strong> over tid: Frå ein stor spreiing i tidlege periodar mot eit smalare bånd etter om lag 1850. Moderne stolar konvergerer mot eit volum på om lag 150–300 liter, uavhengig av stilretning.
        </p>
        <p>
          Dette mønsteret er ein designhistorisk parallell til <em>konvergent evolusjon</em> i biologi. I stolens tilfelle er "miljøet" eit sett av seleksjonstrykk: ergonomi, produksjonseffektivitet, transportlogistikk og standardiserte bustadar.
        </p>
        <h3>4.3 Materialmangfald og formkompleksitet</h3>
        <p>
          Industrialiseringen standardiserte ikkje berre dimensjonar (konvergens), men diversifiserte òg materielle strategiar. Nyare stolar har fleire materialar og eit meir konsentrert kompleksitetsområde.
        </p>
      </section>

      <section>
        <h2>5. Diskusjon: Kvifor Le Corbusier tok feil</h2>
        <h3>5.1 Maskinen mot organismen</h3>
        <p>
          Le Corbusier sin maskinanalogi impliserer at design er ein deterministisk prosess. Men dataa viser at same funksjon (sitjing) produserer hundrevis av ulike formar. Forma er ikkje determinert; ho er selektert. Maskinen er feil metafor. Organismen er riktigare: stolform er resultatet av kumulativ tilpassing til eit komplekst miljø.
        </p>
        <h3>5.2 Fitness-konvergensen som empirisk bevis</h3>
        <p>
          Konvergensen i omsluttande volum er direkte bevis mot den postmoderne relativismen. Industrialiseringa innførte nye seleksjonstrykk som eliminerte mange tidlegare gyldige formar. Samstundes aukar den stilistiske divergensen — noko som viser at fitness ikkje er det same som uniformitet.
        </p>
        <h3>5.3 Implikasjonar for formgjevingsteori</h3>
        <p>
          Designaren er ikkje ein maskiningeniør som deduserer form frå funksjon. Designaren er ein som navigerer eit fitness-landskap — som forstår kva seleksjonstrykk som gjeld. Dette krev forståing av økologi, materialvitskap, ergonomi, økonomi og estetikk som samverkande seleksjonstrykk.
        </p>
      </section>

      <section className="border-t-[10px] border-black pt-24">
        <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
        <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
          <p>
            Denne artikkelen har introdusert <em>form follows fitness</em> som eit evolusjonært rammeverk for designhistorie. Fitness-konvergensen er eit empirisk funn som verken funksjonalismen eller postmodernismen kan forklare. Le Corbusier sin maskinanalogi er falsifisert av dataa. Maskinen bør erstattast av organismen som leiande analogi i formgjevingsteori.
          </p>
        </div>
      </section>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Corbusier, Le (1923). <em className="normal-case">Vers une architecture.</em> Cres.</p>
          <p>Darwin, C. (1859). <em className="normal-case">On the Origin of Species.</em> Murray.</p>
          <p>Dennett, D. C. (1995). <em className="normal-case">Darwin's Dangerous Idea.</em> Simon & Schuster.</p>
          <p>Finne, I. R. (2026a). <em className="normal-case">Materialhistorie: Kolonialt arkiv.</em> AHO Working Paper.</p>
          <p>Manovich, L. (2020). <em className="normal-case">Cultural Analytics.</em> MIT Press.</p>
          <p>Pye, D. (1968). <em className="normal-case">The Nature and Art of Workmanship.</em> Cambridge University Press.</p>
          <p>Steadman, P. (2008). <em className="normal-case">The Evolution of Designs.</em> Routledge.</p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case">Lippincott's Magazine.</em></p>
          <p>Thompson, D. W. (1917). <em className="normal-case">On Growth and Form.</em> Cambridge University Press.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
