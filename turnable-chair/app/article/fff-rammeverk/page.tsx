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
        <strong>Samandrag:</strong> Det modernistiske dogmet "form follows function" impliserer at form er deduserbar frå funksjon. Denne artikkelen falsifiserer dette empirisk ved å analysere 93 stolar frå Nasjonalmuseet si samling gjennom 21 geometriske og 30 materielle eigenskapar utrekna frå 3D-modellar. Artikkelen presenterer Form Follows Fitness (FFF) som eit alternativ.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing</h2>
        <h3>1.1 Eit dogme utan empirisk grunnlag</h3>
        <p>
          I over eit hundreår har Louis Sullivan sitt "form ever follows function" (1896) fungert som det avgjerande aksiomet i formgjevingsfaga. Le Corbusier (1923) bygde ein heil arkitektonisk doktrine på premissen. Implikasjonen er deterministisk: gjev ein spesifikk funksjon, finst det ei optimal form. Men stemmer dette empirisk?
        </p>
        <h3>1.2 Testbar påstand</h3>
        <p>
          Denne artikkelen nyttar Nasjonalmuseet si stolsamling som eit kontrollert eksperiment. Alle objekt i databasen delar same funksjon: å sitte på. Dersom form fylgjer funksjon, burde formvariasjonen vore liten. Ho er i staden enorm.
        </p>
      </section>

      <section className="not-prose my-32">
        <div className="bg-white p-8 md:p-12 lg:p-16 rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-8 text-center">TABELL 1: Formvariasjon blant 93 stolar med identisk funksjon</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs md:text-sm">
              <thead className="border-b-2 border-black">
                <tr>
                  <th className="py-4 px-2">Eigenskap</th>
                  <th className="py-4 px-2">Min</th>
                  <th className="py-4 px-2">Maks</th>
                  <th className="py-4 px-2">Ratio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                <tr><td className="py-4 px-2 uppercase font-black">Symmetriscore</td><td className="py-4 px-2">0.011</td><td className="py-4 px-2">0.171</td><td className="py-4 px-2">15.1x</td></tr>
                <tr><td className="py-4 px-2 uppercase font-black">Djupn</td><td className="py-4 px-2">0.427</td><td className="py-4 px-2">1.262</td><td className="py-4 px-2">3.0x</td></tr>
                <tr><td className="py-4 px-2 uppercase font-black">Breidde</td><td className="py-4 px-2">0.572</td><td className="py-4 px-2">1.631</td><td className="py-4 px-2">2.9x</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section>
        <h2>2. Teoretisk rammeverk: Fem pilarar for FFF</h2>
        <p>
          <em>Form Follows Fitness</em> (FFF) kviler på fem teoretiske pilarar:
        </p>
        <ol>
          <li><strong>Fitnesslandskapet:</strong> Form som posisjon i eit n-dimensjonalt landskap (Wright, 1932; Kauffman, 1993).</li>
          <li><strong>Distribuert kognisjon:</strong> Intelligens utan sentral styrar (Nakagaki et al., 2000; Levin, 2019).</li>
          <li><strong>Exploration/exploitation:</strong> Veksling mellom utforsking av nytt terreng og utnytting av optima.</li>
          <li><strong>Affordanse:</strong> Kvart material tilbyr ei distinkt formverd (Gibson, 1977).</li>
          <li><strong>Morphospace:</strong> Rommet av alle moglege former (Raup, 1966).</li>
        </ol>
      </section>

      <section className="not-prose my-32">
        <div className="bg-black p-8 md:p-12 lg:p-16 rounded-3xl border border-gray-800 overflow-hidden text-white">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-600 mb-8 text-center">TABELL 2: Mutual Information mellom seleksjonstrykk og form</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs md:text-sm">
              <thead className="border-b-2 border-gray-800">
                <tr>
                  <th className="py-4 px-2">Seleksjonstrykk</th>
                  <th className="py-4 px-2 text-right">Snitt MI (bits)</th>
                  <th className="py-4 px-2 text-right">Relativ styrke</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-900">
                <tr><td className="py-4 px-2 uppercase font-black">Material</td><td className="py-4 px-2 text-right">0.382</td><td className="py-4 px-2 text-right">1.00</td></tr>
                <tr><td className="py-4 px-2 uppercase font-black">Tid (hundreår)</td><td className="py-4 px-2 text-right">0.168</td><td className="py-4 px-2 text-right">0.44</td></tr>
                <tr><td className="py-4 px-2 uppercase font-black">Geografi</td><td className="py-4 px-2 text-right">0.079</td><td className="py-4 px-2 text-right">0.21</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section>
        <h2>3. Diskusjon</h2>
        <p>
          <em>Form Follows Fitness</em> er eit rammeverk der form vert forstått som selektert, ikkje dedusert. Forma på ein stol er ikkje eit logisk svar på spørsmålet "korleis sit ein best?", men eit mellombels optimum i eit fleirdimensjonalt landskap.
        </p>
        <p>
          "Form follows function" er gyldig berre når alle andre seleksjonstrykk er nøytraliserte. Dette er eit degenerert spesialtilfelle som aldri eksisterer i praksis. Våre data viser at dette vilkåret aldri er oppfylt.
        </p>
      </section>

      <section className="border-t-[10px] border-black pt-24">
        <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
        <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
          <p>
            Denne artikkelen har lagt fram empiriske bevis som samla falsifiserer "form follows function" og etablerer <em>Form Follows Fitness</em> som eit fundert alternativ.
          </p>
          <p className="text-black not-italic font-sans font-black text-3xl leading-tight tracking-tight">
            FFF gjer estetisk teori testbar. Fitnesskartet erstattar det modernistiske aksiomet med eit verktøy.
          </p>
        </div>
      </section>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Alexander, C. (1964). <em className="normal-case">Notes on the Synthesis of Form.</em> Harvard University Press.</p>
          <p>Clark, A. (2008). <em className="normal-case">Supersizing the Mind.</em> Oxford University Press.</p>
          <p>Giedion, S. (1948). <em className="normal-case">Mechanization Takes Command.</em> Oxford University Press.</p>
          <p>Kauffman, S. A. (1993). <em className="normal-case">The Origins of Order.</em> Oxford University Press.</p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case">Lippincott's Magazine.</em></p>
          <p>Wright, S. (1932). The roles of mutation, inbreeding, crossbreeding and selection in evolution. <em className="normal-case">Proc. 6th Int. Cong. Genet.</em></p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
