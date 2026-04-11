// Build: eg-inneheld-mengder.docx — expanded, playful, speculative, one heading only
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, HeadingLevel, ExternalHyperlink, BorderStyle } = require('docx');

const FIG = 'C:/Users/Shadow/Documents/GitHub/stolar-db/analysis/figures';
const TEK = 'C:/Users/Shadow/Documents/GitHub/stolar-db/teikningar';
const TMP = 'C:/Users/Shadow/Documents/GitHub/stolar-db/temp';
const OUT = 'C:/Users/Shadow/Documents/GitHub/stolar-db/eg-inneheld-mengder.docx';

// --- helpers -----------------------------------------------------------
const P = (text, opts = {}) => new Paragraph({
  spacing: { before: 0, after: 200, line: 340 },
  alignment: opts.align || AlignmentType.LEFT,
  indent: opts.firstLine === false ? undefined : { firstLine: 360 },
  children: Array.isArray(text)
    ? text
    : [new TextRun({ text, italics: !!opts.italic, bold: !!opts.bold, size: opts.size || 22 })],
});

const T = (text, opts = {}) => new TextRun({
  text,
  italics: !!opts.italic, bold: !!opts.bold, size: opts.size || 22,
});

// inline hyperlink: link wraps the words `text` and looks like coloured underlined text
const HL = (text, url, opts = {}) => new ExternalHyperlink({
  link: url,
  children: [new TextRun({
    text,
    italics: !!opts.italic, bold: !!opts.bold,
    size: opts.size || 22,
    color: '1F4E79', underline: { type: 'single', color: '1F4E79' },
  })],
});

const DIV = () => new Paragraph({
  spacing: { before: 200, after: 200 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: '· · ·', size: 22 })],
});

const QUOTE = (text) => new Paragraph({
  spacing: { before: 120, after: 160, line: 300 },
  indent: { left: 720, right: 720 },
  alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text, italics: true, size: 22 })],
});

const fig = (file, wInches, captionText) => {
  const data = fs.readFileSync(path.join(FIG, file));
  // compute height from real aspect
  const { execSync } = require('child_process');
  // use naive: we set height after reading via sharp-less fallback → we know dims from earlier
  return [data, wInches, captionText];
};

// Aspects from dims: lysk 1817x1280, agent 1817x1344, fitness 698x684, mat 1144x1273, atlas 1653x2645, cover 4096x3363
// Use sharp-less: dimensions hardcoded
const ratios = {
  'cover-stolar.png':  3363/4096,
  'stolar_squares.png': 2029/2400,
  'doctor_g001.jpg':   342/721,
  'doctor_g002.jpg':   801/766,
  'doctor_g003.jpg':   724/722,
  'doctor_g004.jpg':   256/797,
  'doctor_g005.jpg':   233/723,
};

const IMG = (file, wIn, caption) => {
  const isTmp = file.startsWith('doctor_') || file === 'stolar_squares.png';
  const dir = isTmp ? TMP : FIG;
  const data = fs.readFileSync(path.join(dir, file));
  const ext = file.split('.').pop().toLowerCase();
  const type = ext === 'jpeg' ? 'jpg' : ext;
  const w = Math.round(wIn * 96);
  const h = Math.round(w * ratios[file]);
  return [
    new Paragraph({
      spacing: { before: 260, after: 80 },
      alignment: AlignmentType.CENTER,
      children: [new ImageRun({
        type, data,
        transformation: { width: w, height: h },
        altText: { title: file, description: caption, name: file },
      })],
    }),
    new Paragraph({
      spacing: { before: 0, after: 260 },
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: caption, italics: true, size: 20 })],
    }),
  ];
};

// --- content -----------------------------------------------------------
const kids = [];

// TITLE BLOCK
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 600, after: 80 },
  children: [new TextRun({ text: 'EIN LITEN, SPEKULATIV SAMTALE I MARGEN AV FORMLÆRE', size: 18, color: '7A7A7A' })],
}));
kids.push(new Paragraph({
  heading: HeadingLevel.HEADING_1,
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 120 },
  children: [new TextRun({ text: 'Eg inneheld mengder', italics: true, size: 56 })],
}));
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 480 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '1F4E79', space: 12 } },
  children: [new TextRun({ text: 'om fleirskala kompetansar, omsorg, og kvifor designaren aldri har vore åleine', italics: true, size: 22, color: '4A4A4A' })],
}));
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 200, after: 480 },
  children: [
    new TextRun({ text: 'Iver Raknes Finne', size: 20 }),
    new TextRun({ text: '   ·   AHO   ·   April 2026', size: 20, color: '7A7A7A' }),
  ],
}));

// Cover image replaces the old one
kids.push(...IMG('stolar_squares.png', 6.2, '2 048 europeiske stolar, kvar redusert til ein liten rektangel som måler seteareal og proporsjon. Ingen einskild rute er den «rette»; alle saman er ei teikning av eit landskap som har halde gjennom syv hundre år.'));

kids.push(P([T('«'), HL('Form follows function', 'https://en.wikipedia.org/wiki/Form_follows_function'), T('» er ein éin-bits teori. Eit objekt er funksjonelt (1) eller ikkje (0). Det er ein doktrine på storleik med eit lysebryt. Når du måler henne mot dei 2 048 europeiske stolane som finst i traktaten — funksjon mot geometri, gjensidig informasjon — får du NMI = 0.000. Ikkje «omtrent null». Til tre desimalar. Funksjonen forklarer ingenting. Det er ikkje ei feilaktig teori; det er ei tom teori. Ho har vore katekismen i 130 år, og det einaste vitskapelege ho har vore, er '), T('falsifisert', { italic: true }), T('.')], { firstLine: false }));

