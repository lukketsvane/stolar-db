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
        <strong>Samandrag:</strong> Dersom funksjonalismen sitt dogme stemmer, at form fylgjer funksjon, burde stolar frå ulike nasjonar og tidsaldrar ikkje låt seg skilje geometrisk.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing</h2>
        <p>
          Tidlegare artiklar i denne serien har etablert at materialar ikkje er nøytrale berarar av form, men at dei inkarnerer kolonial handel og tilgangshistorie (Finne, 2026a).
        </p>
        <p>
          Denne studien formulerer fire forskingsspørsmål:
        </p>
        <ol>
          <li>Kan geometrisk form åleine predikere stilperiode?</li>
          <li>Kan geometrisk form predikere nasjonal opphavstad?</li>
          <li>Korleis interagerer materielle og geometriske trekk i prediksjon?</li>
          <li>Kva geometriske eigenskapar ber mest kulturell informasjon?</li>
        </ol>
      </section>

      <section>
        <h2>2. Forskingsgjennomgang</h2>
        <h3>2.1 Stilhistorie i møbeldesign</h3>
        <p>
          Den vestlege møbelhistoria vert tradisjonelt organisert i stilperiodar (Renessanse, Barokk, Rokokko, Nyklassisisme, Historisme, Jugend, Modernisme).
        </p>
      </section>

      <section className="not-prose my-32">
        <div className="bg-white p-8 md:p-12 lg:p-16 rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-8 text-center">TABELL 1: Klassefordeling for stilprediksjon (n = 229)</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs md:text-sm">
              <thead className="border-b-2 border-black">
                <tr>
                  <th className="py-4 px-2">Stilgruppe</th>
                  <th className="py-4 px-2 text-right">Antal</th>
                  <th className="py-4 px-2 text-right">Andel</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                <tr><td className="py-4 px-2 font-black uppercase">Nyklassisisme</td><td className="py-4 px-2 text-right">68</td><td className="py-4 px-2 text-right">29,7 %</td></tr>
                <tr><td className="py-4 px-2 font-black uppercase">Barokk</td><td className="py-4 px-2 text-right">51</td><td className="py-4 px-2 text-right">22,3 %</td></tr>
                <tr><td className="py-4 px-2 font-black uppercase">Historisme</td><td className="py-4 px-2 text-right">29</td><td className="py-4 px-2 text-right">12,7 %</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section>
        <h2>3. Metode</h2>
        <p>
          Datamaterialet består av 401 stolar med tilgjengelege GLB-modellar. Kvar modell vart normalisert: me sampla 2 048 punkt uniformt frå overflata.
        </p>
      </section>

      <section>
        <h2>4. Resultat</h2>
        <p>
          Geometri åleine predikerer stil nesten fire gonger betre enn sjansen (40,5 % mot 10,5 %), og nasjon med 76,0 % F1.
        </p>
      </section>

      <section className="not-prose my-32">
        <div className="bg-black p-8 md:p-12 lg:p-16 rounded-3xl border border-gray-800 overflow-hidden text-white">
          <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-600 mb-8 text-center">TABELL 2: Klassifikasjonsresultat (makro-F1)</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs md:text-sm">
              <thead className="border-b-2 border-gray-800">
                <tr>
                  <th className="py-4 px-2">Oppgåve</th>
                  <th className="py-4 px-2 text-right">Geometri</th>
                  <th className="py-4 px-2 text-right">Material</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-900">
                <tr><td className="py-4 px-2 font-black uppercase">Stil</td><td className="py-4 px-2 text-right">0,405</td><td className="py-4 px-2 text-right">0,476</td></tr>
                <tr><td className="py-4 px-2 font-black uppercase">Nasjon</td><td className="py-4 px-2 text-right">0,760</td><td className="py-4 px-2 text-right">0,833</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section>
        <h2>Konklusjon</h2>
        <p>
          Funksjonalismen kan ikkje forklare at nasjonalitet er gøymt i proporsjonale utbøyingar av ein rygg, men <em>form follows fitness</em>-rammeverket kan.
        </p>
      </section>

      <footer className="mt-32 pt-16 border-t border-gray-100 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
        <p>&copy; 2026 Iver Raknes Finne</p>
        <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
      </footer>
    </ArticleLayout>
  )
}
