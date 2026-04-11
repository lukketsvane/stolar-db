# -*- coding: utf-8 -*-
import re
import sys

# A mapping of proposition IDs to their abstract, implicit footnotes.
footnotes_mapping = {
    # Chap 1
    "1.1": "Dette gjeld formelt uavhengig av om konfigurasjonen er fysisk materie, informasjonsarkitektur i ei programvare, eller eit sekvensielt tenesteforløp.",
    "1.11": "Identiteten til eit system er uttømmande definert av konfigurasjonen til komponentane sine i det augneblikket.",
    "1.121": "Relasjonen konstituerer ei interaksjonsflate: det realiserte står i konstant spenning til det latente.",
    "1.1211": "Eigenskapen oppstår i differansen mellom tilstandane, analogt med korleis eit digitalt grensesnitt får form gjennom tilstandar det utelukkar.",
    "1.2": "Objektet er ikkje nødvendigvis romleg; i eit distribuert nettverk er objektet ein udeleleg datapakke eller ei atomær hending.",
    "1.21": "Udelelegheit tyder her at vidare dekomponering øydelegg objektets kausale funksjon i den gjevne lyskjegla.",
    "1.211": "Substansen gjev repertoaret for kva tenester eller interaksjonar som overhovudet kan oppstå.",
    "1.2111": "Ein protokoll innheld potensialet for alle framtidige transaksjonar, allereie før første transaksjon er eksekvert.",
    "1.21111": "Grammatikken for grensesnittet er uavhengig av brukarintensjonen.",
    "1.22": "Konfigurasjonen er reglane for samanføyning, isomorf med syntaksen i eit kodespråk.",
    "1.221": "Strukturen ber informasjonen. Geometrien er berre eitt mogleg substrat for struktur.",
    "1.3": "Formrommet generaliserer mogleikane: det kan skildre alt frå topologien i eit API til faserommet i eit maskinlæringssamfunn.",
    "1.31": "Tilstandsrommet i eit digitalt system tilordnar kvar unik konfigurasjon ein eksakt og reversibel koordinat.",
    "1.32": "Projeksjonen er uunngåeleg når n-dimensjonale system (som brukaropplevingar) vert reduserte til lågdimensjonale beregningar (som konverteringsratar).",
    "1.3211": "Optimalisering av éin metrikk i eit system skjuler alltid degenerering av andre, unytta relasjonar.",
    "1.32112": "Grensesnittet sitt utsjånad er ein projeksjon; den underliggande algoritmens tilstand utgjer sjølve forma.",
    "1.33": "Klassen definerer handlingsrommet. I tenestedesign svarer dette til domeneavgrensinga systemet opererer innafor.",
    "1.331": "Brukarmønster og tekniske flaskehalsar utgjer seleksjonstrykka som modellerer frekvensen innanfor tenesta.",
    "1.4": "Topologien styrer all navigasjon; å designe eit system er å teikne grensene for desse regionane.",
    "1.41": "Dei busette regionane er dei mønstera brukarar eller agentar allereie har validert som levedyktige.",
    "1.411": "Eit etablert interaksjonsmønster (som eit sveip eller eit klikk) vert eit ankerpunkt for all framtidig systemutvikling.",
    "1.4111": "Standardiseringa av ein protokoll vert tyngre jo fleire uavhengige nodar som baserer drifta si på han.",
    "1.42": "Moglegheitsrommet i oppdateringar av programvare ligg utelukkande i desse tilstøytande regionane.",
    "1.421": "Latente funksjonar i eit system er opne, men krev ein utløysande agent for aktualisering.",
    "1.42111": "Arkitekturens tekniske gjeld og domenekrava dikterer rigorøst kva for greiner av kodebasen som kan utforskast vidare.",
    "1.42112": "Attraktoren er brukarverdien; den frastøytande krafta er kognitiv friksjon eller teknisk latens.",
    "1.43": "I informasjonssystem er dei forbodne regionane ofte definerte av minnekapasitet, tryggleikspolitiske reglar eller tidsavbrot.",
    "1.431": "Ein overgang til asynkron handtering gjer umiddelbart forbodne arkitekturar tilgjengelege og opne.",

    # Chap 2
    "2": "Sannsynet er vekta av den samla systemtilstanden; ingen tenestekonfigurasjon flyt fritt.",
    "2.1": "Eit trykk kan vere prosessorkostnad, brukaradopsjon, eller overføringsbandbreidde.",
    "2.11": "Gradienten tvingar fram eit mønster utan å diktere den eksakte kodelinja eller grensesnitt-pikselen.",
    "2.11111": "Form er restverdien etter at alle optimaliseringskrav har barbert vekk dei ikkje-levedyktige alternativa.",
    "2.11112": "Systemdesign er soleis ein reduktiv prosess av feilretting, ikkje ein additiv prosess av skaping.",
    "2.12": "Eit system i stabil drift er alltid fanga mellom kryssande trykk, som kravet til tryggleik versus kravet til yting.",
    "2.121": "Å tilskrive suksessen til eit tenestesystem utelukkande til brukarvenlegheit er ein logisk forenkling som overser teknisk og økonomisk trykk.",
    "2.13": "Spenninga mellom dataminimering og rik funksjonalitet peikar i eksakt motsette retningar av formrommet.",
    "2.1311": "Eit programvarekompromiss manifestet som ein mikroteknestearkitektur; ho tolererer bandbreiddetap for å vinne agens-isolasjon.",
    "2.13112": "Ulike operativsystem representerer ulike gyldige kompromiss for det same overordna settet av seleksjonstrykk.",
    "2.131131": "Uten å matematisk vekte yting mot lesbarheit er vurderinga av eit kode-paradigme uformell.",
    "2.141": "Den underliggande forretningslogikken gjev ingen informasjon om kvifor to klientar med ulikt grensesnitt løyser oppgåva ulikt.",
    "2.2": "Affordansen i eit grafisk grensesnitt er ikkje ein farge, men kva for rekke av hendingar fargen logisk opnar for å initiere.",
    "2.21": "Ein API-dokumentasjon er ei skildring av dette latente repertoaret av moglege tilstandar.",
    "2.21111": "Kapasiteten for distribuert konsensus låg i kryptografi og nettverksprotokollar i tiår før blokkjedene tok posisjonen.",
    "2.211122": "Systemarkitekturen vil alltid henge etter maskinvarens affordansar, av di operasjonane tek tid å formalisere til grammatikk.",
    "2.2211": "Termar som 'Web 2.0' eller 'skya' skildrar kvar vandringa stansa, men forklarar ingen av dei underliggande kausale drivkreftene.",

    # Chap 3
    "3": "Landskapet er summen av alle ytelseskrav og restriksjonar som verkar på systemet.",
    "3.1": "Ein lokal optimal løysing i eit tenestedesign samsvarar med ein haug i dette abstrakte landskapet.",
    "3.1111": "Kompilatoren si optimalisering eller marknadens seleksjon verkar som konkrete uttrykk for desse vektene.",
    "3.111121": "Retro-analyse av ein kodebase let oss utleie nøyaktig kva vekt utviklarane la på yting versus skalerbarheit i det gjevne tidspunktet.",
    "3.11113": "Systemet konvergerer alltid mot den mest stabile arkitekturen i nærleiken av sin noverande tilstand.",
    "3.1211": "Å flytte systemet ut av ein slik tilstand krev eit bevisst energipådrag mot gradienten, for å overkome den suboptimale dalen til neste haug.",
    "3.12112": "Jakta på den universelle, altløysande applikasjonen bryt mot landskapets fundamentale multimodalitet.",
    "3.2": "Kanalisering gjer systemet robust mot brukarfeil og dataavbrot: dalveggane dirigerer feilsteg tilbake til trygg tilstand.",
    "3.21111": "Protokollar med høg feil-intoleranse produserer grove, bratte kanalar i formrommet.",
    "3.31": "Grensene for kor ein tenestekategori byrjar og ein annan sluttar, kan aldri definerast binært i logikken; overgangen er ein glidande gradient i avstandsmål.",
    "3.411": "Når to isolerte utviklarteam konvergerer mot identiske designmønster (som MVC-arkitekturen), provar det at mønsteret er ein stabil haug i landskapet, ikkje ein konvensjon.",

    # Chap 4
    "4.1": "Teknologisk gjeld og endra kravspesifikasjonar syter for at trykka fluktuerer konstant.",
    "4.1111": "Ein arkitektur som er optimal for tusen brukarar vert suboptimal for ein million; tilpassinga er lokal i både rom og skala.",
    "4.11112": "Nye abstraksjonslag opnar forbodne regionar av kompleksitet som før krasja grunna minne-handtering.",
    "4.2": "Eit paradigmeskifte i programmering manifesterer seg nøyaktig slik: stase brote av brå topologiske restruktureringar.",
    "4.211": "Nye bibliotek utløyser eksplosiv radiasjon av løysingar, før dei best eigna mønstera vert standardiserte.",
    "4.3": "Den eksisterande databasestrukturen er eit minnespor som avgrensar kva for nye tenester som rasjonelt kan implementerast.",
    "4.3111": "Utviklaren byrjar aldri med blanke ark; rammeverket er allereie ladet med stiavhengige seleksjonstrykk.",
    "4.31112": "Valet av eit asynkront paradigme låser systemet inn i eit spor der visse synkrone mønster vert utilgjengelege utan massiv refaktorering.",
    "4.4": "API-økosystem ekspanderer monotont; deprecation fjerner grensesnitt, men konseptrommet bak dei veks framleis.",
    "4.41112": "Å openkjeldekode eit bibliotek er ikkje å tømme eit rom, men å tilgjengeleggjere eksponentielt fleire tilstøytande posisjonar for eksterne agentar.",
    "4.5": "Viss berre prosesseringsfart vektast og minnekostnad ignorerast, kollapsar systemets arkitektur mot ubrukbar rigiditet.",

    # Chap 5
    "5": "Ein agent kan vere alt frå ein ruter som handsamar trafikk, til ein brukar i eit grensesnitt.",
    "5.1": "Eit kvart sjølv-justerande nettverk stettar krava til systemisk agens i landskapet.",
    "5.11": "Avstandsmålinga i digitale system er ofte eksplisitt definert via feilratar og responstider.",
    "5.1111": "At agens er substratuavhengig, er aksiomet som gjer at vi kan overføre formalisme frå biologi direkte til tenestedesign.",
    "5.121": "Skilnaden mellom ein algoritme og eit operativsystem ligg ikkje i materie, men i spennvidda av deira kognitive lyskjegle og læringsdjupne.",
    "5.131": "Routing-algoritmen finn ikkje opp den kortaste vegen; han oppdagar gradienten i nettverksforskingas formrom.",
    "5.2": "For eit mikroteknestekomponent er lyskjegla strengt identisk med dei variablane som vert mottatt i HTTP-forespurnaden.",
    "5.21": "Alt utanfor dette datalaget er, for komponenten, kausalt eit svart hòl.",
    "5.221": "Grensesnittets oppløysing bestemmer kva operasjonar brukaren kan ta: grovare UI, redusert kompetanse og færre transformasjonar.",
    "5.22121": "Affordansane i ei plattform spring ut av dei formelle kryssingane mellom brukar-lyskjegla og system-lyskjegla.",
    "5.23": "Å gje ein teneste nye tilgangsrettar er, matematisk sett, ein utviding av agensens lyskjegle.",
    "5.3": "Formgrammatikken opererer her som ei rekkje reglar for API-anrop: identifiser del-tilstand, erstatt med oppdatert tilstand.",
    "5.3112": "Tenestelogikken si 'innleiring' krev berre at dei formelle parametrane er oppfylte for at operasjonen skal eksekverast; den historiske stien dit er sletta.",
    "5.321131": "Ein datasettkombinasjon kan avsløre mønster (delformer) som ingen av kjeldene bar i seg sjølve. Relasjonsdatabasens magi kviler på denne proposisjonen.",
    "5.4": "Maskinvaren og internettprotokollen fungerer som null-ordens agentar: dei tvingar all programvare til å unngå nettverksavbrot og minnelekkasjar.",
    "5.51111": "Nettverksruting, evolusjon og backpropagation-læring i nevrale nettverk er isomorfe; dei utfører den same algoritmiske avstandskrympinga i ulike substrat.",

    # Chap 6
    "6.1": "Eit komplekst distribuerte system si åtferd kan ikkje deduserast frå kjeldekoden til éin av nodane; forma spring ut av kompromiss i nettverket.",
    "6.11": "Brukaropplevinga emergerer presis der forretningslogikk, databaseskjema og nettverkslatens kryssar kvarandre som gradientar.",
    "6.111121": "Mikrokomponentar manglar representasjon av heilskapen. Dei leverer data over port 80, men bidreg uvitande til det makroskopiske formrommet vi kallar 'systemet'.",
    "6.121": "Eit strengt typa grensesnitt filtrerer reglane frå grammatikken slik at agenten (brukaren) ikkje feilar; landskapet disiplinerer naboskapet.",
    "6.121112": "Med uendeleg bandbreidde kan komponentar dele fulle representasjonar av sine eigne tilstandar, noko som aukar presisjonen proporsjonalt.",
    "6.12112": "Tenesteorientert arkitektur (SOA) demonstrerer at å frikople agentar reduserer koordineringsevna, men sikrar autonom lokal overleving.",
    "6.13": "Asynkronisering løyser bandbreiddeproblemet nettopp ved å innføre tidsforsinka modellar av avhengigheiter.",
    "6.211": "Når fleire skytjenester bindast saman av ein meldingsbuss, vert heilskapen brått sjølv ein meta-agent med sin eigen tilbakekoplingssløyfe.",
    "6.31111": "Å kopiere eit populært brukargrensesnitt frå ein annan bransje utan omsyn til dei bakenforliggjande trykka, produserer inkompetent form i den nye klassen.",
    "6.41": "Kvart vellukka programvare-API dannar ein plattform, og kvar plattform opnar eit massivt rom av nye, hittil uante moglege tenester.",
    "6.51": "Den statiske koden må refaktorerast fordi trykka – brukartal, tryggleikstruslar, maskinvare – rører seg under føtene på arkitekturen.",
    "6.5111": "Kompetansestrukturen i framtidsretta design kviler på å distribuere agentar slik at oppdateringar kan skje asynkront.",
    "6.611": "Det faktum at isomorfe formrom lèt seg etablere for stoldesign og for nettverksarkitektur bekreftar at teorien grip sjølve mekanismen bak strukturendring, uavhengig av ontologien til byggeklossane.",
    "6.61113": "I all software engineering og tenestedesign er rolla til arkitekten ikkje å diktere utsjånad, men å setje grensevilkåra slik at ei kompetent form sjølv kan emergere.",
    "6.711": "Også den vitskaplege metoden er her ein formalisme i eit epistemisk landskap; falsifiserbarheita tryggar at navigasjonen framleis er gyldig."
}

def inject_footnotes(tex_file):
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to find all propositions: \prop{id}{status}{text}
    pattern = r"\\prop\{([0-6A-Z][^\}]*)\}\{([^\}]*)\}\{(.+?)\}"
    
    def replacer(match):
        prop_id = match.group(1)
        status = match.group(2)
        text = match.group(3)
        
        # Check if we have a footnote to insert
        if prop_id in footnotes_mapping:
            note = footnotes_mapping[prop_id]
            # Ensure text doesn't already end with a footnote to avoid double footnotes
            if not text.rstrip().endswith("}") or r"\footnote" not in text:
                # Add the footnote before the final period if exists, else at the end
                if text.endswith("."):
                    text = text[:-1] + f"\\footnote{{{note}}}."
                else:
                    text = text + f"\\footnote{{{note}}}"
        return f"\\prop{{{prop_id}}}{{{status}}}{{{text}}}"

    new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Injected footnotes successfully. Updated file: {tex_file}")

if __name__ == "__main__":
    inject_footnotes('FORMLÆRE.tex')
