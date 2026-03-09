"use client"

import { useRouter } from "next/navigation"
import ArticleNav from "../../../components/article-nav"

export default function ArticleThreePage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white text-black font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      <header className="max-w-7xl mx-auto pt-48 pb-32 px-6 md:px-12 lg:px-24">
        <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel III</p>
        <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
          Kan form åleine<br/>
          <span className="text-gray-200">fortelje tid?</span>
        </h1>
        <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight max-w-3xl mt-8">
          Materiell-formell kopling i Nasjonalmuseet si stolsamling.
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
            <p className="text-3xl font-sans font-black tracking-tight leading-none uppercase">3D-formanalyse</p>
            <p className="text-sm text-gray-500 font-sans mt-4 leading-relaxed">
              Maskinlæring på tredimensjonale punktskyer frå 401 GLB-modellar.
            </p>
          </div>
        </div>

        <div className="max-w-2xl bg-gray-50 p-8 md:p-12 lg:p-16 rounded-2xl md:rounded-[2rem] border border-gray-100 italic text-base md:text-xl leading-snug text-gray-800 font-serif">
          <strong>Samandrag:</strong> Dersom funksjonalismen sitt dogme stemmer, at form fylgjer funksjon, burde stolar frå ulike nasjonar og tidsaldrar ikkje låt seg skilje geometrisk, sidan sitjefunksjonen er universell. Denne artikkelen testar påstanden empirisk gjennom maskinlæring på tredimensjonale punktsskyer frå 401 GLB-modellar i Nasjonalmuseet si samling. Ved å trekkje ut 21 handlaga geometriske deskriptorar (bounding box, krumming, D2 shape distributions) og 30 binære materialkodar, predikerer me stilperiode med ein makro-F1 på 40,5 ± 6,1 % ved bruk av rein geometri (mot 10,5 % sjanse, p &lt; 0,02), og 47,6 ± 2,6 % med material åleine. Nasjonsprediksjon (Noreg mot utlandet) oppnår 76,0 ± 5,7 % med form og 83,3 ± 3,0 % med material. Funna falsifiserer funksjonalismen si nøytrale formlære: form kodar kulturell identitet og historisk tid romleg og geometrisk.
        </div>
      </header>

      <article className="max-w-2xl mx-auto px-6 md:px-12 lg:px-24 space-y-16 text-base md:text-lg leading-relaxed text-gray-900">
        
        {/* 1. INNLEIING */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">1. Innleiing</h2>
          <p className="mb-8">
            Tidlegare artiklar i denne serien har etablert at materialar ikkje er nøytrale berarar av form, men at dei inkarnerer kolonial handel og tilgangshistorie (Finne, 2026a), og at formutvikling over tid konvergerer mot <em>fitness-optima</em> snarare enn å fylgje ein deterministisk funksjon (Finne, 2026b). Denne tredje delen reiser eit oppfylgjande fundamentalt spørsmål: Dersom ein fjernar overflate, farge og materiale, og <em>berre</em> ser på den nakte geometrien, kan form i seg sjølv bera meining om tid og stad?
          </p>
          <p className="mb-8">
            Spørsmålet har djupe røter i designteorien. Sullivan (1896) formulerte målet <em>form follows function</em>, seinare kanonisert av Le Corbusier (1923) og heile den funksjonalistiske rørsla. Dersom funksjonen til ein stol (ergonomisk støtte for sitjing) er invariant over tid og rom, burde nasjonal opphavsstad og historisk stilperiode vera irrelevante for dei geometriske proposisjonane. Men erfarne kjennarar gjenkjenner ein epoke <em>straks</em>, ofte frå ein silhuett aleine (Lucie-Smith, 1979; Fiell & Fiell, 2005).
          </p>
          <p className="mb-8">
            Dei siste åra har <em>computational cultural heritage</em> vakse fram som eit tverrfagleg forskingsfelt der digitale metodar, som 3D-skanning, statistisk analyse og maskinlæring, vert nytta på kulturhistoriske samlingar (Santos et al., 2017; Manovich, 2020). I dette landskapet tilbyr museumssamlingar med digitaliserte objekt ei unik moglegheit: store nok til statistisk inferens, men kurerte nok til å vera historisk truverdige. Nasjonalmuseet si stolsamling, med over 400 3D-modellerte gjenstandar, er eit ideelt laboratorium for å teste forholdet mellom form og kultur empirisk.
          </p>
          <p>
            Denne studien formulerer fire forskingsspørsmål:
          </p>
          <ol className="list-decimal pl-8 mt-4 space-y-2">
            <li>Kan geometrisk form åleine predikere stilperiode?</li>
            <li>Kan geometrisk form predikere nasjonal opphavstad?</li>
            <li>Korleis interagerer materielle og geometriske trekk i prediksjon?</li>
            <li>Kva geometriske eigenskapar ber mest kulturell informasjon?</li>
          </ol>
        </section>

        {/* 2. FORSKINGSGJENNOMGANG */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">2. Forskingsgjennomgang</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.1 Stilhistorie i møbeldesign</h3>
          <p className="mb-8">
            Den vestlege møbelhistoria vert tradisjonelt organisert i stilperiodar (Renessanse, Barokk, Rokokko, Nyklassisisme, Historisme, Jugend, Modernisme), der kvar epoke vert definert av karakteristiske formtrekk, proporsjonar og dekorstrategiar (Lucie-Smith, 1979). Giedion (1948) viste korleis mekanisering transformerte forholdet mellom handverk og industriell produksjon, noko som endra ikkje berre materialtilgang, men òg kva former som var teknisk møgelege. Fiell & Fiell (2005) dokumenterer korleis stolen, som den mest gjentekne designoppgåva, har fungert som ein seismograf for kulturelle skifte gjennom meir enn 500 år.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.2 3D formanalyse og shape distributions</h3>
          <p className="mb-8">
            Datamaskinbasert formanalyse har utvikla seg frå statistiske deskriptorar til djuplæring. Osada et al. (2002) introduserte <em>shape distributions</em>, det vil seie sannsynsfordelingar av geometriske mål (punkt-til-punkt-avstandar, areal, volum), som eit rotasjonsinvariant fingeravtrykk for 3D-form. Seinare har Wu et al. (2015) vist at djupe nett kan lære volumetriske representasjonar direkte, medan Su et al. (2015) demonstrerte at multi-view-bilete kan fange kompleks formvariasjon. For små og mellomstore datasett, slik som våre ca. 400 stolar, kan robuste handlaga features likevel konkurrere med djuplæringsmetodar, særleg når tolkbarheit er viktig.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.3 Maskinlæring for kulturarvsdata</h3>
          <p className="mb-8">
            Manovich (2020) argumenterer for at kulturanalyse (<em>cultural analytics</em>), det vil seie bruk av statistikk og maskinlæring på store kulturelle datasett, avslører mønster som kvalitativ lesing åleine ikkje kan fange. Santos et al. (2017) gjennomgår korleis 3D-digitalisering av kulturarvsobjekt har mogeleggjort nye former for komparativ analyse. Vår studie koplar desse tradisjonane: me nyttar 3D-punktsskyer frå eit museumsdatasett med etablerte stilmerke for å kvantifisere forholdet mellom geometri, material og kulturell tilhøyrsle.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">2.4 Materiell-formell kopling</h3>
          <p>
            Finne (2026a) synte at material i museumssamlingar er bunde til spesifikke nasjonaløkonomiske omstende; mahogni markerer internasjonale handelsnettverk, medan furu indikerer nordiske produksjonstilhøve. Ingold (2007) argumenterer for at materialar ikkje er passive substrat, men aktive aktørar som <em>tvingar</em> visse former fram: bøyd bøk auka sannsynet for sirkulære former, medan massivt eik disponerer for rektangulær konstruksjon. Miller (2005) utvidar dette perspektivet til ein generell teori om materialitet der objekt og material konstituerer kvarandre gjensidig. Gibson (1977) sitt omgrep <em>affordances</em> gjev eit teoretisk rammeverk for kvifor me kan forvente systematisk kovarians mellom geometri og material. Dermed vert ikkje form berre "form"; den vert eit symptom på ei underliggjande materiell-formell kopling.
          </p>
        </section>

        {/* 3. METODE */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">3. Metode</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">3.1 Datasett og punktskyutrekk</h3>
          <p className="mb-8">
            Datamaterialet består av 408 stolar frå Nasjonalmuseet si digitalsamling, der 401 har tilgjengelege GLB-modellar. Kvar modell vart normalisert med biblioteket Trimesh: me sampla 2 048 punkt uniformt frå overflata, flytta kvar sky til origo, og skalerte til einingsvolum for å sikre skalauavhengigheit. Av dei 401 stolane har 229 eit registrert stilmerke som let seg gruppere i åtte hovudperiodar; 349 har registrert produksjonsstad.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">3.2 Trekkekstraksjon</h3>
          <p className="mb-4">Me trekte ut to sett med deskriptorar:</p>
          <p className="mb-4"><strong>Geometriske trekk</strong> (21 variablar) frå punktskyene:</p>
          <ul className="list-disc pl-8 mb-8 space-y-2">
            <li><strong>Bounding box og aspekt:</strong> Høgde, breidde, djupn (H, W, D) og aspektratioar (H/W, D/W).</li>
            <li><strong>PCA-eigenverdiar:</strong> Eigenverdiratioar (λ2/λ1, λ3/λ1) som måler formfordeling langs prinsipale aksar.</li>
            <li><strong>Konveks skrog:</strong> Kompaktheit (skrogvolum / bbox-volum) og overflateratio.</li>
            <li><strong>D2-distribusjon:</strong> Fem histogram-bins for den innbyrdes avstandsfordelinga mellom tilfeldige overflatepunktpar.</li>
            <li><strong>Høgdefordeling og krumming:</strong> Massefordeling (botn/midt/topp), symmetriscore, gjennomsnittleg og standardavvik for estimert krumming.</li>
          </ul>
          <p className="mb-8"><strong>Materialtrekk</strong> (30 variablar): Binære kodingar av dei 30 mest førekomande materialane (t.d. Nøttetre, Furu, Mahogni, Stål, Lær).</p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">3.3 Klassifiseringseksperiment</h3>
          <p className="mb-8">
            Me nytta <em>Random Forest</em> (Breiman, 2001) med 100 tre og balansert klassevekt, evaluert med stratifisert 5-fold kryssvalidering. Makro-F1 vart brukt som hovudmetrikk for å handtere ubalanserte klassar. Permutasjonstest (n=50) etablerte statistisk signifikans. Eksperiment A testa stilprediksjon (8 klassar), og Eksperiment B testa nasjonsprediksjon (Noreg mot utlandet).
          </p>
        </section>

        {/* TABELL 1 */}
        <section className="py-12 full-bleed">
          <div className="bg-gray-50 p-8 md:p-12 lg:p-16 rounded-2xl md:rounded-[3rem] border border-gray-100 overflow-hidden">
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
                  <tr><td className="py-4 px-2 uppercase font-black">Nyklassisisme</td><td className="py-4 px-2 text-right">68</td><td className="py-4 px-2 text-right">29,7 %</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Barokk</td><td className="py-4 px-2 text-right">51</td><td className="py-4 px-2 text-right">22,3 %</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Historisme</td><td className="py-4 px-2 text-right">29</td><td className="py-4 px-2 text-right">12,7 %</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Rokokko</td><td className="py-4 px-2 text-right">22</td><td className="py-4 px-2 text-right">9,6 %</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Modernisme</td><td className="py-4 px-2 text-right">21</td><td className="py-4 px-2 text-right">9,2 %</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Postmodernisme</td><td className="py-4 px-2 text-right">17</td><td className="py-4 px-2 text-right">7,4 %</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Renessanse</td><td className="py-4 px-2 text-right">11</td><td className="py-4 px-2 text-right">4,8 %</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Jugend</td><td className="py-4 px-2 text-right">10</td><td className="py-4 px-2 text-right">4,4 %</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* 4. RESULTAT */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">4. Resultat</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.1 Formrommet og stilklynging</h3>
          <p className="mb-8">
            Ein UMAP-projeksjon av dei 229 stilmerka stolane langs dei 21 geometriske variablane syner at sjølv fritatt all reell dimensjon og material, i ei naken matematisk form, ser me klynger der Barokk og Modernisme skil seg ut, medan overgangsstilar overlappar. Den låge silhouette-scoren (-0,012 i 21D) stadfestar at klyngene ikkje er skarpt separerte, men det vesentlege er at strukturen likevel fangar systematiske mønster: nærliggjande punkt tenderer til å dele stilperiode.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.2 Hovudresultat: Stil- og nasjonsprediksjon</h3>
          <p className="mb-8">
            Geometri åleine predikerer stil nesten fire gonger betre enn sjansen (40,5 % mot 10,5 %), og nasjon med 76,0 % F1 (mot 46,3 % sjanse). Forvirringsmatrisa avdekker at Historisme hyppig vert forveksla med Barokk og Nyklassisisme, stilar den bevisst imiterte (Nybarokk, Nyrokokko). Dette er ikkje ein algoritmisk feil, men ein refleksjon av at Historismen sitt formprosjekt <em>var</em> å resirkulere tidlegare geometriar.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.3 Per-klasse F1-analyse</h3>
          <p className="mb-4">Resultata avdekker store variasjonar mellom stilgruppene:</p>
          <ul className="list-disc pl-8 mb-8 space-y-2">
            <li><strong>Barokk og Nyklassisisme:</strong> Lettast å klassifisere geometrisk (F1 = 0,78 og 0,73).</li>
            <li><strong>Modernisme:</strong> Oppnår stabil F1 (~0,52) på tvers av alle trekksett, noko som tyder på ein koherent og unik formsignatur.</li>
            <li><strong>Historisme:</strong> Presterer dårleg geometrisk (F1 = 0,22) men betrakteleg betre med material (0,44).</li>
            <li><strong>Jugend og Postmodernisme:</strong> For små eller heterogene til å fange med 21 handlaga trekk.</li>
          </ul>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">4.4 Kombinert-underprestasjonsparadokset</h3>
          <p>
            Eit uventa resultat er at det kombinerte trekksettet (geometri + material) <em>underpresterer</em> material åleine for stilprediksjon (F1 = 0,463 mot 0,476). Korrelasjonsanalysen gjev forklaringa: systematisk Pearson-kovarians mellom geometri- og materialfeatures (maks |r| = 0,33). Når features frå begge sett vert slegne saman utan seleksjon, fører den redundante informasjonen til auka dimensjonalitet utan proporsjonalt auka prediktiv kraft. Paradokset er i seg sjølv eit bevis: redundansen mellom dei to trekksetta <em>er</em> den materiell-formelle koplinga.
          </p>
        </section>

        {/* TABELL 2 */}
        <section className="py-12 full-bleed">
          <div className="bg-black p-8 md:p-12 lg:p-16 rounded-2xl md:rounded-[3rem] border border-gray-800 overflow-hidden text-white">
            <h4 className="text-[10px] font-mono font-black uppercase tracking-[0.4em] text-gray-600 mb-8 text-center">TABELL 2: Klassifikasjonsresultat (makro-F1)</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs md:text-sm">
                <thead className="border-b-2 border-gray-800">
                  <tr>
                    <th className="py-4 px-2">Oppgåve</th>
                    <th className="py-4 px-2 text-right">Geometri</th>
                    <th className="py-4 px-2 text-right">Material</th>
                    <th className="py-4 px-2 text-right">Kombinert</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-900">
                  <tr><td className="py-4 px-2 uppercase font-black">Stil (8 klassar)</td><td className="py-4 px-2 text-right">0,405</td><td className="py-4 px-2 text-right">0,476</td><td className="py-4 px-2 text-right">0,463</td></tr>
                  <tr><td className="py-4 px-2 uppercase font-black">Nasjon (NO/Utland)</td><td className="py-4 px-2 text-right">0,760</td><td className="py-4 px-2 text-right">0,833</td><td className="py-4 px-2 text-right">0,781</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* 5. DISKUSJON */}
        <section>
          <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">5. Diskusjon</h2>
          
          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">5.1 Form som kulturell kode</h3>
          <p className="mb-8">
            Hovudfunnet er at geometrisk form, frigjort frå overflate, farge og material, kodar både historisk stilperiode og nasjonal opphavstad med signifikant presisjon. At ein Random Forest kan predikere stilperiode nesten fire gonger betre enn slump frå 21 enkle geometriske mål, tyder på at kulturelle konvensjonar er djupt innskrivne i dei rommelege proposisjonane til ein stol. Ingold (2007) argumenterer for at materialar "fortel" gjennom sine affordances; våre resultat utvidar dette: òg den reine geometrien fortel, uavhengig av kva tre eller metall som ber den.
          </p>
          <p className="mb-8">
            Dette rokkar tungt ved modernismens teoretiske rammeverk. Om <em>form follows function</em> heldt stikk, skulle ikkje ei norsk punktsky slå annleis inn i geometriske deskriptorar enn ei dansk eller fransk. Likevel oppnår me 76 % prediksjon berre frå geometri. Nasjonale ergonomiske trendar, teknologiske avgrensingar og lokale produksjonsmaskineri tvingar seg igjennom og vert synlege i den geometriske signaturen. Me kallar dette <em>materiell-formell kopling</em>: forma av eit tre inni ein stol fortel historia tvers igjennom.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">5.2 Historisme-paradokset</h3>
          <p className="mb-8">
            At modellen feilar mest på Historisme (F1 = 0,22 geometrisk) er i seg sjølv eit funn. Historismen, med sine Nybarokk- og Nyrokokkostolar, var eit medvite program for å gjenskape tidlegare formuttrykk. At algoritmen forvekslar Historisme med Barokk er då ikkje ein feil, men ein kvantitativ validering av kunsthistoria: den geometriske imitasjonen <em>verka</em>. Materialet, som avslører at Historismestolar nyttar andre treslag enn dei originale, er derimot ein betre diskriminant (F1 = 0,44). Her er det nettopp materialiteten som avslører epoken, ikkje forma.
          </p>

          <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">5.3 Kombinert-paradokset som bevis</h3>
          <p>
            At kombinerte trekksett underpresterer enkle sett er kontraintuitivt, men forklarleg: korrelasjonsanalysen dokumenterer systematisk kovarians mellom geometri og material. Mahogni korrelerer med høgare symmetriscore (r = 0,31); lær korrelerer med smalare proporsjonar (r = 0,33 for H/W). Desse relasjonane reflekterer affordances: materialet <em>disponerer</em> forma. Når begge trekksett inngår utan seleksjon, fører redundansen til auka støy i eit allereie lite datasett. Men sjølve redundansen er det viktigaste funnet: geometri og material er ikkje uavhengige dimensjonar, men to uttrykk for same underliggjande materiell-formelle struktur.
          </p>
        </section>

        {/* KONKLUSJON */}
        <section className="border-t-[10px] border-black pt-24">
          <h2 className="text-6xl font-sans font-black text-black mb-12 tracking-tighter uppercase italic leading-none">Konklusjon.</h2>
          <div className="space-y-12 text-gray-600 italic font-serif leading-relaxed">
            <p>
              Gjennom ei systematisk maskinlæringsanalyse av 401 unike historiske stolar har denne studien vist at 3D geometrisk form åleine kan predikere stilperiode med 40,5 % F1 og nasjonal opphavstad med 76,0 % F1.
            </p>
            <p>
              Per-klasse-analysen avdekker at Barokk og Nyklassisisme har dei sterkaste geometriske signaturane, medan Historismens geometriske forvirring validerer kunsthistoria kvantitativt. Det kombinerte trekksettet underpresterer enkle sett fordi geometri og material kovarierer systematisk; redundansen <em>er</em> den materiell-formelle koplinga.
            </p>
            <p className="text-black not-italic font-sans font-black text-3xl leading-tight tracking-tight">
              Funksjonalismen kan ikkje forklare at nasjonalitet er gøymt i proporsjonale utbøyingar av ein rygg, men <em>form follows fitness</em>-rammeverket kan. Form kodar kultur, og kulturen sit djupt i treverket og geometrien.
            </p>
          </div>
        </section>
      </article>

      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Alexander, C. (1964). <em className="normal-case tracking-normal">Notes on the Synthesis of Form.</em> Harvard University Press.</p>
          <p>Corbusier, Le (1923). <em className="normal-case tracking-normal">Vers une architecture.</em> Cres.</p>
          <p>Fiell, C., & Fiell, P. (2005). <em className="normal-case tracking-normal">1000 Chairs.</em> Taschen.</p>
          <p>Finne, I. R. (2026a). <em className="normal-case tracking-normal">Materialhistorie: Kolonialt arkiv.</em> AHO Working Paper.</p>
          <p>Finne, I. R. (2026b). <em className="normal-case tracking-normal">Form follows fitness.</em> AHO Working Paper.</p>
          <p>Giedion, S. (1948). <em className="normal-case tracking-normal">Mechanization Takes Command.</em> Oxford University Press.</p>
          <p>Ingold, T. (2007). Materials against materiality. <em className="normal-case tracking-normal">Archaeological Dialogues,</em> 14(1), 1-16.</p>
          <p>Lucie-Smith, E. (1979). <em className="normal-case tracking-normal">A History of Furniture.</em> William Morrow.</p>
          <p>Manovich, L. (2020). <em className="normal-case tracking-normal">Cultural Analytics.</em> MIT Press.</p>
          <p>Osada, R. et al. (2002). Shape distributions. <em className="normal-case tracking-normal">ACM Transactions on Graphics,</em> 21(4), 807-832.</p>
          <p>Santos, P. et al. (2017). 3D digitisation of cultural heritage. <em className="normal-case tracking-normal">Digital Heritage,</em> 413-432.</p>
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