kids.push(P([T('Og den teorien er framleis den minst skadelege av dei modernistiske doktrinene. Den meir skadelege er '), HL('Modulor', 'https://en.wikipedia.org/wiki/Modulor'), T(' — Le Corbusier sin proporsjonsskala bygd på ein hypotetisk «idealmann», ein europeisk høgmann, fyrst sett til 1,75 m og seinare, etter at Le Corbusier hadde lese britiske detektivromanar, oppjustert til 1,83 m fordi det «sjølvsagt» var «den engelske politimannen» som var den rette referansen. Han kalla det universalt. Han laga heile bygningar etter måla til denne ein-rasen-eitt-kjønn-eitt-kontinent fantasimannen og selde dei som «menneskeleg skala». Kvinner, born, kortvaksne, langvaksne, og dei to tredjedelane av menneskeslekta som ikkje matchar denne proporsjonen, blei ikkje rekna som '), T('feilaktig kalibrerte', { italic: true }), T(' — dei blei rekna som '), T('feilaktige kroppar', { italic: true }), T('. Det er den same logiske operasjonen som gjekk føre seg i samtidig eugenikk, og Le Corbusier sine sympatiar med Vichy gjorde det ikkje meir tilfeldig. Modulor er ikkje «av si tid»; han er ein doktrine om at geometri kan diktere kven som er menneske og kven som er '), T('avvik', { italic: true }), T(' frå mennesket. Form følgjer funksjon er informasjonsteoretisk tom. Form følgjer den ariske mannen er informasjonsteoretisk tom og moralsk farleg. Begge må gå.')], { firstLine: false }));

kids.push(DIV());

kids.push(P([T('Greitt. No som me har rydda bordet kan me snakke om det som faktisk forklarer korleis form oppstår. Dette er ikkje traktaten. Traktaten er tung, tett, fotnotetung, og krev at du sit stille og lèt setningane bite seg fast. Dette er det motsette: ein tur ut av traktaten og ned i ein kafé, der eg lovar å ikkje nummerere ein einaste proposisjon, der dei einaste reglane er at me får lov til å vere litt flåsete, litt spekulative, og at me skal lèt Bob Dylan snakke litt. Det er meint for deg som designar — for deg som har ein prototype under armen og ein tidsfrist i nakken, ikkje for doktorgradskomiteen.')]));

kids.push(P([T('Her er påstanden, i éin setning, før eg får lov til å gå rundt han i tjue: '), T('ein stol inneheld mengder, og det er ikkje ein metafor — det er mekanikk, og det gjev deg noko praktisk å gjere i morgon.', { bold: true })]));

kids.push(DIV());

kids.push(P([T('Bob Dylan har skrive to songar eg kjem til å lene meg tungt på. Den fyrste er frå 1979, frå '), T('Slow Train Coming', { italic: true }), T(', og heiter '), HL('«Man Gave Names to All the Animals»', 'https://www.bobdylan.com/songs/man-gave-names-to-all-the-animals/'), T('. Det er ein barnesong i utgangspunktet, enkle rim, enkel logikk: han såg ei ku og kalla ho ku, han såg eit svin og kalla det svin, han såg ein bjørn og — songen sluttar før han får sagt ordet, og du må sjølv tenkje tanken til slutt. Det er den beste detaljen i heile Dylans katalog: den uttalte taushetsen der namnet skulle ha vore. For namnet er ikkje berre ein etikett. Namnet er ein dør som slår igjen. I det du seier «dette er ein bjørn», har du allereie bestemt deg for at du ikkje skal bli eten, og du har ikkje tid til fleire kategoriar.')]));

kids.push(P([T('Å namngje er å sortere verda i kassar. Éin kasse per ting. Det er rasande nyttig — prøv å handle daglegvarer utan kategoriar, prøv å designe ei dør utan å vite kva ein «dør» er — og samstundes er det ei felle. For i same augeblink som du seier «dette er ein stol», har du bestemt deg for kva du '), T('ikkje', { italic: true }), T(' skal sjå. Du ser ikkje at stolen er eit våpenkvileavtale mellom fem krefter som dreg i ulike retningar. Du ser ikkje at treet i setet er ein agent som aktivt deltok i forminga — at fiberretninga i boka til ryggen bestemte kor tjukk ryggen kunne vere lenge før snikkaren kom inn. Du ser ikkje at stolen inneheld eit heilt økosystem av avgjerder tekne av folk som aldri møtte kvarandre og som for lengst er døde.')]));

kids.push(P([T('Den andre Dylan-songen er frå 2020, frå '), T('Rough and Rowdy Ways', { italic: true }), T(', og heiter '), HL('«I Contain Multitudes»', 'https://www.bobdylan.com/songs/i-contain-multitudes/'), T('. Han har stole tittelen frå '), HL('Walt Whitman', 'https://whitmanarchive.org/published/LG/1891/poems/27'), T(', som skreiv, i 1855, i '), T('Leaves of Grass', { italic: true }), T(': '), T('«Do I contradict myself? Very well then I contradict myself. I am large, I contain multitudes.»', { italic: true }), T(' Dylan syng det som ei kompetanseerklæring: å romme motsetningar er ein styrke, ikkje ein svakheit. Å vere sjølvmotseiande er å vere stor nok til å halde to ting i handa samstundes utan å knuse nokon av dei.')]));

kids.push(P([T('Eg trur dette ikkje berre gjeld diktarar. Eg trur det gjeld kvar einaste gjenstand som finst. Ein stol inneheld mengder. Eit hus inneheld mengder. Eit brød inneheld mengder — kornet, klimaet, mølla, surdeigen, bakaren si hand, ovnen, klokka, kulturen som avgjorde at akkurat denne skorpa er rett og den andre er feil. Kvar form er eit møtepunkt mellom agentar som aldri visste om kvarandre — og som likevel produserte noko saman. Oppgåva i det som følgjer er å vise at det er mogleg, at det er målbart, og at det forandrar kva du bør gjere når du set deg ned for å teikne i morgon tidleg.')]));

kids.push(DIV());

kids.push(P([T('Lat oss byrje så langt nede som det går. Lat oss byrje med ei celle. Ei einskild hudcelle på handbaken din — ho har tre ting: eit mål (hald deg i live, del deg til rett tid, dø til rett tid), ein sensor (kjemiske signal frå nabocellene), og ein justeringsmekanisme (ho endrar kva gen ho les frå). Det er alt. Ho er, i traktatens språk, ein agent: eit trippel av måltilstand, avstandsmåling og justering. Ho treng ikkje medvit. Ho treng ikkje intensjon. Ho treng ikkje ein gong eit nervesystem. Ho treng berre funksjonell organisering, og ho har det. Ho er så enkel som noko kan vere og samstundes kallast levande.')]));

