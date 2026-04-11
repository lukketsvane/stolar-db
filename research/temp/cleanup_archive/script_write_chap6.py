import os

content = r"""\silentchapter{6 Forma oppstår mellom agentane}{forma oppstår mellom agentane}
\prop{6}{}{Forma oppstår mellom agentane.\footnote{Arkitekturen er tilstanden som trer fram i krysninga av anrop, ikkje ein eigedom hos nodane.}}
\prop{6.1}{t}{Kvar realisert form utgjer eit poly-agentisk kompromiss.\footnote{Odling-Smee, Laland \& Feldman (2003)}\footnote{Åtferda lèt seg ikkje dedusere frå éin kjeldekode; morfologien spring ut av nettverkskonfliktar.}}
\prop{6.11}{t}{Materialet, reiskapen, marknaden og kulturen utgjer uavhengige gradientar.\footnote{Brukaropplevinga emergerer der inkommensurable gradientar kryssar kvarandre.}}
\prop{6.111}{t}{Ingen einskild agent dikterer morfologien.\footnote{Monolittisk styring sviktar der domenet krev polysentrisk tilpassing.}}
\prop{6.1111}{t}{Morfologien emergerer i skjeringspunktet deira.\footnote{Grensesnittet er eit forhandlingsrom mellom domene.}}
\prop{6.11111}{t}{Kvart nivå løyser problem kompetent innanfor si eiga lyskjegle.\footnote{Mikrotenesta agerer suverent og ser berre sin eigen kontrakt.}}
\prop{6.11112}{t}{Lågare komponentar navigerer etter lokale gradientar.\footnote{Ein asynkron tråd prioriterer sin eigen kø og er blind for heilskapen.}}
\prop{6.111121}{t}{Komponentane bidreg til mål dei manglar kapasitet til å representere.\footnote{Rutaren formidlar pakkar utan omgrep om mål-økta; topologien kviler på lokal vankunne.}}
\prop{6.11113}{t}{Reduksjonisme og holisme utgjer komplementære skildringsnivå.\footnote{Arkitektur krev uavhengig overvaking av lokal minnebruk og global gjennomstrøyming.}}
\prop{6.111131}{t}{Eit isolert nivå yter inga tilstrekkeleg skildring.\footnote{Lokal optimalisering utan omsyn til global topologi skapar fatale feil.}}
\prop{6.12}{t}{Landskapet dikterer kva reglar som fyrer, uavhengig av nominell kontroll.\footnote{Deklarative oppsett underkastar seg alltid materielle flaskehalsar.}}
\prop{6.121}{t}{Landskapet filtrerer naboskapen som agenten vel frå.\footnote{Datatypar disiplinerer kva kall som når fram.}}
\prop{6.1211}{t}{Kontrollen er alltid delt.\footnote{Tilstandsmaskina deler styringa med hendingsløkka som avbryt ho.}}
\prop{6.12111}{o}{Endeleg bandbreidde avgrensar all kommunikasjon mellom agentar.\footnote{CAP-teoremet formaliserer grensene for tryggleik i eit distribuert nettverk.}}
\prop{6.121111}{o}{Låg bandbreidde tvingar fram grov og stokastisk navigasjon.\footnote{Rørige nettverk krev heuristisk gjetting framfor deterministisk viten.}}
\prop{6.121112}{o}{Høg bandbreidde lèt forma artikulerast gjennom eksplisitt spesifikasjon.\footnote{Synkrone systembussar deler eksakte representasjonar av global tilstand.}}
\prop{6.12112}{t}{Bandbreidde stend i eit byttetilhøve til uavhengigheit.\footnote{Frikopla tenester oppnår høg oppetid ved å ofre global konsistens.}}
\prop{6.121121}{t}{Tett kopla agentar konvergerer mot felles format som avgrensar formrommet.\footnote{Ein monolittisk database tvingar fram einskap, men frys domenemodellen.}}
\prop{6.121122}{t}{Lauskopla agentar vernar autonomien på kostnad av koordinering.\footnote{Hendingadrivne modular oppdaterer asynkront, og let systemet gli ut av takt.}}
\prop{6.12113}{t}{Systemfasen dikterer det optimale koplingsregimet.\footnote{Inkubasjon krev formbare modular; stordrift krev statisk logikk.}}
\prop{6.121131}{t}{Behovet for utnytting framfor utforsking krev tettare koplingar.\footnote{Dynamiske språk lèt arkitekturen vandre fritt; statiske typar frys rammene for trygg drift.}}
\prop{6.13}{o}{Latens utgjer den temporale dimensjonen til bandbreidda.\footnote{Asynkronitet handterer fordeling ved å postulere tidsforsinka skuggar av sanninga.}}
\prop{6.131}{t}{Høg latens tvingar agenten til å operere på modellar av framande tilstandar.\footnote{Klienten utfører optimistiske oppdateringar for å binde over gapet til databasen.}}
\prop{6.1311}{t}{Koordineringspresisjonen speglar utelukkande modellens adekvatheit.\footnote{Cache-invalidering avgjer når den lokale representasjonen lyt slettast for å hindre konflikt.}}
\prop{6.13111}{t}{Latens avgrensar agentens epistemiske horisont.\footnote{Pakkeforseinking tvingar fram ein absolutt lyskjegle for lokal erfaring.}}
\prop{6.2}{o}{Robust kopling genererer eit overordna system.\footnote{Tett fletta applikasjonar trer fram som eit makroskopisk subjekt.}}
\prop{6.21}{t}{Dette systemet opererer med ei utvida lyskjegle og samansette mål.\footnote{Plattforma maksimerer volum og levetid, eit optimum mikromodulane ikkje kjenner.}}
\prop{6.211}{t}{Heilskapen vert sjølv ein agent når samanbindinga lukkar ei tilbakekoplingssløyfe.\footnote{Kuhn (1962)}\footnote{Eit kluster som autoskalerer etter ekstern last, agerer på eigne vegner.}}
\prop{6.2111}{o}{Multi-agent-system oppnår metastabilitet utan full optimalisering på lågare nivå.\footnote{Arkitekturen vernar robustheita si gjennom overflytande reaksjonar på distribuerte trådar.}}
\prop{6.21111}{o}{Metastabiliteten bergar tradisjonar gjennom fluktuasjonar som ville utsletta isolerte delar.\footnote{Distribuerte system held tilstanden intakt sjølv når nodar døyr.}}
\prop{6.3}{t}{Stilar og tradisjonar manglar kausal kraft.\footnote{"MVC-paradigme" er ein etterhandsdiagnostikk som ikkje genererer kode.}}
\prop{6.31}{t}{Dei markerer punkta der formvandringa mellombels stansar.\footnote{Arkitektoniske mønster er arr etter gjentekne møte med same strukturelle press.}}
\prop{6.311}{t}{Å formgje etter ein stil utgjer ein logisk feil.\footnote{Å tvinge objektorientert form inn i funksjonelle rammeverk skapar syntaktisk støy.}}
\prop{6.3111}{t}{Stilimitasjon etterliknar eit symptom utan å gripe seleksjonstrykket.\footnote{Skeumorfisme imiterer ein mekanisk brytar framfor å formgje verkeleg digital affordans.}}
\prop{6.31111}{t}{Stilimitasjon kopierer effekten og ignorerer årsaka.\footnote{Mikrotenester utan domenekrav mimer Netflix-løysingar på problem ein ikkje har.}}
\prop{6.311111}{t}{Resultatet vert eit hylster utan tilknyting til reelle trykk.\footnote{Tape-stasjon-logikk overlever i moderne nettskysystem.}}
\prop{6.4}{t}{Nyheitsraten i formrommet fylgjer det tilstøytande moglege.\footnote{Nye API-kall eksponerer momentant eit tre av uprøvde systemkombinasjonar.}}
\prop{6.41}{o}{Kvar realisert form opnar hittil ukjende regionar av naboskapen.\footnote{Kompilatoren skapar fundamentet der høgnivå-abstraksjonar breier ut sine formrom.}}
\prop{6.411}{t}{Det moglege veks med det realiserte.\footnote{Kauffman (1993)}\footnote{Nettverkseffekten ekspanderer morfologien; nye grensesnitt kvadrerer moglege pakkevandringar.}}
\prop{6.4111}{t}{Formhistoria tappar aldri eit gjeve repertoar.\footnote{Løysingar tvingast fram av nyoppdaga friksjonar, dei plukkast ikkje frå ein katalog.}}
\prop{6.41111}{t}{Rørsla ekspanderer sjølv repertoaret.\footnote{Systemdrifta framkallar ukjende feil som krev nye abstraksjonar.}}
\prop{6.5}{t}{Inga form er endeleg.\footnote{Utgjevingar markerer berre ein kort kvilepuls i ein uavbroten distribusjon.}}
\prop{6.51}{t}{Flyktige seleksjonstrykk gjer kvar realisert balanse suboptimal over tid.\footnote{Modulane lyt evig refaktorerast av di domenekrav kontinuerleg rører seg.}}
\prop{6.511}{t}{Forma speglar utelukkande vilkåra i sitt eige aktualiseringsaugeblikk.\footnote{Prosessar frosne i utdaterte minnemodellar sprekk i møte med parallelliserte kall.}}
\prop{6.5111}{t}{Høg agensstratifisering overgår rigiditet i jakta på robustheit.\footnote{Plugin-arkitekturen tolerer eksterne krasj av di kjernedomenet haldast lausrive frå periferien.}}
\prop{6.51111}{o}{Uavhengige tilpassingsmekanismar på tvers av skalaer aukar responshastigheita.\footnote{Elastisk allokering slettar instansar samstundes som databasen driv urørt vidare.}}
\prop{6.51112}{t}{Berre den generative strukturen varer.\footnote{Maskinvare forgår, men tilstandsprotokollar står uskada att.}}
\prop{6.511121}{t}{Formene utgjer flyktige spor i ein stabil grammatikk.\footnote{Rammeverk dekomponerer, men von Neumann-arkitekturen sine prinsipp held fast.}}
\prop{6.6}{o}{Rammeverket yter ingen ontologiske påstandar.\footnote{Strukturen er materielt tom og bind seg korkje til serverfarmar eller nevrale brikker.}}
\prop{6.61}{o}{Strukturen utgjer eit koordinatsystem for spesifikasjon.\footnote{Programmeraren opererer innanfor grensesnitta utan å teoretisere maskinvarens elektrisitet.}}
\prop{6.611}{o}{Substratuavhengigheita syner fruktbarheit, ikkje sanning.\footnote{Isomorfiane mellom programvare og evolusjonær morfologi syner at syntaksen fangar dynamikken formelt.}}
\prop{6.6111}{o}{Observatøren av formverda høyrer sjølv til i ho.\footnote{Kompilatoren som sjekkar syntaksen, verkar sjølv som eit binært objekt inni maskinvaren.}}
\prop{6.61111}{o}{Utsida manglar eit arkimedisk punkt.\footnote{Systemtilstanden materialiserer seg berre under køyretid; testmiljøet yter inga sanning.}}
\prop{6.61112}{o}{Formlæra manifesterer seg alltid lokalt og situert.\footnote{Konsensusprotokollar unngår platonsk matematikk og utfører situerte forsøk på å maskere korrupte noder.}}
\prop{6.61113}{o}{Å gje form er å diktere kva krefter som utgjer landskapet.\footnote{Arkitektens handlingsrom ligg utelukkande i å definere straffefunksjonane agentane skal minimere.}}
\prop{6.611131}{o}{Formgjevinga utvidar agentens lyskjegle mot latente affordansar.\footnote{Type-sjekking legg ikkje til logikk, men gjev køyremiljøet auge til å unngå inkonsistens.}}
\prop{6.611132}{o}{Formgjevinga lyt akseptere emergens mellom agentane.\footnote{Morfologien avslører seg der asynkrone oppkall kolliderer.}}
\prop{6.611133}{o}{Formgjevinga fastset vilkåra for kompetente delar.\footnote{Solid kode sensurerer ikkje feil, men riggar rammeverket for det trygge unntaksfallet.}}
\prop{6.7}{o}{Navigasjonen gjennom tilpassingslandskapet tek aldri slutt.\footnote{Koden definerer tilstanden, domena utgjer landskapet, og refaktoreringa kviler aldri.}}
\prop{6.71}{o}{Denne traktaten utgjer ein eigen posisjon i formrommet.\footnote{Kapittelinndelinga utfaldar seg i eit strengt rekursivt domenetre for eit gjeve hierarki.}}
\prop{6.711}{o}{Falsifiserbarheita garanterer tekstens gyldigheit.\footnote{Formelle system stadfestar seg sjølve berre i den grad dårlege input faktisk krasjar dei.}}
"""

with open(r"C:\Users\Shadow\Documents\GitHub\stolar-db\chap6_sharp.tex", "w", encoding="utf-8") as f:
    f.write(content)
