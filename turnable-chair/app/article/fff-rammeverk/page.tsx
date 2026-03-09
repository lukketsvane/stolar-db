"use client"

import { useRouter } from "next/navigation"
import ArticleLayout from "../../../components/article-layout"

export default function ArticleFourPage() {
  const router = useRouter()

  const header = (
    <div className="max-w-4xl">
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

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> Det modernistiske dogmet "form follows function" impliserer at form er deduserbar frå funksjon. Denne artikkelen falsifiserer dette empirisk.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing</h2>
        <h3>1.1 Eit dogme utan empirisk grunnlag</h3>
        <p>
          I over eit hundreår har Louis Sullivan sitt "form ever follows function" (1896) fungert som det avgjerande aksiomet i formgjevingsfaga.
        </p>
      </section>

      <section>
        <h2>2. Teoretisk rammeverk: Fem pilarar for FFF</h2>
        <p>
          <em>Form Follows Fitness</em> (FFF) kviler på fem teoretiske pilarar:
        </p>
        <ul>
          <li><strong>Fitnesslandskapet:</strong> Form som posisjon i eit n-dimensjonalt landskap.</li>
          <li><strong>Distribuert kognisjon:</strong> Intelligens utan sentral styrar.</li>
          <li><strong>Exploration/exploitation:</strong> Veksling mellom utforsking og utnytting.</li>
          <li><strong>Affordanse:</strong> Materialet som aktiv aktør.</li>
          <li><strong>Morphospace:</strong> Rommet av alle moglege former.</li>
        </ul>
      </section>

      <section>
        <h2>3. Resultat: Åtte empiriske bevis</h2>
        <h3>3.1 Bevis I: Funksjon er konstant, form varierer radikalt</h3>
        <p>
          Dersom form fylgjer funksjon burde den geometriske variasjonen vore liten. Dataa viser at symmetriscore varierer 15.1 gonger.
        </p>
      </section>

      <section>
        <h2>4. Diskusjon</h2>
        <p>
          FFF generaliserer funksjonalismen: Sullivan og Le Corbusier sine prinsipp er spesialtilfelle der MI for alt utanom funksjon er lik null. Våre data viser at dette vilkåret aldri er oppfylt.
        </p>
      </section>

      <footer className="mt-32 pt-16 border-t border-gray-100 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
        <p>&copy; 2026 Iver Raknes Finne</p>
        <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
      </footer>
    </ArticleLayout>
  )
}