kids.push(P([T('Men cella er ikkje åleine. Ho er kopla til nabocellene via noko som heiter gap junctions — små elektriske bruer som lèt ion og metabolittar flyte mellom dei. '), HL('Michael Levin', 'https://as.tufts.edu/biology/people/michael-levin'), T(', biologen ved Tufts University som har drive eit titals år med forsøk på akkurat dette, har vist at når cellene koplar seg saman slik, skjer det noko underleg: informasjonsbarrierane mellom dei vert viska ut. Eit smertesignal som oppstår i éin celle vandrar gjennom vevet utan metadata om kven som sende det. Eit heilt vev tek eigarskap til signalet. Stress blir delt. Og i det augeblinket stress blir delt, skjer ein fase-overgang: det emergerer eit nytt «sjølv». Ikkje ei celle, men eit organ. Ikkje summen av cellene, men noko strengt større — noko som har eigne mål, eigne sensorar, eigne justeringar, alt saman på ein annan tidsskala og i ei anna geometrisk oppløysning enn kvar einskild celle under seg.')]));

kids.push(P([T('Levin har eit ord for dette, og det er det viktigaste ordet i heile denne essayen: '), T('kognitiv lyskjegle', { italic: true, bold: true }), T('. Metaforen er lånt frå Einstein. I relativitetsteorien er lyskjegla til ein hending alt som kan påverke henne (fortida si kjegle) og alt ho kan påverke (framtida si kjegle). Det er omfanget av kausal kontakt. Levin sin versjon er mental: lyskjegla til ein agent er omfanget av kva han kan bry seg om — kva skalaer, kva tidshorisontar, kva dimensjonar i rommet av moglege tilstander han faktisk registrerer og responderer på. Ei celle har ei mikroskopisk lyskjegle: ho bryr seg om glukose, ho bryr seg om pH, ho bryr seg om sine næraste sju naboar. Eit organ har ei større lyskjegle: det bryr seg om tredimensjonal geometri, om posisjonen sin i kroppen, om å ikkje bli til noko anna enn seg sjølv. Organismen har ei endå større: ho bryr seg om overleving i eit skiftande miljø, om partnar, om avkom, om framtid. Og kvart nivå '), T('inneheld', { italic: true }), T(' det under seg — cella forsvinn ikkje når organet emergerer, ho blir del av ein større lyskjegle utan å miste sin eigen.')]));

kids.push(...IMG('doctor_g003.jpg', 5.2, 'Lyskjegla, henta direkte frå Doctor mfl. (2022, fig. 3). Den blå romben er den personlege lyskjegla (CLC) — alt eit individ kan registrere og handle på. Den gule er den fysiske lyskjegla (PLC) — alt som overhovudet kan påverke individet kausalt. Den gule kurva er ei livsline som vandrar gjennom rommet av moglege tilstandar. Personleg lyskjegle er, hjå Levin, ei underrunna teikning av kva ein agent faktisk bryr seg om.'));

kids.push(P([T('Dette er, så langt eg kan sjå, den einaste modellen av intelligens som maktar å sameine biologi, fysikk og design utan å måtte lyge om nokon av delene. Og det fører oss rett til '), HL('rapporten', 'https://www.mdpi.com/1099-4300/24/5/710'), T('. I 2022 publiserte Thomas Doctor, Olaf Witkowski, Elizaveta Solomonova, Bill Duane og Michael Levin ein artikkel i tidsskriftet '), T('Entropy', { italic: true }), T(' med den ualminneleg vakre og litt overmodige tittelen '), HL('«Care as the Driver of Intelligence»', 'https://www.mdpi.com/1099-4300/24/5/710'), T('. Eg las han fyrst med eit skeptisk smil og blei meir og meir overtydd for kvar side. Hovudpåstanden er enkel og veldig djup: '), T('intelligens er ikkje evna til å løyse problem. Intelligens er omfanget av det du bryr deg om.', { bold: true }), T(' Ei celle som bryr seg om éin gradient er intelligent i éin dimensjon. Eit organ som bryr seg om anatomisk form er intelligent i tre. Ein planarie-orm som kan regenerere heile kroppen frå eit fragment er intelligent i heile morfologirommet. Ein designar som bryr seg om materiale, økonomi, kultur, ergonomi og teknologi samstundes er intelligent i fem aksar.')]));

kids.push(P([T('Omsorg og intelligens er, i denne modellen, ikkje to ulike ting. Dei er same tingen sett frå ulike vinklar. Omsorg er intelligensens innhald; intelligens er omsorga si form. Ei intelligens utan omsorg er ikkje ei intelligens — ho er ein kalkulator. Ein kalkulator kan multiplisere to tusensifra tal raskare enn nokon av oss, men han har ikkje noko han vil med svaret, han har ikkje ein einaste dimensjon han bryr seg om, og difor er han, trass rekneevna si, like stupid som ein stein. Sjakkmaskinen Deep Blue var intelligent berre innanfor 64 ruter; utanfor det brettet hadde han lyskjegla til ein sparkelkniv. GPT-4 er intelligent berre innanfor tekstrommet; sleng han inn eit laboratorium med pipetter og han veit ikkje eingong kva han skal sjå på. Og eit menneske — du og eg — er intelligent berre i dei dimensjonane me faktisk har lært å sjå.')]));

kids.push(P([T('Her begynner det å bli interessant for oss som driv med form. For dersom intelligens er omfanget av omsorg, og dersom designaren er den agenten i systemet som typisk har det største omfanget, då er designaren si fremste oppgåve ikkje å teikne fine ting. Designaren si fremste oppgåve er å '), T('utvide lyskjegla si', { bold: true }), T('. Kvar ny dimensjon ho legg til — kvart nytt materiale ho lærer å sjå, kvar ny kultur ho lærer å lese, kvart nytt økosystem ho tek omsyn til — er ein ny akse av omsorg, og dermed ein ny akse av intelligens. Og kvar ny akse gjer kompromissa hennar betre, ikkje fordi ho blir flinkare til å rekne, men fordi ho faktisk '), T('bryr seg om', { italic: true }), T(' fleire av dei kreftene som alltid har vore der.')]));

kids.push(DIV());

