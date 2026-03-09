# Kva er Autoresearch, og korleis fungerer det?

Denne fila forklarar systemet me har bygd for å autonomt forbetre maskinlæringsmodellane dine. Målet er å skaffe det sterkaste moglege empiriske beviset for at "Form Follows Fitness" (FFF) stemmer, og at funksjonalismen ("form follows function") er feil.

## Konseptet i korte trekk
Kort sagt: Du har no ein AI-assistent (Gemini) som sit og jobbar for deg heile døgnet. Han endrar litt og litt på maskinlæringskoden din, køyrer han, ser om resultatet vart betre, og lærer av feila sine.

I staden for at *du* manuelt må skrive kode for å prøve ut hundrevis av ulike algoritmar (som RandomForest, XGBoost, Support Vector Machines), eller prøve å justere små parameter for å få modellen til å treffe betre, gjer dette skriptet alt heilt av seg sjølv.

## Korleis det heng saman med doktorgrada di
For å knuse Le Corbusier og Sullivan sitt dogme, må me bevise at forma (geometrien) til ein gjenstand nesten fullt ut kan predikerast av **materialet**, **opphavsstaden** og **epoken** han vart laga i. 

Viss me fôrar ein maskinlæringsmodell med geometriske og materielle data for ein stol, og modellen klarer å gjette presist kva *land* og *stilperiode* stolen kjem frå (målt i F1-score), betyr det at funksjonen ("å sitje på") *ikkje* er det som dikterer forma. Hadde funksjon vore det einaste viktige, ville alle stolar vore heilt like, og modellen ville gjetta feil kvar gong.

Desto høgare score (treffsikkerheit) me klarer å få (det me kallar `FINAL_SCORE`), desto sterkare er beviset ditt. Autoresearch-scriptet har som si einaste oppgåve å maksimere denne scoren matematisk.

## Steg-for-steg: Slik fungerer loopen (`agent.py`)

Sjølve hjernen i systemet ligg i mappa `chair_autoresearch`. For å ikkje øydeleggje dei originale artiklane dine, lagar me ein leikeplass (sandkasse) for koden her. Når du startar fila `agent.py`, gjer den fylgjande i ein evig loop:

1. **Les koden:** Agenten les fila `train_eval.py` (som er koden for maskinlæringsmodellen din).
2. **Tenkjer og skriv:** Han sender denne koden til Gemini 2.5 Pro med ein tydeleg instruksjon: *"Du er ein ekspert på AI som prøver å bevise Form Follows Fitness. Endre denne koden for å få ein endå høgare FINAL_SCORE. Prøv nye algoritmar eller matematiske metodar."*
3. **Køyrer eksperimentet:** Agenten slettar den gamle koden, lagrar den nye koden som Gemini fann på, og køyrer fila for å sjå kva score han får i røynda.
4. **Evaluerer:**
   - Viss den nye koden kræsjar, eller scoren er **lågare** enn før, slettar han endringane og går tilbake til førre versjon (merkar det som "discard" i loggen).
   - Viss scoren er **høgare**, lagrar han denne nye koden som den nye standarden! Han lagrar òg ein sikkerheitskopi av den gode koden (f.eks. `train_eval_best_5.py`) og merkar det som "keep".
5. **Gjentek:** Han byrjar på nytt att frå steg 1 med den forbetra koden. Dette gjer han heilt til du stoppar han.

## Utviding til andre objekt (Generalisering)
For at FFF-teorien skal vere eit fullstendig paradigmeskifte, må det gjelde for meir enn berre stolar. Teorien må kunne generaliserast. Derfor har me laga mappa `data_gathering_pipeline/`.

- Her ligg eit skript som heiter `fetch_digitaltmuseum.py`.
- Dette skriptet koplar seg til API-et til DigitaltMuseum (KulturNav) for å hente ut titusenvis av andre objekt (t.d. keramikk, bord, lampar).
- Skriptet byggjer opp automatiserte databasar med materielle eigenskapar og geometri for desse nye objekta.
- Når du har henta ut data for f.eks. "keramikk", kan du enkelt be autoresearch-agenten om å trene modellane på *keramikk* i staden for stolar. Viss agenten greier å maksimere scoren og bevise at material/geografi styrer forma for keramikk òg, har du bevist at teorien din gjeld for *all* industridesign!

## Slik startar du evigheitsmaskina
For å la maskina jobbe medan du gjer andre ting (eller søv), opnar du PowerShell og skriv desse tre linjene:

```powershell
# 1. Gå inn i sandkassa
cd C:\Users\Shadow\Documents\GitHub\stolar-db\chair_autoresearch

# 2. Legg inn API-nøkkelen din for denne sesjonen
$env:GEMINI_API_KEY="<din-api-nokkel-her>"

# 3. Start agenten
python agent.py
```

Du kan når som helst avbryte han med `Ctrl + C`. Du vil finne alle resultata, iterasjon for iterasjon, i fila `results.tsv` inne i `chair_autoresearch`-mappa. Dei beste kodeversjonane vil bli lagra som eigne filer der inne.