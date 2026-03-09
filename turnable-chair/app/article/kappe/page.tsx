"use client"

import { useRouter } from "next/navigation"
import ArticleLayout from "../../../components/article-layout"

export default function ArticleFivePage() {
  const router = useRouter()

  const header = (
    <div className="max-w-4xl">
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
          <p className="text-sm text-gray-500 mt-4 leading-relaxed">
            Syntese av fire empiriske artiklar om form, materialitet og industridesign.
          </p>
        </div>
      </div>

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> I 130 år har estetiske fag operert under eit deterministisk aksiom: "form follows function". Denne kappa bind saman fire empiriske artiklar som til saman falsifiserer aksiomet og etablerer eit alternativ. Gjennom kvantitativ analyse av 461 stolar frå Nasjonalmuseet (1280–2020), 401 tredimensjonale modellar og 740 år med materialdata demonstrerer serien at form ikkje er dedusert frå funksjon, men selektert av eit fleirdimensjonalt fitnesslandskap der materialaffordanse, teknologi, økonomi, geografi og kultur utøver seleksjonstrykk.
      </blockquote>
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
          Det som byrja som ein enkel test vart ei beviskjede på fire ledd. Artikkel I avdekte at materialar ikkje er nøytrale medium, men komprimerte geopolitiske historier. Artikkel II viste at stilar migrerer langs maktgeografiske linjer, ikkje etter formell logikk. Artikkel III demonstrerte at rein 3D-geometri kodar kulturell identitet og historisk tid. Artikkel IV samla bevisa og formulerte <em>Form Follows Fitness</em> (FFF) som eit koherent alternativ.
        </p>
        <p>
          Denne kappa har tre oppgåver: (1) syntetisere beviskjeda til éi samanhengande forteljing, (2) demonstrere at FFF er eit fullstendig paradigmeskifte i Kuhn si tyding (1962), og (3) vise at rammeverket generaliserer frå stolar til alle estetiske fag.
        </p>
      </section>

      <section>
        <h2>2. Det gamle paradigmet</h2>
        <h3>2.1 Sullivan, Le Corbusier og det deterministiske aksiomet</h3>
        <p>
          Louis Sullivan sin formulering frå 1896, "form ever follows function", var meint som ein poetisk observasjon av naturen. Men etterfylgjande generasjonar gjorde han til eit <em>aksiom</em>. Le Corbusier radikaliserte premissen: huset er "une machine à habiter". Loos (1908) gjekk endå lenger: ornament er kriminalitet. Desse etablerte det me kan kalle <em>det deterministiske aksiomet</em>: gjev ein funksjon, skal forma kunne deduserast.
        </p>
        <h3>2.2 Modulor: Universalitet som illusjon</h3>
        <p>
          Le Corbusier sitt Modulor-system (1950) er den mest ambisiøse konsekvensen av aksiomet: eit proposjonssystem basert på den menneskelege kroppen. Våre data falsifiserer dette direkte. Blant 93 stolar med identisk funksjon varierer symmetri 15 gonger og djupn 3 gonger. Dersom éin universell proporsjon var optimal, burde variansen vore null. Den er enorm.
        </p>
        <h3>2.3 Alternativa som ikkje heldt</h3>
        <p>
          Funksjonalismen har ikkje mangla kritikarar. Pye (1968) viste at form alltid er delvis kontingent. Alexander (1964) foreslo at form kan deriverast frå dekomponering, men aksepterte underdeterminering. Simon (1996) kom nærast med design som søking i eit løysingsrom, men mangla det evolusjonære perspektivet.
        </p>
        <h3>2.4 Kvifor det gamle paradigmet overlevde</h3>
        <p>
          Kuhn (1962) argumenterte for at vitskapelege paradigme ikkje fell fordi dei er motbevist, men fordi eit betre alternativ vert tilgjengeleg. "Form follows function" overlevde fordi det var <em>operativt</em>: det gav designstudentar eit enkelt prinsipp. Problemet er at det er feil.
        </p>
      </section>

      <section>
        <h2>3. Det nye paradigmet: Form Follows Fitness</h2>
        <h3>3.1 Kjernepåstanden</h3>
        <p>
          <em>Form Follows Fitness</em> (FFF) seier: Forma på eit objekt er ikkje dedusert frå funksjonen, men <strong>selektert</strong> av eit fleirdimensjonalt fitnesslandskap der kvar akse representerer eit seleksjonstrykk. Funksjon er eitt av desse trykka, og sjeldan det viktigaste.
        </p>
        <h3>3.2 Dei fem pilarane</h3>
        <ul>
          <li><strong>Fitnesslandskapet (Wright, 1932):</strong> Form som posisjon i eit n-dimensjonalt landskap. Stilar er lokale toppunkt.</li>
          <li><strong>Distribuert kognisjon:</strong> Intelligens utan sentral styrar. Materialet "veit" kva det toler.</li>
          <li><strong>Exploration/exploitation:</strong> Veksling mellom utforsking av nytt terreng og utnytting av optima.</li>
          <li><strong>Affordanse (Gibson, 1977):</strong> Kvart material tilbyr ei distinkt formverd.</li>
          <li><strong>Morphospace (Raup, 1966):</strong> Rommet av alle moglege former.</li>
        </ul>
        <h3>3.3 Sullivan som degenerert spesialtilfelle</h3>
        <p>
          I FFF sin terminologi er "form follows function" gyldig <em>berre</em> når alle seleksjonstrykk utanom funksjon er lik null. Våre data viser at dette vilkåret aldri er oppfylt. Sullivan si lov er såleis ikkje feil i absolutt forstand, men eit degenerert spesialtilfelle.
        </p>
      </section>

      <section className="not-prose my-32">
        <div className="bg-white p-8 md:p-12 lg:p-16 rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-8 text-center">TABELL 1: Frå funksjonalisme til Form Follows Fitness</h4>
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
        <h2>4. Beviskjeda: Fire artiklar, éin konklusjon</h2>
        <p>
          <strong>Art. I:</strong> Materialet som agent. Mahogni sin boge avspeglar kolonihandelen. Materialet er ikkje nøytralt; det legg løynde stiar i fitnesskartet.
        </p>
        <p>
          <strong>Art. II:</strong> Fitness-konvergensen. Omsluttande volum konvergerer etter industrialiseringa, eit uttrykk for auka seleksjonstrykk (logistikk, standardisering).
        </p>
        <p>
          <strong>Art. III:</strong> Form kodar identitet. Rein 3D-geometri predikerer nasjon (76 %) og stil (40,5 %). Funksjonen forklarer ingenting.
        </p>
        <p>
          <strong>Art. IV:</strong> Fitnesskartet. Material ber fem gonger meir informasjon om form enn geografi. Stilperiode er den svakaste prediktoren.
        </p>
      </section>

      <section>
        <h2>5. Generalisering: Frå stolar til alle estetiske fag</h2>
        <p>
          FFF er utvikla på stolar, men mekanismane generaliserer. Ein kopp delar same funksjonelle invarians, men formrommet er enormt. I tekstil affordar ull andre former enn silke. I arkitektur utøver reguleringsplanar og økonomi trykk samstundes. FFF tilbyr eit <strong>felles vokabular</strong>: seleksjonstrykk, morphospace, affordanse.
        </p>
      </section>

      <section>
        <h2>6. Distribuert intelligens</h2>
        <p>
          Det funksjonalistiske paradigmet set designaren i sentrum. FFF snur dette på hovudet. Formgjeving er ein <strong>distribuert prosess</strong> der materialet utøver agentur, verktyot avgrensar det moglege, marknaden selekterer og kulturen premierer. Designaren kontrollerer ikkje utfallet, men navigerer i landskapet.
        </p>
      </section>

      <section>
        <h2>7. FFF som pedagogisk rammeverk</h2>
        <p>
          Studenten bør starte med spørsmålet: "Kva er seleksjonstrykka?", ikkje berre "Kva er funksjonen?". Materialval vert den primære designvariabelen. Stilkategoriar vert diagnostiske verktøy, ikkje mål i seg sjølv.
        </p>
      </section>

      <section>
        <h2>8. FFF som vitskapsteori: Paradigmeskiftet</h2>
        <p>
          FFF oppfyller Kuhn sine kjenneteikn på eit paradigmeskifte: anomaliar vert uignorlege, eit nytt paradigme løyser anomaliane, og det nye subsumerer det gamle som spesialtilfelle. FFF er empirisk, kvantitativt og falsifiserbart.
        </p>
      </section>

      <section>
        <h2>9. Avgrensingar og framtidig forsking</h2>
        <p>
          Beviskjeda har avgrensingar: éi samling, éin objekttype, museumsseleksjonsskaevheit. Framtidig forsking bør inkludere kryssmuseum-validering (Victoria & Albert, MoMA) og bruk av deep learning (PointNet) for formanalyse.
        </p>
      </section>

      <section className="border-t-[10px] border-black pt-24">
        <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
        <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
          <p>
            461 stolar. 401 tredimensjonale modellar. 740 år med data. Fire artiklar. Éin konklusjon: <strong>Form follows fitness.</strong>
          </p>
          <p>
            Sullivan sitt aksiom er ikkje ein feil, men eit degenerert spesialtilfelle. FFF gjer estetisk teori testbar, kvantifiserbar og operativ. Fitnesskartet erstattar aksiomet. Verktyet erstattar dogmet.
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