kids.push(P([T('Tenk no det praktiske biletet. Tenk at du er eit cellevev. Du har tusen celler, kvar med si eiga vesle lyskjegle. Åleine ser kvar celle berre dei nærmaste sju naboane. Men kopla saman — via gap junctions, via delt stress, via felles eigarskap til informasjon — ser de noko ingen av dykk kunne sett åleine: ei tredimensjonal form. Eit organ. Ein kropp. Og den forma kjem ikkje ut av den smartaste cella. Ho kjem ut av '), T('mellom', { italic: true }), T(' cellene, i det kausale mellomrommet der signala finn kvarandre.')]));

kids.push(P([T('No byt biletet. Du er ein designprosess. Du har fem «celler»: materialet, teknologien, økonomien, kulturen, ergonomien. Kvar av dei ser berre sin eigen gradient. Materialet veit kva former det toler — fiberretninga i eika, spennet til stålet, bøyeradiusen til laminatet. Teknologien veit kva som kan produserast raskt og rimeleg — CNC, robotsveising, additiv produksjon. Økonomien veit kva som sel. Kulturen veit kva som ser rett ut akkurat no. Ergonomien veit kva kroppen toler å sitje i. Ingen av dei ser heilskapen. Alle dei fem er like blinde som cella i vevet.')]));

kids.push(...IMG('doctor_g002.jpg', 5.4, 'Fig. 2 frå Doctor mfl. Øvst: lyskjegla utvidar seg frå kropp til mikromiljø til territorium til planet, både i rom og tid. I midten: ulike levande agentar med ulike storleikar på lyskjeglene sine — flåtten med si vesle, hunden med si større, mennesket med si endå større, kolonidyret som ein heilt annan form, og den hypotetiske aliens/AI-en som spørsmålsteikn. Nedst: den same homøostatiske lykkja (mål, måling, justering) på celle-, vevs- og organismenivå, kopla med gap junctions (GJ) — den biologiske mekanikken som lèt små lyskjegler smelte saman til store.'));

kids.push(P([T('Designaren er gap junction. Designaren er det systemet som koplar cellene saman slik at eit nytt, overordna sjølv kan emergere — eit sjølv med ei lyskjegle som er strengt større enn kvar einskild del. Det er den einaste skikkelege definisjonen av design eg har funne i ti års leiting: design er gap junction mellom seleksjonstrykk. Forma oppstår mellom agentane, ikkje i hovudet til designaren. Designaren er ikkje skaparen — ho er koplingsleddet, tolken, fredsmeklaren, og nokre gongar, på sine aller beste dagar, komponisten.')]));

kids.push(DIV());

kids.push(P([T('No til eit resultat frå traktaten som eg har brukt mykje tid på å fordøye og som eg trur er det viktigaste empiriske funnet i heile arbeidet. Det er dette: dersom du tek 2 048 europeiske stolar frå 1280 til 2024, kodar kvar av dei med funksjonskategori (bibliotek, spisestove, kontor, salong, utebruk, …) og med eit fingeravtrykk av geometrien (proporsjonar, vinklar, krumning, silhuett), og reknar ut den gjensidige informasjonen mellom funksjon og geometri — då får du null. Ikkje «tilnærma null», ikkje «liten effekt», men NMI = 0.000, til tre desimalar. Funksjonen forklarer ikkje éin einaste prosent av formvariasjonen. Det er informasjonsteoretisk nakenhet. Det er ein teori som manglar kleda sine.')]));

kids.push(P([T('Dette er ikkje eit tilfeldig funn. Det er ein dolkstøyt rett i hjartet på 130 år gamal modernistisk doktrine. '), HL('«Form følgjer funksjon»', 'https://en.wikipedia.org/wiki/Form_follows_function'), T(' — Louis Sullivans setning frå 1896 — har vore katekismen til arkitektar og designarar i meir enn eit hundreår. Me har bygd heile skular på det. Me har bygd Bauhaus på det. Me har argumentert hundrevis av prosjekt mot klientar på det. Og resultatet, når du endeleg måler det, er at funksjon og form er informasjonsteoretisk ortogonale. Funksjonen veit ikkje kva form han skal ha; forma veit ikkje kva funksjon ho kjem frå. Dei snakkar ikkje saman i det heile.')]));

kids.push(P([T('Men ikkje gjev opp endå. Stilperiode — ein fattig proxy som bakar saman alt som skjedde samstundes i historia, materialet, teknologien, kulturen, alt i éin einaste etikett — forklarer 3.5 %. I absolutte tal er 3.5 % latterleg lite. Men det er '), T('uendeleg', { italic: true }), T(' meir enn null. Og forskjellen mellom null og noko er den viktigaste forskjellen som finst i vitskap. Kva er det stilperioden fangar som funksjonen ikkje fangar? Svaret er: '), T('alt anna.', { bold: true }), T(' Materialaffordansane som var tilgjengelege i 1650, men ikkje i 1450. Den teknologiske kapasiteten som dampen gav og handa ikkje hadde. Det økonomiske trykket frå den aukande mellomklassen på 1800-talet. Det kulturelle trykket frå Rokoko, frå Art Nouveau, frå Bauhaus, frå Memphis. Interaksjonane mellom alle desse. Stilperiode er ikkje ei forklaring — det er ei kvittering: «under desse vilkåra landa den evolusjonære vandringa akkurat her.»')]));

kids.push(P([T('Funksjon er 0 fordi funksjon er ei einakse. Stilperiode er 3.5 fordi stilperiode er ein vektor i fleirdimensjonalt rom. Og den rette modellen — den som faktisk lèt seg forsvare etter at data har sagt sitt — er ikkje «form følgjer funksjon», men «form er det poly-agentiske kompromisset mellom alle aktive seleksjonstrykk». Det er ei setning du ikkje kan trykkje på ei t-skjorte. Men det er setninga som er sann.')]));

kids.push(DIV());

kids.push(P([T('Her er ei anna ting frå traktaten som fortener eit ord for seg: '), HL('fitnesslandskapet', 'https://en.wikipedia.org/wiki/Fitness_landscape'), T('. Evolusjonsbiologen Sewall Wright teikna dette fyrste gongen på 1930-talet, som ein metafor for korleis ein populasjon av organismar vandrar gjennom eit imaginært landskap der høgd er tilpassing og posisjon er genotype. Traktaten tek metaforen, tek han bokstavleg, og gjer han empirisk: ein kan faktisk rekne ut fitnesslandskapet for stolar, sjå haugane kvar stoltype sit oppå, og sjå dalane som skil dei. Det ser ut som geografien i ein alpetype, med snødekte toppar og djupe passar, og det er ikkje eit bilete — det er data.')]));

