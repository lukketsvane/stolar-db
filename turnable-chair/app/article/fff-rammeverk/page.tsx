"use client"

import { useRouter } from "next/navigation"
import ArticleNav from "../../../components/article-nav"

export default function ArticleFourPage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      <header className="max-w-7xl mx-auto pt-48 pb-32 px-6 md:px-12 lg:px-24">
        <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel IV</p>
        <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Form Follows<br/>
          <span className="text-gray-200">Fitness.</span>
        </h1>
        <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight max-w-3xl mt-8">
          Empirisk grunnlag for eit evolusjonært rammeverk i estetiske fag.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16">
          <div>
            <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed max-w-xs">
              Institutt for design, Arkitektur- og designhøgskolen i Oslo (AHO)
            </p>
          </div>
          <div>
            <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Informasjonsteori</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Analyse av 93 stolar gjennom 21 geometriske og 30 materielle eigenskapar.
            </p>
          </div>
        </div>

        <div className="max-w-2xl bg-gray-50 p-8 md:p-12 lg:p-16 rounded-2xl md:rounded-[2rem] border border-gray-100 italic text-base md:text-xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> Det modernistiske dogmet "form follows function" impliserer at form er deduserbar frå funksjon. Denne artikkelen falsifiserer dette empirisk ved å analysere 93 stolar frå Nasjonalmuseet si samling (1632–2018) gjennom 21 geometriske og 30 materielle eigenskapar utrekna frå 3D-modellar. Analysen viser at funksjon er konstant, alle objekta er stolar, medan form varierer radikalt. Informasjonsteoretisk analyse (mutual information) avdekkjer at material ber fem gonger meir informasjon om geometrisk form enn geografi (MI_material = 0.382, MI_geografi = 0.079). Artikkelen presenterer Form Follows Fitness (FFF), eit nytt rammeverk der form vert forstått som selektert av eit fleirdimensjonalt fitnesslandskap av materialaffordanse, teknologi, økonomi, geografi og kultur.
        </div>
      </header>

      <article className="max-w-2xl mx-auto px-6 md:px-12 lg:px-24 space-y-16 text-base md:text-lg leading-relaxed text-gray-900">
        
        {/* 1. INNLEIING */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">1. Innleiing</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">1.1 Eit dogme utan empirisk grunnlag</h3>
          <p className="mb-8">
            I over eit hundreår har Louis Sullivan sitt "form ever follows function" (1896) fungert som det avgjerande aksiomet i formgjevingsfaga. Le Corbusier (1923) bygde ein heil arkitektonisk doktrine på premissen, og etterkrigsmodernismen institusjonaliserte dogmet som pedagogisk rammeverk i designutdanningar verda over. Implikasjonen er deterministisk: gjev ein spesifikk funksjon, finst det <em>ei</em> optimal form. Alexander (1964) føreslo at form kan deriverast systematisk frå funksjonskrav, medan Giedion (1948) dokumenterte korleis mekaniseringa transformerte forholdet mellom form og produksjon. Ingen av desse stilte spørsmålet empirisk: <em>Stemmer det at form fylgjer funksjon?</em>
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">1.2 Testbar påstand, testbart datasett</h3>
          <p className="mb-8">
            Denne artikkelen nyttar Nasjonalmuseet si stolsamling som eit kontrollert eksperiment. Alle 408 objekt i databasen delar <em>same funksjon</em>: å sitte på. Dersom form fylgjer funksjon, burde formvariasjonen vore liten. Dersom form fylgjer <em>andre</em> krefter, burde me finne stor variasjon <em>og</em> kunne identifisere kva desse kreftene er. Frå denne samlinga har me modellert og målte 93 stolar med komplett metadata, 3D-geometri og materialopplysningar (1632–2018).
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">1.3 Forskingsspørsmål</h3>
          <ol className="list-decimal pl-8 mt-4 space-y-2">
            <li>Er formvariasjonen blant objekt med identisk funksjon stor nok til å falsifisere funksjonsdeterminismen?</li>
            <li>Kva seleksjonstrykk (material, tid, geografi) forklarer mest av formvariasjonen?</li>
            <li>Er stilperiode ein kausal eller emergent kategori?</li>
            <li>Korleis endrar fitnesslandskapet seg over tid, og kva driv endringane?</li>
            <li>Kan me formulere eit koherent alternativ til "form follows function" som er empirisk testbart?</li>
          </ol>
        </section>

        {/* 2. TEORETISK RAMMEVERK */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">2. Teoretisk rammeverk: Fem pilarar for FFF</h2>
          <p className="mb-8">
            <em>Form Follows Fitness</em> (FFF) kviler på fem teoretiske pilarar frå ulike fagfelt som til saman gjer rammeverket operativt.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.1 Fitnesslandskapet</h3>
          <p className="mb-8">
            Wright (1932) introduserte fitnesslandskapet som ein modell der kombinasjonar av genetiske variablar definerer eit topografisk rom med toppunkt (høg fitness) og dalar. Kauffman (1993) utvida modellen til komplekse system: når talet på interagerande variablar aukar, vert landskapet meir ruglete, med fleire lokale optimum. I FFF er forma til eit objekt ein posisjon i eit <em>n</em>-dimensjonalt landskap der kvar akse representerer eit seleksjonstrykk: material, teknologi, økonomi, geografi, kultur.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.2 Distribuert kognisjon og agentur</h3>
          <p className="mb-8">
            Intelligens treng ikkje ein sentral styrar. Nakagaki et al. (2000) viste at slimsoppen <em>Physarum polycephalum</em> finn optimale nettverksbaner utan nervesystem. Levin (2019) generaliserer dette: kognitiv kapasitet eksisterer på alle biologiske skalaer. Clark (2008) argumenterer for at kognisjon er <em>utvida</em>, spreidd ut over kropp, verkty og miljø. I FFF overfører me dette til designhistoria: materialet "veit" kva det toler, verktyot avgrensar kva som er mogleg, marknaden selekterer kva som overlever.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.3 Exploration og exploitation</h3>
          <p className="mb-8">
            Frå reinforcement learning kjenner me avveginga mellom <em>exploration</em> (utforske ukjent terreng) og <em>exploitation</em> (utnytte kjende løysingar). Gould & Eldredge (1972) skildra ein analog dynamikk i paleobiologien: <em>punctuated equilibrium</em>. I designhistoria ser me periodar med høg formdiversitet (exploration) etterfylgd av konvergens (exploitation).
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.4 Affordanse-teori</h3>
          <p className="mb-8">
            Gibson (1977) definerte affordanse som det eit miljø tilbyr ein aktør. Pye (1968) nyanserte korleis materialets natur legg føringar for kva former handverkaren kan realisere. I FFF er kvart material ein aktør med ein distinkt <em>geometrisk profil</em>. Desse affordansane er ikkje passive eigenskapar, men aktive føringar som kanaliserer forma (Ingold, 2007).
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.5 Morphospace og latent space</h3>
          <p>
            Raup (1966) innførte <em>morphospace</em> i paleobiologien: det teoretiske rommet av alle moglege skalformer. UMAP-projeksjonen i Art. III er nett dette, eit empirisk morphospace for stolar. FFF foreiner desse: fitnesslandskapet <em>er</em> det evaluerte morphospace.
          </p>
        </section>

        {/* 3. METODE */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">3. Metode</h2>
          <p className="mb-8">
            Datasettet består av 93 stolar med komplett metadata (1632–2018). Kvar stol er skildra av 21 geometriske features og 30 binære materialvariablar. Me nyttar <em>mutual information</em> (MI) for å kvantifisere kor mykje kvart seleksjonstrykk fortel om geometrisk form (Cover & Thomas, 2006). Random Forest (Breiman, 2001) evaluerer prediksjonskraft.
          </p>
        </section>

        {/* 4. RESULTAT */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">4. Resultat: Åtte empiriske bevis</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.1 Bevis I: Funksjon er konstant, form varierer radikalt</h3>
          <p className="mb-8">
            Dersom form fylgjer funksjon burde den geometriske variasjonen vore liten. Dataa viser at symmetriscore varierer 15.1 gonger, djupn 3.0 gonger, og kompaktheit 2.6 gonger blant objekt med identisk funksjon. Funksjon kan ikkje forklare denne variasjonen.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.2 Bevis II & III: Material predikerer form og affordanse</h3>
          <p className="mb-8">
            Materialval er ein sterkare formgjevar enn funksjon. Ull, skumplast og gummi har enorme effektstorleikar (Cohens d > 1.2) på massefordeling og formfordeling. Kvart material tilbyr ei distinkt formverd: Mahogni affordar slanke konstruksjonar (låg kompaktheit: 0.38), medan stål affordar rette linjer (låg kurvatur: 0.07).
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.3 Bevis IV: MI-dekomponering</h3>
          <p className="mb-8">
            Mutual Information-analysen viser at material (MI = 0.382) ber fem gonger meir informasjon om form enn geografi (MI = 0.079). Tidsperioden (MI = 0.168) ligg mellom. Funksjon forklarer ingenting (MI = 0).
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.4 Bevis V: Stil er emergent, ikkje kausal</h3>
          <p className="mb-8">
            Stilperiode (F1 = 0.19) predikerer formklynger dårlegast av alle alternativ. Tid (F1 = 0.44) og material (F1 = 0.33) slår stilmerkelappen kvar for seg. Stil er eit <em>symptom</em> på seleksjonstrykk, ikkje ein <em>årsak</em>.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.5 Bevis VII & VIII: Drift og Entropi</h3>
          <p>
            Den desidert største drifta i fitnesslandskapet (11.66 standardeiningar) fell mellom 1600-talet og 1750, nett når koloniale materialar vert tilgjengelege. Shannon-entropien kollapsar frå 2.50 til 1.50 bit under mahognitoppen, ein klassisk exploitation-syklus der éi løysing utkonkurrerer alle andre.
          </p>
        </section>

        {/* 5. DISKUSJON */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">5. Diskusjon</h2>
          <p className="mb-8">
            <em>Form Follows Fitness</em> er eit rammeverk der form vert forstått som <em>selektert</em>, ikkje dedusert. Forma på ein stol er eit mellombels optimum i eit fleirdimensjonalt landskap definert av materialaffordanse, temporalt trykk, geografi og kultur.
          </p>
          <p className="mb-8">
            "Form follows function" er eit <em>degenerert spesialtilfelle</em> som aldri eksisterer i praksis, fordi materialtilgang, økonomiske vilkår og kulturelle preferansar alltid utøver trykk. Sullivan og Le Corbusier sine prinsipp er spesialtilfelle der MI for alt utanom funksjon er lik null. Våre data viser at dette vilkåret aldri er oppfylt.
          </p>
          <p>
            Innsikta om distribuert kognisjon gjev FFF eit djupare fundament: formgjeving er ein distribuert prosess der intelligens er spreidd over materialets eigenskapar, handverkaren sin kompetanse, handelsnettverket og kulturell seleksjon. Designaren er éin agent blant mange.
          </p>
        </section>

        {/* KONKLUSJON */}
        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
            <p>
              Denne artikkelen har lagt fram åtte empiriske bevis som samla falsifiserer "form follows function" og etablerer <em>Form Follows Fitness</em> som eit empirisk fundert alternativ.
            </p>
            <p className="text-black not-italic font-sans font-black text-3xl leading-tight tracking-tight">
              FFF gjer estetisk teori testbar. Rammeverket er ikkje ein filosofisk posisjon, men ein empirisk modell, open for falsifisering og operativ for designpraksis. Fitnesskartet erstattar det modernistiske aksiomet med eit verktøy.
            </p>
          </div>
        </section>
      </article>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Alexander, C. (1964). <em className="normal-case tracking-normal">Notes on the Synthesis of Form.</em> Harvard University Press.</p>
          <p>Clark, A. (2008). <em className="normal-case tracking-normal">Supersizing the Mind.</em> Oxford University Press.</p>
          <p>Cover, T. M., & Thomas, J. A. (2006). <em className="normal-case tracking-normal">Elements of Information Theory.</em> Wiley.</p>
          <p>Finne, I. R. (2026c). <em className="normal-case tracking-normal">Kan form åleine fortelje tid?</em> AHO Working Paper.</p>
          <p>Giedion, S. (1948). <em className="normal-case tracking-normal">Mechanization Takes Command.</em> Oxford University Press.</p>
          <p>Ingold, T. (2007). Materials against materiality. <em className="normal-case tracking-normal">Archaeological Dialogues,</em> 14(1), 1-16.</p>
          <p>Kauffman, S. A. (1993). <em className="normal-case tracking-normal">The Origins of Order.</em> Oxford University Press.</p>
          <p>Nakagaki, T. et al. (2000). Intelligence: Maze-solving by an amoeboid organism. <em className="normal-case tracking-normal">Nature,</em> 407, 470.</p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case tracking-normal">Lippincott's Magazine,</em> 57, 403-409.</p>
          <p>Wright, S. (1932). The roles of mutation, inbreeding, crossbreeding and selection in evolution. <em className="normal-case tracking-normal">Proc. 6th Int. Cong. Genet,</em> 1, 356-366.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </div>
  )
}
