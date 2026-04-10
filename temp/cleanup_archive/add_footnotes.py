# -*- coding: utf-8 -*-
import sys

with open('FORMLÆRE.tex', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    r"\prop{1.1}{d}{Morforommet er den logiske mengda av alle moglege konfigurasjonar for ein gjeven funksjon.}": 
        r"\prop{1.1}{d}{Morforommet er den logiske mengda av alle moglege konfigurasjonar for ein gjeven funksjon.\footnote{Raup (1966); Mitteroecker \& Huttegger (2009)}}",
        
    r"\prop{1.22}{d}{Den tilstøytande regionen er mengda av posisjonar som kan nåast med éin logisk operasjon frå den aktualiserte.}": 
        r"\prop{1.22}{d}{Den tilstøytande regionen er mengda av posisjonar som kan nåast med éin logisk operasjon frå den aktualiserte.\footnote{Kauffman (1993)}}",
        
    r"\prop{1.3}{o}{Kvar empirisk måling av fysisk form er ein dimensjonsreduserande projeksjon. Valet av aksar avgjer kva topologiske grenser analysen registrerer.}": 
        r"\prop{1.3}{o}{Kvar empirisk måling av fysisk form er ein dimensjonsreduserande projeksjon. Valet av aksar avgjer kva topologiske grenser analysen registrerer.\footnote{Thompson (1917)}}",
        
    r"\prop{2.1}{o}{Fordelinga av aktualiserte posisjonar i morforommet er ikkje termodynamisk uniform. Formene samlar seg i tette klynger med massive tomrom i mellom.}": 
        r"\prop{2.1}{o}{Fordelinga av aktualiserte posisjonar i morforommet er ikkje termodynamisk uniform. Formene samlar seg i tette klynger med massive tomrom i mellom.\footnote{Raup (1966)}}",
        
    r"\prop{2.21}{t}{Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess. Sannsynlegheita for ei ny form er radikalt betinga av historia.}": 
        r"\prop{2.21}{t}{Sannsynlegheitsfordelinga for formgenerering er isomorf med ein ergodisk Markoff-prosess. Sannsynlegheita for ei ny form er radikalt betinga av historia.\footnote{Shannon (1948)}}",
        
    r"\prop{2.41}{t}{Ergo er kvar realisert form logisk definert som eit kompromiss.}": 
        r"\prop{2.41}{t}{Ergo er kvar realisert form logisk definert som eit kompromiss.\footnote{Michl (1995)}}",
        
    r"\prop{2.5}{d}{Materialaffordanse er funksjonen som determinerer grensene for den forbodne regionen. Materialet legg eigne sannsynsfordelingar over rommet.}": 
        r"\prop{2.5}{d}{Materialaffordanse er funksjonen som determinerer grensene for den forbodne regionen. Materialet legg eigne sannsynsfordelingar over rommet.\footnote{Gibson (1979)}}",
        
    r"\prop{3.1}{d}{Tilpassingslandskapet er den aggregerte verdien av alle verksame seleksjonstrykk over morforommet.}": 
        r"\prop{3.1}{d}{Tilpassingslandskapet er den aggregerte verdien av alle verksame seleksjonstrykk over morforommet.\footnote{Wright (1932)}}",
        
    r"\prop{3.3}{d}{Gradienten kring eit lokalt maksimum definerer graden av kanalisering. Høg negativ gradient determinerer formsekvensen med høg robustheit.}": 
        r"\prop{3.3}{d}{Gradienten kring eit lokalt maksimum definerer graden av kanalisering. Høg negativ gradient determinerer formsekvensen med høg robustheit.\footnote{Waddington (1957)}}",
        
    r"\prop{3.4}{d}{Ein stil er den deskriptive nemninga på ei klynge av aktualiserte former kring same attraktor i landskapet.}": 
        r"\prop{3.4}{d}{Ein stil er den deskriptive nemninga på ei klynge av aktualiserte former kring same attraktor i landskapet.\footnote{Kubler (1962)}}",
        
    r"\prop{4.21}{t}{Av 4.2 følgjer at form følgjer form. Den eksisterande forma endrar infrastrukturen, verktøya og forventningane for den neste.}": 
        r"\prop{4.21}{t}{Av 4.2 følgjer at form følgjer form. Den eksisterande forma endrar infrastrukturen, verktøya og forventningane for den neste.\footnote{Arthur (1994)}}",
        
    r"\prop{4.4}{o}{Morfologisk endringsrate manifesterer ei trappefunksjon (avbrote likevekt): lange periodar med stase avbrote av episodisk radiasjon.}": 
        r"\prop{4.4}{o}{Morfologisk endringsrate manifesterer ei trappefunksjon (avbrote likevekt): lange periodar med stase avbrote av episodisk radiasjon.\footnote{Eldredge \& Gould (1972)}}",
        
    r"\prop{5.11}{d}{Ein agent er ein operator definert uttømande ved ei cybernetisk sløyfe: måling av avvik frå eit mål, og applikasjon av ei korrigerande transformasjon.}": 
        r"\prop{5.11}{d}{Ein agent er ein operator definert uttømande ved ei cybernetisk sløyfe: måling av avvik frå eit mål, og applikasjon av ei korrigerande transformasjon.\footnote{Rosenblueth, Wiener \& Bigelow (1943)}}",
        
    r"\prop{5.12}{t}{Agens er substrat-uavhengig. Definisjonen krev korkje eit biologisk nervesystem, menneskeleg medvit eller intensjon.}": 
        r"\prop{5.12}{t}{Agens er substrat-uavhengig. Definisjonen krev korkje eit biologisk nervesystem, menneskeleg medvit eller intensjon.\footnote{Wiener (1948); Turing (1950)}}",
        
    r"\prop{5.2}{d}{Den kognitive lyskjegla er den delmengda av morforommet agenten har algoritmisk oppløysing til å representere og transformere.}": 
        r"\prop{5.2}{d}{Den kognitive lyskjegla er den delmengda av morforommet agenten har algoritmisk oppløysing til å representere og transformere.\footnote{Fields \& Levin (2022)}}",
        
    r"\prop{5.4}{t}{C-K-teorien er det proposisjonslogiske spesialtilfellet av navigasjon i lyskjegla. Design er den felles ekspansjonen av eit Kunnskapsrom (K) og eit Konseptrom (C).}": 
        r"\prop{5.4}{t}{C-K-teorien er det proposisjonslogiske spesialtilfellet av navigasjon i lyskjegla. Design er den felles ekspansjonen av eit Kunnskapsrom (K) og eit Konseptrom (C).\footnote{Hatchuel \& Weil (2003, 2009)}}",
        
    r"\prop{5.6}{d}{Agenten transformerer forma utelukkande via matematisk innleiring (embedding) i notida.}": 
        r"\prop{5.6}{d}{Agenten transformerer forma utelukkande via matematisk innleiring (embedding) i notida.\footnote{Stiny \& Gips (1972)}}",
        
    r"\prop{5.62}{i}{Reglane for innleiring og geometrisk transformasjon utførast via formgrammatikk:}": 
        r"\prop{5.62}{i}{Reglane for innleiring og geometrisk transformasjon utførast via formgrammatikk:\footnote{Stiny (1980, 1991, 2006)}}",
        
    r"\prop{5.7}{t}{Av 5.12 og 5.6 følgjer same underliggjande algebra: Ein planaria navigerer morforommet via bioelektriske gradientar. Ein handverkar navigerer morforommet via taktil tilbakemelding. Ein diffusjonsmodell navigerer eit latent rom via denoising. Substrata er ulike; den kybernetiske strukturen er identisk.}": 
        r"\prop{5.7}{t}{Av 5.12 og 5.6 følgjer same underliggjande algebra: Ein planaria navigerer morforommet via bioelektriske gradientar. Ein handverkar navigerer morforommet via taktil tilbakemelding. Ein diffusjonsmodell navigerer eit latent rom via denoising. Substrata er ulike; den kybernetiske strukturen er identisk.\footnote{Levin (2022, 2025)}}",
        
    r"\prop{6.2}{d}{Nisjekonstruksjon: Kvar transformasjon utført av éin agent, endrar landskapet for alle andre agentar i nettverket.}": 
        r"\prop{6.2}{d}{Nisjekonstruksjon: Kvar transformasjon utført av éin agent, endrar landskapet for alle andre agentar i nettverket.\footnote{Odling-Smee, Laland \& Feldman (2003)}}",
        
    r"\prop{6.3}{t}{Kvar generasjon av formgjevarar etterlet eit modifisert tilpassingslandskap; eit fryst lag av fastlåste maskinar, standardar og verktøy. Dette utgjer den økologiske arven.}": 
        r"\prop{6.3}{t}{Kvar generasjon av formgjevarar etterlet eit modifisert tilpassingslandskap; eit fryst lag av fastlåste maskinar, standardar og verktøy. Dette utgjer den økologiske arven.\footnote{Odling-Smee, Laland \& Feldman (2003)}}",
        
    r"\prop{6.41}{d}{Eit slikt tett kopla system fungerer som ein makro-agent. Tradisjon er ein makro-agent i stase; problemløysing utførast kollektivt strengt innanfor grensa av eit etablert Kunnskapsrom (K).}": 
        r"\prop{6.41}{d}{Eit slikt tett kopla system fungerer som ein makro-agent. Tradisjon er ein makro-agent i stase; problemløysing utførast kollektivt strengt innanfor grensa av eit etablert Kunnskapsrom (K).\footnote{Kuhn (1962)}}",
        
    r"\prop{6.5}{t}{Paradigmeskifte utløysast viss og berre viss akkumulerte anomaliar i landskapet tvingar makro-agenten til systemisk restrukturering, der K-rommet kollapsar og C-rommet må omkodast.}": 
        r"\prop{6.5}{t}{Paradigmeskifte utløysast viss og berre viss akkumulerte anomaliar i landskapet tvingar makro-agenten til systemisk restrukturering, der K-rommet kollapsar og C-rommet må omkodast.\footnote{Kuhn (1962)}}"
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('FORMLÆRE.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("Footnotes successfully inserted!")