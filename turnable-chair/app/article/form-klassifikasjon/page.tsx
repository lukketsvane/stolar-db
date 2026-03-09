"use client"

import { useRouter } from "next/navigation"
import ArticleLayout from "../../../components/article-layout"

export default function ArticleThreePage() {
  const router = useRouter()

  const header = (
    <div className="max-w-4xl">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel III</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Kan form åleine<br/>
        <span className="text-gray-200">fortelje tid?</span>
      </h1>
      <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight mt-8">
        Materiell-formell kopling i Nasjonalmuseet si stolsamling.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16 font-sans">
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">AHO</p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">3D-formanalyse</p>
        </div>
      </div>

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> Dersom funksjonalismen sitt dogme stemmer, at form fylgjer funksjon, burde stolar frå ulike nasjonar og tidsaldrar ikkje låt seg skilje geometrisk, sidan sitjefunksjonen er universell. Denne artikkelen testar påstanden empirisk gjennom maskinlæring på tredimensjonale punktsskyer frå 401 GLB-modellar i Nasjonalmuseet si samling. Funna falsifiserer funksjonalismen si nøytrale formlære: form kodar kulturell identitet og historisk tid romleg og geometrisk.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing</h2>
        <p>
          Tidlegare artiklar i denne serien har etablert at materialar ikkje er nøytrale berarar av form, men at dei inkarnerer kolonial handel og tilgangshistorie (Finne, 2026a), og at formutvikling over tid konvergerer mot fitness-optima snarare enn å fylgje ein deterministisk funksjon (Finne, 2026b). Denne tredje delen reiser eit oppfylgjande fundamentalt spørsmål: Dersom ein fjernar overflate, farge og materiale, og berre ser på den nakte geometrien, kan form i seg sjølv bera meining om tid og stad?
        </p>
        <p>
          Spørsmålet har djupe røter i designteorien. Sullivan (1896) formulerte målet <em>form follows function</em>, seinare kanonisert av Le Corbusier (1923). Dersom funksjonen til ein stol er invariant over tid og rom, burde nasjonal opphavsstad og historisk stilperiode vera irrelevante for dei geometriske proposisjonane. Men erfarne kjennarar gjenkjenner ein epoke straks, ofte frå ein silhuett aleine.
        </p>
      </section>

      <section>
        <h2>2. Forskingsgjennomgang</h2>
        <h3>2.1 Stilhistorie i møbeldesign</h3>
        <p>
          Den vestlege møbelhistoria vert tradisjonelt organisert i stilperiodar (Renessanse, Barokk, Rokokko, Nyklassisisme, Historisme, Jugend, Modernisme), der kvar epoke vert definert av karakteristiske formtrekk og dekorstrategiar (Lucie-Smith, 1979).
        </p>
        <h3>2.2 3D formanalyse</h3>
        <p>
          Datamaskinbasert formanalyse har utvikla seg frå statistiske deskriptorar til djuplæring. Osada et al. (2002) introduserte <em>shape distributions</em> som eit rotasjonsinvariant fingeravtrykk for 3D-form.
        </p>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig1_formrom.png" alt="Figur 1" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 1: UMAP-projeksjon av formrommet basert på 21 geometriske variablar. Klynger indikerer systematiske likskapar mellom stilperiodar.
          </figcaption>
        </figure>
      </section>

      <section>
        <h2>3. Metode</h2>
        <p>
          Datamaterialet består av 401 stolar med tilgjengelege GLB-modellar frå Nasjonalmuseet. Kvar modell vart normalisert: me sampla 2 048 punkt uniformt frå overflata, flytta kvar sky til origo, og skalerte til einingsvolum.
        </p>
        <p>
          Me trekte ut to sett med deskriptorar: 21 geometriske variablar (bounding box, PCA-eigenverdiar, konveks skrog, D2-distribusjon, krumming) og 30 materialtrekk.
        </p>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig2_klassefordeling.png" alt="Figur 2" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 2: Klassefordeling for stilprediksjon (n = 229).
          </figcaption>
        </figure>
      </section>

      <section>
        <h2>4. Resultat</h2>
        <p>
          Geometri åleine predikerer stil nesten fire gonger betre enn sjansen (40,5 % mot 10,5 %), og nasjon med 76,0 % F1 (mot 46,3 % sjanse). Barokk og Nyklassisisme er lettast å klassifisere geometrisk (F1 = 0,78 og 0,73).
        </p>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig3_klassifikasjon.png" alt="Figur 3" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 3: Klassifikasjonsresultat (makro-F1) for ulike trekksett. Geometri åleine presterer signifikant over sjansen.
          </figcaption>
        </figure>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6 text-center">
          <img src="/figurar/fig4_forvirring.png" alt="Figur 4" className="max-w-3xl h-auto rounded-xl shadow-sm border border-gray-100 inline-block" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 4: Forvirringsmatrise for stilprediksjon. Legg merke til forveksling mellom Historisme og Barokk/Nyklassisisme.
          </figcaption>
        </figure>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig5_perklasse_f1.png" alt="Figur 5" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 5: Per-klasse F1-score. Barokk og Nyklassisisme har dei tydelegaste geometriske signaturane.
          </figcaption>
        </figure>
      </section>

      <section>
        <h2>5. Diskusjon</h2>
        <p>
          Hovudfunnet er at geometrisk form, frigjort frå overflate, farge og material, kodar både historisk stilperiode og nasjonal opphavstad med signifikant presisjon. Dette rokkar tungt ved modernismens teoretiske rammeverk. Om <em>form follows function</em> heldt stikk, skulle ikkje ei norsk punktsky slå annleis inn i geometriske deskriptorar enn ei dansk eller fransk.
        </p>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig6_korrelasjon.png" alt="Figur 6" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 6: Korrelasjonsmatrise mellom geometriske og materielle trekk. Systematisk kovarians dokumenterer den materiell-formelle koplinga.
          </figcaption>
        </figure>
      </section>

      <section className="not-prose my-24 text-center">
        <figure className="space-y-6 inline-block">
          <img src="/figurar/fig7_kopling.png" alt="Figur 7" className="max-w-2xl h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 7: Visualisering av materiell-formell kopling. Spesifikke materialar affordar spesifikke geometriske konfigurasjoner.
          </figcaption>
        </figure>
      </section>

      <section className="border-t-[10px] border-black pt-24">
        <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
        <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
          <p>
            Gjennom ei systematisk maskinlæringsanalyse av 401 unike historiske stolar har denne studien vist at 3D geometrisk form åleine kan predikere stilperiode og nasjonal opphavstad. Form kodar kultur, og kulturen sit djupt i treverket og geometrien.
          </p>
        </div>
      </section>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Corbusier, Le (1923). <em className="normal-case">Vers une architecture.</em> Cres.</p>
          <p>Finne, I. R. (2026a). <em className="normal-case">Materialhistorie: Kolonialt arkiv.</em> AHO Working Paper.</p>
          <p>Finne, I. R. (2026b). <em className="normal-case">Form follows fitness.</em> AHO Working Paper.</p>
          <p>Lucie-Smith, E. (1979). <em className="normal-case">A History of Furniture.</em> William Morrow.</p>
          <p>Manovich, L. (2020). <em className="normal-case">Cultural Analytics.</em> MIT Press.</p>
          <p>Osada, R. et al. (2002). Shape distributions. <em className="normal-case">ACM Transactions on Graphics.</em></p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
