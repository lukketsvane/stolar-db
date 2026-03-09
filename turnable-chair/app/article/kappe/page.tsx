"use client"

import { useRouter } from "next/navigation"
import ArticleNav from "../../../components/article-nav"

export default function ArticleFivePage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      <header className="max-w-5xl mx-auto pt-48 pb-32 px-8">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">PhD-kappe</p>
        <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Distribuert<br/>
          <span className="text-gray-200">intelligens.</span>
        </h1>
        <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight max-w-3xl mt-8">
          Eit nytt paradigme for estetiske fag.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16">
          <div>
            <p className="text-[10px] font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed max-w-xs">
              Institutt for design, Arkitektur- og designhøgskolen i Oslo (AHO)
            </p>
          </div>
          <div>
            <p className="text-[10px] font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Type</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">PhD-kappe</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Syntese av fire empiriske artiklar om form, materialitet og industridesign.
            </p>
          </div>
        </div>

        <div className="max-w-3xl bg-gray-50 p-6 md:p-12 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100 italic text-lg md:text-2xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> I 130 år har estetiske fag operert under eit deterministisk aksiom: "form follows function". Denne kappa bind saman fire empiriske artiklar som til saman falsifiserer aksiomet og etablerer eit alternativ. Gjennom kvantitativ analyse av 461 stolar frå Nasjonalmuseet (1280–2020), 401 tredimensjonale modellar og 740 år med materialdata demonstrerer serien at form ikkje er dedusert frå funksjon, men selektert av eit fleirdimensjonalt fitnesslandskap der materialaffordanse, teknologi, økonomi, geografi og kultur utøver seleksjonstrykk. Kappa formulerer <em>Form Follows Fitness</em> (FFF) som eit fullstendig paradigmeskifte der formgjeving vert forstått som ein distribuert intelligent prosess.
        </div>
      </header>

      <article className="max-w-3xl mx-auto px-8 space-y-24 text-lg md:text-2xl leading-relaxed text-gray-900">
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">1. Innleiing: Ein revolusjon i fire akter</h2>
          <p className="mb-12">
            Denne avhandlinga starta med eit enkelt eksperiment: å stille Sullivan sitt aksiom "form ever follows function" på prøve mot eit reelt datasett. 461 stolar frå Nasjonalmuseet, alle med same funksjon, alle målte, dokumenterte og modellerte. Dersom aksiomet heldt, burde formvariasjonen vore liten. Ho var enorm.
          </p>
          <p>
            Denne kappa har tre oppgåver: (1) syntetisere beviskjeda til éi samanhengande forteljing, (2) demonstrere at FFF er eit fullstendig paradigmeskifte, og (3) vise at rammeverket generaliserer frå stolar til alle estetiske fag.
          </p>
        </section>

        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">2. Det nye paradigmet: Form Follows Fitness</h2>
          <p className="mb-12">
            <em>Form Follows Fitness</em> (FFF) seier: Forma på eit objekt er ikkje dedusert frå funksjonen, men <strong>selektert</strong> av eit fleirdimensjonalt fitnesslandskap der kvar akse representerer eit seleksjonstrykk. Funksjon er eitt av desse trykka, og sjeldan det viktigaste.
          </p>
          <p>
            I FFF er kvar stil eit lokalt optimum: ei mellombels stabil formkonfigurasjon som held så lenge seleksjonstrykka held seg. Når materialtilgangen skiftar (som med mahogni) eller teknologien endrar seg (som med kryssfiner), flyttar fitness-toppane seg, og formene må fylgje etter for å overleve.
          </p>
        </section>

        <section className="py-12 full-bleed">
          <div className="bg-white p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] border border-gray-100 shadow-sm overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">TABELL 1: Frå funksjonalisme til Form Follows Fitness</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-sm">
                <thead className="border-b-2 border-black">
                  <tr>
                    <th className="py-4 px-2">Gammalt omgrep</th>
                    <th className="py-4 px-2">FFF-omgrep</th>
                    <th className="py-4 px-2">Definisjon i FFF</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr><td className="py-4 px-2">Form follows function</td><td className="py-4 px-2 font-black uppercase">Form follows fitness</td><td className="py-4 px-2">Form er resultatet av eit fitnesslandskap</td></tr>
                  <tr><td className="py-4 px-2">Funksjon</td><td className="py-4 px-2 font-black uppercase">Seleksjonstrykk</td><td className="py-4 px-2">Eitt av mange trykk</td></tr>
                  <tr><td className="py-4 px-2">Designer</td><td className="py-4 px-2 font-black uppercase">Distribuert agent</td><td className="py-4 px-2">Éin aktør i eit nettverk</td></tr>
                  <tr><td className="py-4 px-2">Stil</td><td className="py-4 px-2 font-black uppercase">Fitnessoptimum</td><td className="py-4 px-2">Mellombels lokalt optimum</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">3. Distribuert intelligens</h2>
          <p className="mb-12">
            Det funksjonalistiske paradigmet set designaren i sentrum: éin intensjon, éin plan, éi optimal form. FFF snur dette på hovudet. Formgjeving er ein <strong>distribuert prosess</strong>:
          </p>
          <ul className="space-y-8 my-12 border-l-4 border-black pl-12 list-none">
            <li><strong>Materialet</strong> utøver agentur gjennom sine fysiske eigenskapar.</li>
            <li><strong>Verktyet</strong> avgrensar det moglege.</li>
            <li><strong>Marknaden</strong> selekterer kva som overlever.</li>
            <li><strong>Kulturen</strong> premierer visse formar gjennom prestisje-bias.</li>
          </ul>
          <p>
            Designaren er ikkje ein eineveldig skapar, men éin agent i eit distribuert system. Forma som kjem ut er eit <em>emergent resultat</em> av mange samverkande seleksjonstrykk, nett slik slimsoppen finn optimale baner utan ein hjerne.
          </p>
        </section>

        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
            <p>
              461 stolar. 401 tredimensjonale modellar. 740 år med data. Fire artiklar. Éin konklusjon: <strong>Form follows fitness.</strong>
            </p>
            <p>
              Sullivan sitt aksiom er ikkje ein feil, men eit <em>degenerert spesialtilfelle</em> som aldri er oppfylt i praksis. FFF gjer estetisk teori testbar, kvantifiserbar og operativ.
            </p>
            <p className="text-black not-italic font-sans font-black text-3xl leading-tight tracking-tight">
              Fitnesskartet erstattar aksiomet. Verktyet erstattar dogmet.
            </p>
          </div>
        </section>
      </article>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Clark, A. (2008). <em className="normal-case tracking-normal">Supersizing the Mind.</em> Oxford University Press.</p>
          <p>Kuhn, T. S. (1962). <em className="normal-case tracking-normal">The Structure of Scientific Revolutions.</em> University of Chicago Press.</p>
          <p>Levin, M. (2019). The computational boundary of a self. <em className="normal-case tracking-normal">Frontiers in Psychology,</em> 10, 2688.</p>
          <p>Nakagaki, T. et al. (2000). Intelligence: Maze-solving by an amoeboid organism. <em className="normal-case tracking-normal">Nature,</em> 407, 470.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </div>
  )
}
