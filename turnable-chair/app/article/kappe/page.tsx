"use client"

import { useRouter } from "next/navigation"
import ArticleLayout from "../../../components/article-layout"

export default function ArticleFivePage() {
  const router = useRouter()

  const header = (
    <div className="w-full">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">PhD-kappe</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Distribuert<br/>
        <span className="text-gray-200">intelligens.</span>
      </h1>
      <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight mt-8">
        Eit nytt paradigme for estetiske fag.
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
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Type</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">PhD-kappe</p>
        </div>
      </div>

      <div className="mt-16 py-8 border-t border-black">
        <p className="text-xl font-serif italic leading-relaxed text-black">
          <strong>Samandrag:</strong> I 130 år har estetiske fag operert under eit deterministisk aksiom: "form follows function". Denne kappa bind saman fire empiriske artiklar som til saman falsifiserer aksiomet og etablerer eit alternativ. Kappa formulerer Form Follows Fitness (FFF) som eit fullstendig paradigmeskifte der formgjeving vert forstått som ein distribuert intelligent prosess.
        </p>
      </div>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing: Ein revolusjon i fire akter</h2>
        <p>
          Denne avhandlinga starta med eit enkelt eksperiment: å stille Sullivan sitt aksiom "form ever follows function" (1896) på prøve mot eit reelt datasett. 461 stolar frå Nasjonalmuseet, alle med same funksjon, alle målte, dokumenterte og modellerte. Dersom aksiomet heldt, burde formvariasjonen vore liten. Ho var enorm.
        </p>
        <p>
          Denne kappa har tre oppgåver: (1) syntetisere beviskjeda til éi samanhengande forteljing, (2) demonstrere at FFF er eit fullstendig paradigmeskifte, og (3) vise at rammeverket generaliserer frå stolar til alle estetiske fag.
        </p>
      </section>

      <section>
        <h2>2. Det gamle paradigmet</h2>
        <h3>2.1 Sullivan, Le Corbusier og det deterministiske aksiomet</h3>
        <p>
          Louis Sullivan sin formulering frå 1896 var meint som ein poetisk observasjon. Men etterfylgjande generasjonar gjorde han til eit <em>aksiom</em>. Le Corbusier (1923) radikaliserte premissen: huset er "une machine à habiter". Desse etablerte <em>det deterministiske aksiomet</em>: gjev ein funksjon, skal forma kunne deduserast.
        </p>
        <h3>2.2 Modulor: Universalitet som illusjon</h3>
        <p>
          Le Corbusier sitt Modulor-system er den mest ambisiøse konsekvensen av aksiomet. Våre data falsifiserer dette direkte. Blant 93 stolar med identisk funksjon varierer symmetri 15 gonger. Modulor er feil fordi den er empirisk falsifisert.
        </p>
      </section>

      <section>
        <h2>3. Det nye paradigmet: Form Follows Fitness</h2>
        <p>
          <em>Form Follows Fitness</em> (FFF) seier: Forma på eit objekt er ikkje dedusert frå funksjonen, men <strong>selektert</strong> av eit fleirdimensjonalt fitnesslandskap der kvar akse representerer eit seleksjonstrykk.
        </p>
        <p>
          I FFF er kvart lokalt optimum ein <em>stil</em>: ei mellombels stabil formkonfigurasjon som held så lenge seleksjonstrykka held seg.
        </p>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs md:text-sm">
              <thead className="border-b-2 border-black">
                <tr>
                  <th className="py-4 px-2">Gammalt omgrep</th>
                  <th className="py-4 px-2">FFF-omgrep</th>
                  <th className="py-4 px-2">Definisjon i FFF</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                <tr><td className="py-4 px-2 text-black">Form follows function</td><td className="py-4 px-2 font-black uppercase text-black">Form follows fitness</td><td className="py-4 px-2 text-black">Form er resultatet av eit fitnesslandskap</td></tr>
                <tr><td className="py-4 px-2 text-black">Funksjon</td><td className="py-4 px-2 font-black uppercase text-black">Seleksjonstrykk</td><td className="py-4 px-2 text-black">Eitt av mange trykk</td></tr>
                <tr><td className="py-4 px-2 text-black">Designer</td><td className="py-4 px-2 font-black uppercase text-black">Distribuert agent</td><td className="py-4 px-2 text-black">Éin aktør i eit nettverk</td></tr>
              </tbody>
            </table>
          </div>
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            TABELL 1: Paradigmeskifte frå funksjonalisme til Form Follows Fitness.
          </figcaption>
        </figure>
      </section>

      <section>
        <h2>4. Distribuert intelligens</h2>
        <p>
          Det funksjonalistiske paradigmet set designaren i sentrum. FFF snur dette på hovudet. Formgjeving er ein <strong>distribuert prosess</strong>: materialet utøver agentur, verktyot avgrensar det moglege, marknaden selekterer og kulturen premierer. Designaren er ikkje ein eineveldig skapar, men éin agent i eit distribuert system.
        </p>
      </section>

      <section className="border-t-[10px] border-black pt-24">
        <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
        <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
          <p>
            461 stolar. 401 tredimensjonale modellar. 740 år med data. Fire artiklar. Éin konklusjon: <strong>Form follows fitness.</strong>
          </p>
          <p>
            Rammeverket gjer estetisk teori det den aldri har vore: testbar. Kvantifiserbar. Falsifiserbar. Operativ. Fitnesskartet erstattar aksiomet. Verktyet erstattar dogmet.
          </p>
        </div>
      </section>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Clark, A. (2008). <em className="normal-case">Supersizing the Mind.</em> Oxford University Press.</p>
          <p>Corbusier, Le (1923). <em className="normal-case">Vers une architecture.</em> Cres.</p>
          <p>Kuhn, T. S. (1962). <em className="normal-case">The Structure of Scientific Revolutions.</em> University of Chicago Press.</p>
          <p>Levin, M. (2019). The computational boundary of a self. <em className="normal-case">Frontiers in Psychology.</em></p>
          <p>Nakagaki, T. et al. (2000). Intelligence: Maze-solving by an amoeboid organism. <em className="normal-case">Nature.</em></p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case">Lippincott's Magazine.</em></p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
