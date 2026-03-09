"use client"

import { useRouter } from "next/navigation"
import ArticleNav from "../../../components/article-nav"

export default function ArticleThreePage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      <header className="max-w-5xl mx-auto pt-48 pb-32 px-8">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel III</p>
        <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Kan form åleine<br/>
          <span className="text-gray-200">fortelje tid?</span>
        </h1>
        <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight max-w-3xl mt-8">
          Materiell-formell kopling i Nasjonalmuseet si stolsamling.
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
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">3D-formanalyse</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Maskinlæring på tredimensjonale punktskyer frå 401 GLB-modellar.
            </p>
          </div>
        </div>

        <div className="max-w-3xl bg-gray-50 p-6 md:p-12 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100 italic text-lg md:text-2xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> Dersom funksjonalismen sitt dogme stemmer, at form fylgjer funksjon, burde stolar frå ulike nasjonar og tidsaldrar ikkje låt seg skilje geometrisk, sidan sitjefunksjonen er universell. Denne artikkelen testar påstanden empirisk gjennom maskinlæring på tredimensjonale punktsskyer frå 401 GLB-modellar i Nasjonalmuseet si samling. Ved å trekkje ut 21 geometriske deskriptorar predikerer me stilperiode med ein makro-F1 på 40,5% ved bruk av rein geometri (mot 10,5% sjanse), og 47,6% med material åleine. Nasjonsprediksjon oppnår 76,0% med form og 83,3% med material. Funna falsifiserer funksjonalismen si nøytrale formlære: form kodar kulturell identitet og historisk tid romleg og geometrisk.
        </div>
      </header>

      <article className="max-w-3xl mx-auto px-8 space-y-24 text-lg md:text-2xl leading-relaxed text-gray-900">
        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">1. Innleiing</h2>
          <p className="mb-12">
            Tidlegare artiklar i denne serien har etablert at materialar ikkje er nøytrale berarar av form, men at dei inkarnerer kolonial handel og tilgangshistorie, og at formutvikling over tid konvergerer mot fitness-optima snarare enn å fylgje ein deterministisk funksjon. Denne tredje delen reiser eit oppfylgjande fundamentalt spørsmål: Dersom ein fjernar overflate, farge og materiale, og berre ser på den nakte geometrien, kan form i seg sjølv bera meining om tid og stad?
          </p>
          <p>
            Spørsmålet har djupe røter i designteorien. Sullivan formulerte målet <em>form follows function</em>, seinare kanonisert av Le Corbusier og heile den funksjonalistiske rørsla. Dersom funksjonen til ein stol er invariant over tid og rom, burde nasjonal opphavsstad og historisk stilperiode vera irrelevante for dei geometriske proposisjonane. Men erfarne kjennarar gjenkjenner ein epoke straks, ofte frå ein silhuett aleine.
          </p>
        </section>

        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">2. Metode</h2>
          <p className="mb-12">
            Datamaterialet består av 401 stolar med tilgjengelege GLB-modellar frå Nasjonalmuseet. Kvar modell vart normalisert: me sampla 2 048 punkt uniformt frå overflata, flytta kvar sky til origo, og skalerte til einingsvolum for å sikre skalauavhengigheit.
          </p>
          <p className="mb-12">
            Me trekte ut to sett med deskriptorar: 21 geometriske variablar (bounding box, PCA-eigenverdiar, konveks skrog, D2-distribusjon, krumming) og 30 materialtrekk (binære kodingar av dei mest førekomande materialane).
          </p>
          <p>
            Me nytta <em>Random Forest</em> med 100 tre for klassifisering, evaluert med stratifisert 5-fold kryssvalidering. Makro-F1 vart brukt som hovudmetrikk.
          </p>
        </section>

        <section className="py-12 full-bleed">
          <div className="bg-gray-50 p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] border border-gray-100 overflow-hidden">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-300 mb-16 text-center">TABELL 1: Klassefordeling for stilprediksjon (n = 229)</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-sm">
                <thead className="border-b-2 border-black">
                  <tr>
                    <th className="py-4 px-2">Stilgruppe</th>
                    <th className="py-4 px-2">Antal</th>
                    <th className="py-4 px-2">Andel</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr><td className="py-4 px-2 uppercase font-black">Nyklassisisme</td><td className="py-4 px-2">68</td><td className="py-4 px-2">29,7%</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Barokk</td><td className="py-4 px-2">51</td><td className="py-4 px-2">22,3%</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Historisme</td><td className="py-4 px-2">29</td><td className="py-4 px-2">12,7%</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Rokokko</td><td className="py-4 px-2">22</td><td className="py-4 px-2">9,6%</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Modernisme</td><td className="py-4 px-2">21</td><td className="py-4 px-2">9,2%</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Postmodernisme</td><td className="py-4 px-2">17</td><td className="py-4 px-2">7,4%</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Renessanse</td><td className="py-4 px-2">11</td><td className="py-4 px-2">4,8%</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Jugend</td><td className="py-4 px-2">10</td><td className="py-4 px-2">4,4%</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">3. Resultat</h2>
          <p className="mb-12">
            Geometri åleine predikerer stil nesten fire gonger betre enn sjansen (40,5% mot 10,5%), og nasjon med 76,0% F1 (mot 46,3% sjanse). Barokk og Nyklassisisme er lettast å klassifisere geometrisk (F1 = 0,78 og 0,73), truleg fordi dei har distinkte proporsjonar.
          </p>
          <p className="mb-12">
            Eit uventa resultat er at det kombinerte trekksettet (geometri + material) <em>underpresterer</em> material åleine for stilprediksjon (F1 = 0,463 mot 0,476). Korrelasjonsanalysen gjev forklaringa: systematisk kovarians mellom geometri- og materialfeatures. Redundansen mellom dei to trekksetta <em>er</em> den materiell-formelle koplinga.
          </p>
          <p>
            Forvirringsmatrisa avdekker at Historisme hyppig vert forveksla med Barokk og Nyklassisisme, stilar den bevisst imiterte. Dette er ein kvantitativ validering av kunsthistoria: den geometriske imitasjonen verka.
          </p>
        </section>

        <section className="py-12 full-bleed">
          <div className="bg-black p-4 md:p-12 lg:p-24 rounded-2xl md:rounded-[4rem] border border-gray-800 overflow-hidden text-white">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-600 mb-16 text-center">TABELL 2: Klassifikasjonsresultat (makro-F1)</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-sm">
                <thead className="border-b-2 border-gray-800">
                  <tr>
                    <th className="py-4 px-2">Oppgåve</th>
                    <th className="py-4 px-2">Geometri</th>
                    <th className="py-4 px-2">Material</th>
                    <th className="py-4 px-2">Kombinert</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-900">
                  <tr><td className="py-4 px-2 uppercase font-black">Stil (8 klassar)</td><td className="py-4 px-2">0,405</td><td className="py-4 px-2">0,476</td><td className="py-4 px-2">0,463</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Nasjon (NO/Utland)</td><td className="py-4 px-2">0,760</td><td className="py-4 px-2">0,833</td><td className="py-4 px-2">0,781</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-3xl md:text-5xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic">4. Diskusjon</h2>
          <p className="mb-12">
            Hovudfunnet er at geometrisk form, frigjort frå overflate, farge og material, kodar både historisk stilperiode og nasjonal opphavstad med signifikant presisjon. Dette rokkar tungt ved modernismens teoretiske rammeverk. Om <em>form follows function</em> heldt stikk, skulle ikkje ei norsk punktsky slå annleis inn i geometriske deskriptorar enn ei dansk eller fransk.
          </p>
          <p>
            Nasjonale ergonomiske trendar, teknologiske avgrensingar og lokale produksjonsmaskineri tvingar seg igjennom og vert synlege i den geometriske signaturen. Me kallar dette <em>materiell-formell kopling</em>: forma av eit tre inni ein stol fortel historia tvers igjennom.
          </p>
        </section>

        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
            <p>
              Gjennom ei systematisk maskinlæringsanalyse av 401 unike historiske stolar har denne studien vist at 3D geometrisk form åleine kan predikere stilperiode og nasjonal opphavstad.
            </p>
            <p>
              Funksjonalismen kan ikkje forklare at nasjonalitet er gøymt i proporsjonale utbøyingar av ein rygg, men <em>form follows fitness</em>-rammeverket kan. Form kodar kultur, og kulturen sit djupt i treverket og geometrien.
            </p>
          </div>
        </section>
      </article>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Corbusier, Le (1923). <em className="normal-case tracking-normal">Vers une architecture.</em> Cres.</p>
          <p>Finne, I. R. (2026a). <em className="normal-case tracking-normal">Materialhistorie: Kolonialt arkiv.</em> AHO Working Paper.</p>
          <p>Finne, I. R. (2026b). <em className="normal-case tracking-normal">Form follows fitness.</em> AHO Working Paper.</p>
          <p>Manovich, L. (2020). <em className="normal-case tracking-normal">Cultural Analytics.</em> MIT Press.</p>
          <p>Osada, R. et al. (2002). Shape distributions. <em className="normal-case tracking-normal">ACM Transactions on Graphics,</em> 21(4), 807-832.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </div>
  )
}