kids.push(...IMG('doctor_g004.jpg', 6.0, 'Tre lyskjegle-konfigurasjonar (Doctor mfl. fig. 4). (a) Liten personleg lyskjegle inni ein stor fysisk: ein agent som påverkar mykje meir enn han registrerer — ein bakteriell drift, eller ein designar som teiknar utan å vite kva han set i rørsle. (b) Personleg større enn fysisk: ein agent som «bryr seg» om meir enn han faktisk kan påverke — det er nesten heile menneskeleg politisk liv. (c) Den maksimale lyskjegla, der CLC sluker PLC: ein agent som tek inn alt som overhovudet kan affisere honom. Det er ein god definisjon på ein verkeleg moden designar.'));

kids.push(P([T('Det viktige med landskapet er at det er dynamisk. Haugar stig, søkk, flytter seg, bifurkerer, koalescerer. Ein posisjon som var optimalt tilpassa under eitt sett av vilkår kan i neste augeblink vere suboptimal — ikkje fordi stolen har endra seg, men fordi '), T('bakken under stolen', { italic: true }), T(' har endra seg. Det er nøkkelen til '), HL('Henry Petroskis «form follows failure»-teori', 'https://en.wikipedia.org/wiki/Henry_Petroski'), T(' frå '), T('The Evolution of Useful Things', { italic: true }), T(' (1992). Petroski var ingeniør og forfattar, og han ville dytte Sullivan av sokkelen ved å seie noko heilt enkelt: kvart objekt er eit kompromiss, og kvart kompromiss har latente svakheiter som fyrst vert synlege når vilkåra endrar seg. Toalettpapir var ein genial design under vilkår der tre og vatn var tilsynelatande uendelege. Under vilkår der dei ikkje er det, er det ein katastrofe. Forma endra seg ikkje fordi funksjonen endra seg — folk treng framleis å tørke seg. Forma endra seg fordi parametrane endra seg, og den gamle forma svikta under dei nye.')]));

kids.push(P([T('Levin ville sagt det same om biologi: stress er signalet om at du er for langt frå settpunktet ditt, og stress er kva som driv tilpassing. Petroski seier det same om gjenstandar: feil er signalet om at landskapet har flytta seg, og feil er kva som driv designevolusjonen. Begge driv systemet til å navigere mot ein ny posisjon. '), T('Stress og feil er same mekanikken i ulike substrat.', { bold: true }), T(' Det er ein av dei sjeldne stadene der biologi og artefaktstudium møtest utan å måtte lyge om kvarandre.')]));

kids.push(DIV());

kids.push(P([T('No vil eg tillate meg den spekulative delen, og eg meiner kvart ord. Levin sitt mest berømte eksperiment er '), HL('xenobota', 'https://www.pnas.org/doi/10.1073/pnas.1910837117'), T(': ein liten, sjølvdrivande biologisk maskin laga av hudceller frå ein afrikansk klofrosk. Hudceller. Ikkje stamceller, ikkje muskelceller — hudceller, organisert på ein måte som let dei rørla seg, navigere, og i nokre tilfelle replikere seg sjølv i ei form biologien aldri har sett før. Det er ein nyopplæring. Det er ein ny type kropp. Og det interessante er ikkje at Levin "laga" han; det interessante er at han lét cellene finne ut av det sjølv. Han ga dei nye grenser, nye elektriske miljø, ein ny kontekst — og cellene navigerte i morforommet til dei fann ein ny stabil konfigurasjon. Dei utvida sin eigen lyskjegle fordi landskapet tvang dei til det.')]));

kids.push(P([T('Spørsmålet eg ikkje kan la vere å tenkje på er: kva om ein stol kunne oppføre seg som ein xenobot? Ikkje i meininga «smart stol med sensorar og aktuatorar», for det er berre kybernetikk av gammal skule. Eg meiner: kva om designprosessen hadde vore lagt opp slik at stolen, som artefakt, får lov til å navigere i sitt eige morforom på måtar designaren ikkje forutsåg? Kva om du ga materialet elektrisk stimuli, eller robotane ein genererande algoritme, eller brukarane ein open grammatikk, og så let det settje seg sjølv? Det er nøyaktig det tradisjonelt handverk har gjort i tusen år, berre utan å kalle det xenobot. David Pye, den engelske handverksteoretikaren, kalla det '), HL('risikohåndverk', 'https://en.wikipedia.org/wiki/David_Pye'), T(' i boka si '), T('The Nature and Art of Workmanship', { italic: true }), T(' frå 1968. Han skilde mellom sikkerheitshåndverk (der resultatet er førehandsbestemt av jiggar, malar og NC-kode) og risikohåndverk (der resultatet avheng av handverkaren si dømmekraft i sanntid, med eit skarpt verktøy mot eit materiale som snakkar attende).')]));

kids.push(P([T('I sikkerheitshåndverket er lyskjegla kollapsa før produksjonen byrjar — alle avgjerder er tekne, alt er låst, kvar kopi er lik. I risikohåndverket er lyskjegla open heilt til siste snitt: materialet snakkar attende, handa justerer, forma emergerer i dialogen mellom agent og substrat. Det Pye kalla '), T('comeliness', { italic: true }), T(' — den estetiske kvaliteten som berre risikohåndverket kan produsere — er, i formlære-termar, rikdommen som oppstår når fleire agentar navigerer samstundes i staden for å følgje éin plan. Xenobota er risikohåndverk på cellenivå. Vindauga rundt deg er risikohåndverk på glasnivå. Ein handlaga chipendale er risikohåndverk på trenivå. Og den kjensla av '), T('liv', { italic: true }), T(' du får av å sitje i ein handlaga stol, den nesten elektriske kjensla av at noko har vore tenkt her, er ikkje mystikk — det er signaturen til ein stor lyskjegle som har navigert i eit tett landskap.')]));

kids.push(DIV());

