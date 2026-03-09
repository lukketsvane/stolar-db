"use client"

import { useRouter } from "next/navigation"
import ArticleLayout from "../../../components/article-layout"

export default function ArticleFourPage() {
  const router = useRouter()

  const header = (
    <div className="w-full">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel IV</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Form Follows<br/>
        <span className="text-gray-200">Fitness.</span>
      </h1>
      <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight mt-8">
        Empirisk grunnlag for eit evolusjonært rammeverk i estetiske fag.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16 font-sans">
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">AHO</p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Informasjonsteori</p>
        </div>
      </div>

      <div className="mt-16 py-8 border-t border-black">
        <p className="text-xl font-serif italic leading-relaxed text-black">
          <strong>Samandrag:</strong> Det modernistiske dogmet "form follows function" impliserer at form er deduserbar frå funksjon. Denne artikkelen falsifiserer dette empirisk ved å analysere 93 stolar frå Nasjonalmuseet si samling gjennom 21 geometriske og 30 materielle eigenskapar utrekna frå 3D-modellar. Artikkelen presenterer Form Follows Fitness (FFF) som eit alternativ.
        </p>
      </div>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing</h2>
        <h3>1.1 Eit dogme utan empirisk grunnlag</h3>
        <p>
          I over eit hundreår har Louis Sullivan sitt "form ever follows function" (1896) fungert som det avgjerande aksiomet i formgjevingsfaga. Le Corbusier (1923) radikaliserte premissen. Ingen av desse stilte spørsmålet empirisk: <em>Stemmer det at form fylgjer funksjon?</em>
        </p>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig1_form_variasjon.png" alt="Figur 1" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 1: Formvariasjon blant objekt med identisk funksjon. Symmetri, djupn og kompaktheit varierer radikalt.
          </figcaption>
        </figure>
      </section>

      <section>
        <h2>2. Teoretisk rammeverk: Fem pilarar for FFF</h2>
        <p>
          <em>Form Follows Fitness</em> (FFF) kviler på fem teoretiske pilarar:
        </p>
        <ol>
          <li><strong>Fitnesslandskapet:</strong> Form som posisjon i eit n-dimensjonalt landskap (Wright, 1932).</li>
          <li><strong>Distribuert kognisjon:</strong> Intelligens utan sentral styrar (Nakagaki et al., 2000).</li>
          <li><strong>Exploration/exploitation:</strong> Veksling mellom utforsking og utnytting (Gould & Eldredge, 1972).</li>
          <li><strong>Affordanse:</strong> Materialet som aktiv aktør (Gibson, 1977; Ingold, 2007).</li>
          <li><strong>Morphospace:</strong> Rommet av alle moglege former (Raup, 1966).</li>
        </ol>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig2_material_form_heatmap.png" alt="Figur 2" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 2: Heatmap som viser korrelasjonen mellom spesifikke materialar og geometriske trekk.
          </figcaption>
        </figure>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig3_fitness_landscape_pca.png" alt="Figur 3" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 3: PCA-projeksjon av fitnesslandskapet. Toppane representerer stabile formelle konfigurasjoner (stilar).
          </figcaption>
        </figure>
      </section>

      <section>
        <h2>3. Resultat: Åtte empiriske bevis</h2>
        <h3>3.1 Bevis I: Funksjon er konstant, form varierer radikalt</h3>
        <p>
          Dataa viser at symmetriscore varierer 15.1 gonger, djupn 3.0 gonger, og kompaktheit 2.6 gonger blant objekt med identisk funksjon.
        </p>
      </section>

      <section className="not-prose my-24 text-center">
        <figure className="space-y-6 inline-block">
          <img src="/figurar/fig4_exploration_exploitation.png" alt="Figur 4" className="max-w-3xl h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 4: Syklusar av exploration (utforsking) og exploitation (utnytting) over tid.
          </figcaption>
        </figure>
      </section>

      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src="/figurar/fig5_material_affordance.png" alt="Figur 5" className="w-full h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 5: Spesifikke material-affordansar. Kvart material tilbyr ei unik "formverd".
          </figcaption>
        </figure>
      </section>

      <section className="not-prose my-24 text-center">
        <figure className="space-y-6 inline-block">
          <img src="/figurar/fig6_mutual_information.png" alt="Figur 6" className="max-w-xl h-auto rounded-xl shadow-sm border border-gray-100" />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            FIGUR 6: Mutual Information (MI) mellom seleksjonstrykk og form. Material ber fem gonger meir informasjon enn geografi.
          </figcaption>
        </figure>
      </section>

      <section>
        <h2>4. Diskusjon</h2>
        <p>
          FFF generaliserer funksjonalismen: Sullivan og Le Corbusier sine prinsipp er spesialtilfelle der MI for alt utanom funksjon er lik null. Våre data viser at dette vilkåret aldri er oppfylt.
        </p>
      </section>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Alexander, C. (1964). <em className="normal-case">Notes on the Synthesis of Form.</em> Harvard University Press.</p>
          <p>Clark, A. (2008). <em className="normal-case">Supersizing the Mind.</em> Oxford University Press.</p>
          <p>Giedion, S. (1948). <em className="normal-case">Mechanization Takes Command.</em> Oxford University Press.</p>
          <p>Kauffman, S. A. (1993). <em className="normal-case">The Origins of Order.</em> Oxford University Press.</p>
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
