"use client"

import { useRouter } from "next/navigation"
import ArticleNav from "../../../components/article-nav"

export default function ArticleFivePage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      <header className="max-w-7xl mx-auto pt-48 pb-32 px-6 md:px-12 lg:px-24">
        <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">PhD-kappe</p>
        <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Distribuert<br/>
          <span className="text-gray-200">intelligens.</span>
        </h1>
        <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight max-w-3xl mt-8">
          Eit nytt paradigme for estetiske fag.
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
            <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Type</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">PhD-kappe</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Syntese av fire empiriske artiklar om form, materialitet og industridesign.
            </p>
          </div>
        </div>

        <div className="max-w-2xl bg-gray-50 p-8 md:p-12 lg:p-16 rounded-2xl md:rounded-[2rem] border border-gray-100 italic text-base md:text-xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> I 130 år har estetiske fag operert under eit deterministisk aksiom: "form follows function". Denne kappa bind saman fire empiriske artiklar som til saman falsifiserer aksiomet og etablerer eit alternativ. Gjennom kvantitativ analyse av 461 stolar frå Nasjonalmuseet (1280–2020), 401 tredimensjonale modellar og 740 år med materialdata demonstrerer serien at form ikkje er dedusert frå funksjon, men selektert av eit fleirdimensjonalt fitnesslandskap der materialaffordanse, teknologi, økonomi, geografi og kultur utøver seleksjonstrykk. Kappa formulerer Form Follows Fitness (FFF) som eit fullstendig paradigmeskifte der formgjeving vert forstått som ein distribuert intelligent prosess.
        </div>
      </header>

      <article className="max-w-2xl mx-auto px-6 md:px-12 lg:px-24 space-y-16 text-base md:text-lg leading-relaxed text-gray-900">
        
        {/* 1. INNLEIING */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">1. Innleiing: Ein revolusjon i fire akter</h2>
          <p className="mb-8">
            Denne avhandlinga starta med eit enkelt eksperiment: å stille Sullivan sitt aksiom "form ever follows function" (1896) på prøve mot eit reelt datasett. 461 stolar frå Nasjonalmuseet, alle med same funksjon, alle målte, dokumenterte og modellerte. Dersom aksiomet heldt, burde formvariasjonen vore liten. Ho var enorm.
          </p>
          <p className="mb-8">
            Det som byrja som ein enkel test vart ei beviskjede på fire ledd. Artikkel I avdekte at materialar ikkje er nøytrale medium, men komprimerte geopolitiske historier. Artikkel II viste at stilar migrerer langs maktgeografiske linjer, ikkje etter formell logikk. Artikkel III demonstrerte at rein 3D-geometri kodar kulturell identitet og historisk tid. Artikkel IV samla bevisa og formulerte <em>Form Follows Fitness</em> (FFF) som eit koherent alternativ.
          </p>
          <p>
            Denne kappa har tre oppgåver: (1) syntetisere beviskjeda til éi samanhengande forteljing, (2) demonstrere at FFF er eit fullstendig paradigmeskifte, og (3) vise at rammeverket generaliserer frå stolar til alle estetiske fag.
          </p>
        </section>

        {/* 2. DET GAMLE PARADIGMET */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">2. Det gamle paradigmet</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.1 Sullivan, Le Corbusier og det deterministiske aksiomet</h3>
          <p className="mb-8">
            Louis Sullivan sin formulering frå 1896, "form ever follows function", var meint som ein poetisk observasjon av naturen. Men etterfylgjande generasjonar gjorde han til eit <em>aksiom</em>. Le Corbusier (1923) radikaliserte premissen: huset er "une machine à habiter", og kvar del må tene ein funksjon. Loos (1908) gjekk endå lenger: ornament er kriminalitet. Desse etablerte det me kan kalle <em>det deterministiske aksiomet</em>: gjev ein funksjon, skal forma kunne <em>deduserast</em>.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.2 Modulor: Universalitet som illusjon</h3>
          <p className="mb-8">
            Le Corbusier sitt Modulor-system (1950) er den mest ambisiøse konsekvensen av aksiomet: eit proposjonssystem basert på den menneskelege kroppen. Våre data falsifiserer dette direkte. Blant 93 stolar med identisk funksjon varierer symmetri 15 gonger og djupn 3 gonger. Dersom éin universell proporsjon var optimal, burde variansen vore null. Den er enorm.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.3 Kvifor det gamle paradigmet overlevde</h3>
          <p>
            Kuhn (1962) argumenterte for at vitskapelege paradigme ikkje fell fordi dei er motbevist, men fordi eit betre alternativ vert tilgjengeleg. "Form follows function" overlevde i 130 år ikkje fordi det var korrekt, men fordi det var <em>operativt</em>: det gav designstudentar eit enkelt prinsipp å arbeide etter. Problemet er at det er feil.
          </p>
        </section>

        {/* 3. DET NYE PARADIGMET */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">3. Det nye paradigmet: Form Follows Fitness</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">3.1 Kjernepåstanden</h3>
          <p className="mb-8">
            <em>Form Follows Fitness</em> (FFF) seier: Forma på eit objekt er ikkje dedusert frå funksjonen, men <strong>selektert</strong> av eit fleirdimensjonalt fitnesslandskap der kvar akse representerer eit seleksjonstrykk. Ideen kjem frå Wright (1932) og Kauffman (1993): eit topografisk rom der kvar stil er eit lokalt optimum.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">3.2 Dei fem pilarane</h3>
          <ul className="list-disc pl-8 mb-8 space-y-2">
            <li><strong>Fitnesslandskapet:</strong> Form som posisjon i eit n-dimensjonalt landskap.</li>
            <li><strong>Distribuert kognisjon:</strong> Intelligens utan sentral styrar. Materialet "veit" kva det toler.</li>
            <li><strong>Exploration/exploitation:</strong> Veksling mellom utforsking av nytt terreng og utnytting av optima.</li>
            <li><strong>Affordanse:</strong> Materialet som aktiv aktør (Gibson, 1977).</li>
            <li><strong>Morphospace:</strong> Rommet av alle moglege former (Raup, 1966).</li>
          </ul>
        </section>

        {/* 4. BEVISKJEDA */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">4. Beviskjeda: Fire artiklar, éin konklusjon</h2>
          <p className="mb-8">
            Artikkel I viste at material er ein agent (mahogniens boge). Artikkel II viste at form er selektert (fitness-konvergens i volum). Artikkel III viste at form kodar identitet (3D-geometri predikerer nasjon). Artikkel IV la fram åtte empiriske bevis på at fitnesslandskapet er reelt og målbart.
          </p>
          <p>
            Det mest oppsiktsvekkande funnet er at <strong>stilperiode predikerer form dårlegast av alle alternativ</strong> (F1 = 0.19). Stilkategoriane er symptom på seleksjonstrykk, ikkje årsaker til form.
          </p>
        </section>

        {/* 5. DISTRIBUERT INTELLIGENS */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">5. Distribuert intelligens</h2>
          <p className="mb-8">
            Formgjeving er ein distribuert prosess: materialet utøver agentur, verktyot avgrensar det moglege, marknaden selekterer og kulturen premierer. Designaren er ikkje ein eineveldig skapar, men éin agent i eit distribuert system. Forma som kjem ut er eit <em>emergent resultat</em>, lik slimsoppen som finn optimale baner utan ein hjerne.
          </p>
        </section>

        {/* KONKLUSJON */}
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
          <p>Corbusier, Le (1923). <em className="normal-case tracking-normal">Vers une architecture.</em> Cres.</p>
          <p>Kuhn, T. S. (1962). <em className="normal-case tracking-normal">The Structure of Scientific Revolutions.</em> University of Chicago Press.</p>
          <p>Levin, M. (2019). The computational boundary of a self. <em className="normal-case tracking-normal">Frontiers in Psychology,</em> 10, 2688.</p>
          <p>Nakagaki, T. et al. (2000). Intelligence: Maze-solving by an amoeboid organism. <em className="normal-case tracking-normal">Nature,</em> 407, 470.</p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case tracking-normal">Lippincott's Magazine,</em> 57, 403-409.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </div>
  )
}