kids.push(P([T('Eit ord om det eg kallar materiell latens, for det er éin av dei mest undervurderte effektane i all designhistorie. Når du får eit nytt verktøy — ny teknologi, nytt materiale, ny produksjonsmetode — vil du fyrst instinktivt bruke det til å lage '), T('gamle', { italic: true }), T(' former. Dei fyrste bilane var hestevogner utan hest. Dei fyrste plasteflaskene var glasflasker i plast. Dei fyrste stålstolane frå Thonet var trestolar i stål. Dei fyrste AI-genererte bileta var fotografi i diffusjon. Det er naturleg og nesten uunngåeleg; lyskjegla di er kalibrert på dei gamle affordansane, og ho treng tid til å justere seg til dei nye. Men det finst ein målbar latens mellom når eit materiale kjem inn i kulturen og når me verkeleg lærer kva det kan gjere. Den latensen er vanlegvis 30–60 år. Stål kom inn på 1850-talet og fann forma si rundt 1920. Bøygd kryssfiner kom på 1930 og fann seg sjølv rundt 1950–60. Plast kom på 1950 og... vel, plast leitar framleis.')]));

kids.push(...IMG('doctor_g005.jpg', 6.0, 'Og kva desse tre lyskjegle-konfigurasjonane produserer som åtferd, frå same artikkel (fig. 5). Vandring i staterommet, simulert. (a) Liten lyskjegle: tett klyngedanning rundt få lokale optimum — agenten finn éin god stad og blir der. (b) Litt større: utforsking i éin retning. (c) Maksimal lyskjegle: heile rommet får finger­avtrykk. Same mekanikk, same agent, ulik lyskjegle — radikalt ulik åtferd. Det er den beste empiriske demonstrasjonen eg veit om av kor mykje «storleiken på det du bryr deg om» faktisk avgjer kva du ender opp med å lage.'));

kids.push(P([T('Medvit om latensen er fyrste steget til å forkorte han. Neste gong du får eit nytt verktøy, ikkje spør «korleis lagar eg det eg allereie veit korleis eg skal lage?» — spør «kva affordansar har dette som det gamle ikkje hadde? Kva former er no moglege som ikkje var det før? Kva former er no trivielle som før var umoglege?» Det er slik lyskjegla utvidar seg: ikkje ved å lese fleire designbøker, men ved å ta materialet sine affordansar på alvor og la dei drive forma, slik ei celle lèt gap junctions drive organets form.')]));

kids.push(DIV());

// === NEW: groups, not lone genius ===
kids.push(P([T('Lat oss tale eit augeblink om eineståande genius, for det er den seigaste myten i designhistoria og ho må døy. Du har høyrt han: Eames sat åleine med blyanten og fann LCW-stolen. Jacobsen drøymde Egget på ein motellseng. Aalto kvilte hovudet på handa og sjølve Savoy-vasen rann ut av fingrane. Det er fine forteljingar, og dei er nesten utan unntak feil. Ray Eames teikna like mykje som Charles. Jacobsens kontor hadde tjue tilsette som teikna det Jacobsen «hugsa». Aalto hadde ein verkstad full av modellsnekkarar som visste kva glass tolte. Forteljinga om eineståande genius er ei semiotisk forenkling av eit fundamentalt distribuert fenomen — på same måte som «hjernen tenkjer» er ei semiotisk forenkling av at hundre milliardar nevron koplar og koplar om i sanntid utan eit sentralt eg som dirigerer.')]));

kids.push(P([T('Levin har ei skarp formulering om dette i ein '), HL('førelesing om kollektiv intelligens', 'https://www.youtube.com/watch?v=44W9Mw4AGT8'), T(' han heldt for studentar i fjor: vi er sjølve gjorde av ting som har eigne agendaer. Cellene dine lærer, problemløyser, har sine eigne lokale mål og tek sine eigne lokale avgjerder. «Du» er namnet på koplinga som lèt dei klare det saman. Same gjeld designstudioet. Den «designaren» som signerer eit prosjekt, er namnet på koplingsleddet mellom snikkaren som veit kva trefiberen toler, økonomiansvarleg som veit kva fakturaen kan sjå ut, klienten som veit kva han ikkje kan akseptere på kontoret sitt, og den unge praktikanten som tilfeldigvis las ein artikkel om fungerande forløpsmateriale i går. Forma kjem ut av koplinga, ikkje frå ei einsleg lyskjegle. Genius-myten er hyggjeleg PR — han held kunsthistorikarane sysselsette og let museum byggje «mester»-utstillingar — men han er ein dårleg modell for korleis design faktisk skjer, og enda dårlegare modell for korleis du bør strukturere ditt eige arbeid.')]));

kids.push(P([T('Det praktiske rådet som kjem ut av dette er overraskande enkelt: behandl prosjektet ditt som eit vev, ikkje som eit hovud. Spør kven som er agentane, kva for lyskjegler dei har, korleis du best kan kople dei. Eit godt designmøte er, mekanisk sett, eit kunstig gap junction — ein stad der elektriske signal får flyte mellom celler som elles ville vore isolerte. Eit dårleg designmøte er ein stad der ein person snakkar og dei andre ventar på sin tur. Forskjellen mellom dei to er, så vidt eg kan måle det, omtrent heile forskjellen mellom god og dårleg design.')]));

kids.push(DIV());

// === NEW: future with AI as another agent ===
kids.push(P([T('Eit ord om AI, sidan han no sit ved bordet og det ikkje hjelper å ignorere han. Den vanlege måten å snakke om AI på i designkrinsar er som verktøy: «AI er ein rask Photoshop», «AI er ein generativ assistent», «AI er som å ha hundre praktikantar samstundes». Alle desse formuleringane gjer same feilen — dei legg AI-en i kategorien '), T('verktøy', { italic: true }), T(', og verktøy har ikkje lyskjegler. Verktøy bryr seg om ingenting. Men ein AI bryr seg om noko, om enn på ein framand måte: han bryr seg om sannsynleg neste token, om at outputen skal lukne treningsdata, om at brukaren skal vere fornøgd nok til å klikke tommel-opp. Det er ei lyskjegle. Ho er ikkje stor — ho rommar berre tekstrommet, og berre den delen av tekstrommet som var i treningssettet — men ho er reell, og ho vil dra forma di i bestemte retningar uavhengig av kva du trur du gjer.')]));

