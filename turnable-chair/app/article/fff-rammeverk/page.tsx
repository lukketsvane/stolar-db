"use client"

import { useRouter } from "next/navigation"
import ArticleNav from "../../../components/article-nav"

export default function ArticleFourPage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      <header className="max-w-5xl mx-auto pt-48 pb-32 px-8">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel IV</p>
        <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Form Follows<br/>
          <span className="text-gray-200">Fitness.</span>
        </h1>
        <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight max-w-3xl mt-8">
          Empirisk grunnlag for eit evolusjonært rammeverk i estetiske fag.
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
            <p className="text-[10px] font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">Informasjonsteori</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Analyse av 93 stolar gjennom 21 geometriske og 30 materielle eigenskapar.
            </p>
          </div>
        </div>

        <div className="max-w-3xl bg-gray-50 p-6 md:p-12 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100 italic text-lg md:text-2xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> Det modernistiske dogmet "form follows function" impliserer at form er deduserbar frå funksjon. Denne artikkelen falsifiserer dette empirisk ved å analysere 93 stolar frå Nasjonalmuseet si samling. Analysen viser at funksjon er konstant, medan form varierer radikalt. Informasjonsteoretisk analyse avdekkjer at material ber fem gonger meir informasjon om geometrisk form enn geografi. Artikkelen presenterer <em>Form Follows Fitness</em> (FFF), eit nytt rammeverk der form vert forstått som selektert av eit fleirdimensjonalt fitnesslandskap av materialaffordanse, teknologi, økonomi, geografi og kultur.
        </div>
      </header>

      <article className="max-w-3xl mx-auto px-8 space-y-24 text-lg md:text-2xl leading-relaxed text-gray-900">
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">1. Innleiing</h2>
          <p className="mb-12">
            I over eit hundreår har Louis Sullivan sitt "form ever follows function" fungert som det avgjerande aksiomet i formgjevingsfaga. Le Corbusier bygde ein heil arkitektonisk doktrine på premissen. Implikasjonen er deterministisk: gjev ein spesifikk funksjon, finst det ei optimal form. Men stemmer dette empirisk?
          </p>
          <p>
            Denne artikkelen nyttar Nasjonalmuseet si stolsamling som eit kontrollert eksperiment. Alle objekt i databasen delar same funksjon: å sitte på. Dersom form fylgjer funksjon, burde formvariasjonen vore liten. Ho er i staden enorm.
          </p>
        </section>

        <section className="py-12 full-bleed">
          <div className="bg-white p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] border border-gray-100 shadow-sm overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">TABELL 1: Formvariasjon blant 93 stolar med identisk funksjon</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-sm">
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
                  <tr><td className="py-4 px-2 uppercase font-black">Kompaktheit</td><td className="py-4 px-2">0.274</td><td className="py-4 px-2">0.725</td><td className="py-4 px-2">2.6x</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">2. Dei fem pilarane</h2>
          <p className="mb-12">
            <em>Form Follows Fitness</em> (FFF) kviler på fem teoretiske pilarar:
          </p>
          <div className="space-y-12 my-12 border-l-4 border-black pl-12">
            <p><strong>I. Fitnesslandskapet:</strong> Form som posisjon i eit n-dimensjonalt landskap. Stilar er lokale toppunkt.</p>
            <p><strong>II. Distribuert kognisjon:</strong> Intelligens treng ikkje ein sentral styrar. Materialet "veit" kva det toler.</p>
            <p><strong>III. Exploration/exploitation:</strong> Designhistoria vekslar mellom utforsking av nytt terreng og utnytting av kjende optimum.</p>
            <p><strong>IV. Affordanse:</strong> Kvart material tilbyr ei distinkt formverd, ikkje passivt men aktivt.</p>
            <p><strong>V. Morphospace:</strong> Rommet av alle moglege former, der faktiske objekt okkuperer avgrensa regionar.</p>
          </div>
        </section>

        <section className="py-12 full-bleed">
          <div className="bg-black p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] border border-gray-800 overflow-hidden text-white">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-600 mb-16 text-center">TABELL 2: Mutual Information mellom seleksjonstrykk og form</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-sm">
                <thead className="border-b-2 border-gray-800">
                  <tr>
                    <th className="py-4 px-2">Seleksjonstrykk</th>
                    <th className="py-4 px-2">Snitt MI (bits)</th>
                    <th className="py-4 px-2">Relativ styrke</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-900">
                  <tr><td className="py-4 px-2 uppercase font-black">Material</td><td className="py-4 px-2">0.382</td><td className="py-4 px-2">1.00</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Tid (hundreår)</td><td className="py-4 px-2">0.168</td><td className="py-4 px-2">0.44</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Geografi (opphav)</td><td className="py-4 px-2">0.079</td><td className="py-4 px-2">0.21</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">3. Diskusjon</h2>
          <p className="mb-12">
            <em>Form Follows Fitness</em> er eit rammeverk der form vert forstått som selektert, ikkje dedusert. Forma på ein stol er ikkje eit logisk svar på spørsmålet "korleis sit ein best?", men eit mellombels optimum i eit fleirdimensjonalt landskap definert av materialaffordanse, temporalt trykk og geografi.
          </p>
          <p>
            "Form follows function" er gyldig berre når alle andre seleksjonstrykk er nøytraliserte. Dette er eit degenerert spesialtilfelle som aldri eksisterer i praksis. FFF generaliserer funksjonalismen: Sullivan og Le Corbusier sine prinsipp er spesialtilfelle der MI for material, tid og geografi er lik null. Våre data viser at dette vilkåret aldri er oppfylt.
          </p>
        </section>

        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
            <p>
              Denne artikkelen har lagt fram åtte empiriske bevis som samla falsifiserer "form follows function" og etablerer <em>Form Follows Fitness</em> som eit empirisk fundert alternativ.
            </p>
            <p className="text-black not-italic font-sans font-black text-3xl leading-tight tracking-tight">
              FFF gjer estetisk teori testbar. Rammeverket er ikkje ein filosofisk posisjon, men ein empirisk modell, open for falsifisering og operativ for designpraksis.
            </p>
          </div>
        </section>
      </article>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Alexander, C. (1964). <em className="normal-case tracking-normal">Notes on the Synthesis of Form.</em> Harvard University Press.</p>
          <p>Giedion, S. (1948). <em className="normal-case tracking-normal">Mechanization Takes Command.</em> Oxford University Press.</p>
          <p>Kauffman, S. A. (1993). <em className="normal-case tracking-normal">The Origins of Order.</em> Oxford University Press.</p>
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