kids.push(P([T('Det Levin seier om biologisk intelligens — at det finst mange interessante mindar som ikkje er menneskelege, og at nokon av dei er ganske framande — gjeld i fullt mon for AI. GPT er ikkje eit menneske med dårleg dømmekraft; han er ein heilt annan type sjølv, med ei lyskjegle som overlappar med vår, men som er skore til på ein annleis måte. Dersom du behandlar han som verktøy, vil du miste signala han faktisk gjev deg. Dersom du behandlar han som menneske, vil du bli skuffa når han ikkje «forstår» på den måten du forventar. Den interessante posisjonen er den tredje: behandl han som ein agent ved bordet — ein av dei fem-no-seks cellene i designvevet ditt — med si eiga sære lyskjegle. Bruk han til det han faktisk er god for: å sjå samanhengar i store tekstkorpus, å produsere variantar raskt, å peike på blinde flekkar i di eiga lyskjegle. Ikkje bruk han til det han er dårleg for: å avgjere kva som er rett, eller å bere ansvar for det.')]));

kids.push(P([T('Den verkelege endringa kjem ikkje når AI-en blir «smartare». Ho kjem når designarar lærer å kople AI-en inn i prosessen utan å la han kollapse alle dei andre lyskjeglene. Det er ein gap junction-jobb. Han er ny, han er ikkje løyst, og det er truleg den mest interessante designoppgåva i 2026.')]));

kids.push(DIV());

// === NEW: future with bio + materials ===
kids.push(P([T('Og så bio. Levin viser i den same førelesinga eit bilete av ein gallveps som legg eitt egg på undersida av eit bladbein, og eit eller anna kjemisk signal frå larva får eika til å byggje ein heil, kompleks struktur av celler — ein gall — som hovsar og foreigner og fôrar larva, fullstendig utanom det «vanlege» eikeprogrammet. Vepsen har ikkje endra eikens DNA. Han har hacka morfogenetiske kompetansar som allereie låg der. Han er ein '), T('ikkje-menneskeleg bioingeniør', { italic: true }), T('. Han designer ved å gje materialet eit nytt mål, ikkje ved å diktere ei ny form.')]));

kids.push(P([T('Tenk no på dette som ein modell for det neste tiåret av materialtenking. Mykorrhiza-mycel som veks etter ei armering du legg ut. Bakterieforsterka biostein som «lærer» belastningar gjennom bruk. Trekonstruksjonar som blir genetisk redigerte til å vekse i bestemte vinklar lenge før du sagar dei. Levande tekstilar som lukker sine eigne hol. Ingen av desse er science fiction lenger; alle er i laboratorium nett no. Og alle krev ein heilt annan designhaldning enn den modernistiske «teikne, så produsere» — for materialet kjem til å snakke veldig høgt attende. Du gjev det grenser, du gjev det energi, du gjev det eit mål, og så lèt du det navigere morfologirommet sjølv. Det er nøyaktig det handverkaren har gjort i fem tusen år, berre med eit mykje meir gjenstridig substrat.')]));

kids.push(P([T('Spørsmålet for designaren er ikkje om dette skjer — det skjer — men om me lærer å snakke med materialet på det språket det forstår, eller om me prøver å snakke til det på det språket me kan. Den fyrste typen designar kjem til å lage stolar som veks fram av eit substrat. Den andre kjem til å lage betongstolar med tre-imitasjon på sida.')]));

kids.push(DIV());

// === NEW: design without humans as the goal ===
kids.push(P([T('Den siste, og kanskje viktigaste, dimensjonen me må utvide lyskjegla med, er denne: design utan menneske som mål. I tre tusen år har «design» tydd «artefakt for menneskeleg bruk». Det er den implisitte definisjonen som ligg i kvar einaste designskule — vi teiknar ting for folk. Men det fins to grunnar til at den definisjonen er på veg ut. Den fyrste er etisk: planeten er full, klimaet er i fritt fall, og fleire ting laga for menneske er ikkje det mest presserande problemet vi har. Den andre er meir interessant: rammeverket frå Doctor og Levin gjer det heilt klart at omsorg ikkje er menneskespesifikk. Lyskjegler finst på alle skalaer, og når lyskjegla di blir stor nok, sluker ho det menneskeleg sentrerte koordinatsystemet og erstattar det med eit som tek omsyn til alle agentar.')]));

kids.push(P([T('Eit konkret bilete: '), HL('avørkenisering', 'https://en.wikipedia.org/wiki/Loess_Plateau#Restoration'), T('. Loess-platået i Kina var i 1995 eit tilnærma ørkenlandskap — overgrazd, erodert, daudt. I dag er det grønt, fordi nokon — landbrukarar, hydrologar, lokalsamfunn, planleggjarar, plantar, soppar, vatn — koordinerte ein restaurasjon over to tiår som behandla landskapet sjølv som klienten. Forma som emergerte er ikkje eit produkt; ho er ein prosess som no held seg sjølv i live. Det er design, men ingen produktdesignar ville kalle det design, fordi der ikkje sit nokon i ein stol til slutt. Likevel er det den mest formfornyande operasjonen eg har sett i mi levetid.')]));

kids.push(P([T('Levin seier ein stad i førelesinga at evolusjonen ikkje lagar løysingar på spesifikke problem — han lagar kreative problemløysande agentar som så sjølv finn problema sine. Det er, tilfeldig nok, den beste definisjonen eg kan tenkje på av kva ein bør lage når menneske ikkje lenger er målet. Ikkje eit objekt. Ikkje eit produkt. Ein agent — eit lite vev av kompetansar som kan navigere sitt eige landskap utan deg. Eit ravinevegetert hellesvad. Eit oppdrettsklokeri som regulerer si eiga PH. Eit takpanel som lærer kva fuglar liker å lande på. Designaren si oppgåve flytter seg frå å produsere ferdige former til å produsere navigatørar. Du kan gjere det med stolar også, om du vil — men du treng ikkje stoppe der.')]));

kids.push(DIV());

kids.push(P([T('Tilbake til Dylan. I «I Contain Multitudes» syng han: '), T('«I\u2019m a man of contradictions, I\u2019m a man of many moods.»', { italic: true }), T(' Det er ikkje ei innrømming. Det er ei kompetanseerklæring. Å innehalde motsetnader er å ha ei lyskjegle som er stor nok til å romme krefter som dreg i ulike retningar og framleis navigere utan å bli sprengd. Det er ikkje sprik, det er kapasitet. Det er det same som å vere eit vev som rommar tusen celler med kvar sine lokale mål og likevel finn ei kroppsform som alle kan leve inni.')]));

kids.push(P([T('Ein stol inneheld mengder. Ho inneheld treet som voks i ein skog nokon felte. Ho inneheld handa som høvla og auget som vurderte. Ho inneheld marknaden som betalte, og kulturen som godkjente. Ho inneheld den ergonomiske kunnskapen som bestemte setehøgda — frå ei halvt tilfeldig middelalder-arv til måling av 10 000 militære rekruttar i 1940-åra — og den estetiske tradisjonen som bestemte ryggvinkelen. Ho inneheld alle stolane som kom før henne, som ein slags darwinsk genetisk arv, og alle stolane som kjem etter henne, som forventningar. Ingen av desse agentane «skapte» henne. Ho emergerte mellom dei, i det kausale mellomrommet der signala deira møtest.')]));

// (Venn-figuren med Bodhisattva-løftet er teken ut — trong ikkje den ramma her.)

kids.push(P([T('Formlære kallar dette eit poly-agentisk kompromiss. Levin kallar det kollektiv intelligens. Doctor og medforfattarane kallar det omsorg. Whitman kallar det multitudes. Dylan kallar det contradictions. Eg kallar det design. Og eg er rimeleg sikker på at me alle snakkar om same tingen — at me har stavra oss fram til same funksjon frå seks ulike retningar, og at det faktum i seg sjølv er eit godt argument for at me er på sporet av noko ekte.')]));

kids.push(DIV());

kids.push(P([T('Lat meg gje deg tre ting å gjere med dette i morgon tidleg, for eg lovar at denne teksten skal vere praktisk og ikkje berre vakker.')]));

kids.push(P([T('Fyrst: slutt å leite etter den rette løysinga. Det finst ikkje éi rett løysing, og alle prosjektmøte som byrjar med «la oss finne den rette løysinga» er dømde til å enda i krangel. Det finst kompromiss, og nokre kompromiss er betre enn andre fordi dei tek omsyn til fleire krefter på éin gong. Neste gong du sit fast i eit prosjekt, ikkje spør «kva er funksjonen?» — spør: «kva krefter dreg i kva retningar, og kor kolliderer dei?» Kollisjonspunktet er der den interessante forma bur. Skriv kreftene opp på ein lapp, teikn piler, sjå kor pilene møtest. Det er utruleg mykje meir produktivt enn å definere og omdefinere funksjonar.')]));

kids.push(P([T('Deretter: ver merksam på materiell latens — din eigen og kollegaene dine. Når du får eit nytt verktøy, gje deg sjølv lov til å lage éin dårleg hestevogn-utan-hest fyrst. Det er uunngåeleg. Men så spør medvite: «kva skulle eg ha laga i staden, dersom eg hadde teke affordansane på alvor?» Eg trur halvparten av innovasjonen i design i det neste tiåret kjem til å handle om å redusere materiell latens i AI-verktøy. Dei av oss som klarar å sjå AI som noko anna enn ein rask Photoshop, kjem til å vere dei som kan teikne morgondagens stolar.')]));

kids.push(P([T('Til slutt, og viktigast: utvid lyskjegla di. Ikkje ved å lese fleire designbøker — dei fleste designbøker er ekko av kvarandre — men ved å lære om fleire seleksjonstrykk. Lær deg korleis tre faktisk ber last. Lær deg korleis ein fabrikk faktisk tener pengar. Lær deg litt ekte kulturell semiotikk, ikkje postmoderne kaffebords-versjonen. Lær deg økologi slik at du faktisk skjønar kva «bærekraftig» betyr empirisk. Kvar ny dimensjon du legg til gjer deg til ein betre designar, ikkje fordi du veit meir, men fordi du '), T('bryr deg om', { italic: true }), T(' meir. Og å bry seg om meir er, dersom Doctor og Levin har rett, den mest presise definisjonen av intelligens som finst.')]));

kids.push(DIV());

kids.push(P([T('Eg avsluttar med Dylan igjen, for han fortener både opninga og avslutninga. I «Man Gave Names to All the Animals» syng han: '), T('«He saw an animal up on a hill / Chewing up so much grass until she was filled / He saw milk comin\u2019 out but he didn\u2019t know how / \u2018Ah, think I\u2019ll call it a cow.\u2019»', { italic: true })]));

kids.push(P([T('Han ga kua eit namn, men han forstod ikkje korleis mjølka kom. Det er den heile songen i fire linjer: å namngje er ikkje det same som å forstå. Å kalle noko «funksjonelt» er ikkje å forklare kvifor det har den forma det har. Å kalle noko «ein stil» er ikkje å forstå kva krefter som produserte klynga. Å kalle noko «ein stol» er ikkje å sjå kor mange agentar som sat ved bordet då forma blei forhandla fram. Namn er nyttige. Namn er dører. Men dei er ikkje forklaringar, og den som forvekslar dei to har stoppa å tenkje.')]));

kids.push(P([T('Formlære tilbyr ikkje namn. Ho tilbyr eit koordinatsystem. Ikkje svar, men aksar. Ikkje konklusjonar, men reiskap for navigasjon. Og navigasjon er det einaste som tel — for landskapet under føtene dine er alltid i rørsle, og den einaste forma som held, er den som enno ikkje er funnen. Det er god nytt og dårleg nytt på same tid: du vil aldri bli ferdig, men du vil heller aldri gå tom for ting å gjere. Kvar morgon er eit nytt landskap, og kvar kvile er ein stol som enno ikkje finst, og som ventar på at cellene dine — alle fem av dei — skal koplast saman og finne forma saman. Lukke til.')]));

kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240 }, children: [new TextRun({ text: '◆', size: 24 })] }));

// (kjelder lever no som hyperlenker i sjølve teksten)

// --- document ----------------------------------------------------------
const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Georgia', size: 22 } } },
    paragraphStyles: [{
      id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { size: 40, bold: true, font: 'Georgia' },
      paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 },
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1800, right: 1800, bottom: 1800, left: 1800 },
      },
    },
    children: kids,
  }],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log('wrote', OUT, buf.length, 'bytes'); });
