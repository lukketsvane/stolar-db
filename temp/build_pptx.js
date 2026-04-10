const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Iver Raknes Finne";
pres.title = "Stolen som formhistorisk laboratorium";

// White-based palette
const WHITE  = "FFFFFF";
const OFF    = "F7F4F0";
const DARK   = "1A1714";
const RUST   = "B8542A";
const TEAL   = "2B5F75";
const MUTED  = "888077";
const SIG    = "Iver Raknes Finne \u2014 70142 V26";
const FIG    = path.join(__dirname, "..", "analysis", "figures");

function sig(slide) {
  slide.addText(SIG, {
    x: 0.4, y: 5.15, w: 9.2, h: 0.35,
    fontSize: 8, fontFace: "Georgia", color: MUTED,
    align: "right", margin: 0,
  });
}

// ============================================================
// SLIDE 1 — Tittelslide (mørk, einaste mørke)
// ============================================================
let s1 = pres.addSlide();
s1.background = { color: DARK };
s1.addImage({
  path: path.join(FIG, "fig-A.6.21-gradient.png"),
  x: 0, y: 0, w: 10, h: 5.625,
  transparency: 70,
});
s1.addText("STOLEN SOM\nFORMHISTORISK\nLABORATORIUM", {
  x: 0.7, y: 0.7, w: 8.5, h: 3.0,
  fontSize: 48, fontFace: "Georgia", color: WHITE,
  bold: true, lineSpacingMultiple: 1.1, margin: 0,
});
s1.addShape("rect", { x: 0.7, y: 3.8, w: 3, h: 0, line: { color: RUST, width: 3 } });
s1.addText("2\u2009300 europeiske stolar, 1280\u20132024", {
  x: 0.7, y: 3.98, w: 7, h: 0.45,
  fontSize: 17, fontFace: "Georgia", color: "BBBBBB", margin: 0,
});
s1.addText(SIG, {
  x: 0.7, y: 4.55, w: 5, h: 0.35,
  fontSize: 12, fontFace: "Georgia", color: RUST, margin: 0,
});
s1.addNotes("Eg har valt stolen \u2014 ikkje \u00e9in stol, men stolen som klasse. Stolen er det mest designa bruksobjektet i europeisk historie. Kvar epoke, kvart materiale, kvar ideologi har forma sin versjon. Det gjer stolen til eit unikt laboratorium for \u00e5 studere korleis form faktisk oppst\u00e5r. I dette prosjektet har eg samla 2\u2009300 stolar fr\u00e5 Nasjonalmuseet og Victoria & Albert Museum og analysert dei kvantitativt \u2014 ikkje som symbol eller narrativ, men som m\u00e5lbare konfigurasjonar i eit morfologisk rom. Det er denne prosessen \u2014 kvantitativ formanalyse \u2014 eg vil argumentere for som avgjerande for designfaget framover.");

// ============================================================
// SLIDE 2 — Storatlaset
// ============================================================
let s2 = pres.addSlide();
s2.background = { color: WHITE };
s2.addImage({
  path: path.join(FIG, "fig-A.6.21-gradient.png"),
  x: 0.3, y: 0.85, w: 9.4, h: 4.25,
  sizing: { type: "contain", w: 9.4, h: 4.25 },
});
s2.addText("STORATLASET", {
  x: 0.5, y: 0.12, w: 5, h: 0.55,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 6, margin: 0,
});
s2.addText("Nasjonalmuseet + Victoria & Albert Museum \u2014 kvart bilete er \u00e9in stol", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s2);
s2.addNotes("Dette er storatlaset: 2\u2009300 stolar fr\u00e5 to av Europas viktigaste samlingar. Kvar prikk p\u00e5 skjermen er ein reell stol med katalognummer, m\u00e5l, materiale, datering og stilperiode. Eg har brukt Nasjonalmuseets og V&A sine opne API-ar til \u00e5 hente all metadata, og deretter generert 3D-modellar av kvar stol ved hjelp av AI. Til saman dekkjer datasettet 744 \u00e5r med europeisk m\u00f8belhistorie. Det er ikkje eit utval \u2014 det er i praksis heile den tilgjengelege digitaliserte samlinga. Og n\u00e5r ein har 2\u2009300 individ med m\u00e5l, kan ein byrje \u00e5 sj\u00e5 m\u00f8nster som er usynlege for det blotte auge.");

// ============================================================
// SLIDE 3 — 744 år
// ============================================================
let s3 = pres.addSlide();
s3.background = { color: WHITE };
s3.addImage({
  path: path.join(FIG, "chairs_top144_16x9.jpg"),
  x: 0.3, y: 0.85, w: 9.4, h: 4.25,
  sizing: { type: "contain", w: 9.4, h: 4.25 },
});
s3.addText("744 \u00c5R MED FORM", {
  x: 0.5, y: 0.12, w: 5, h: 0.55,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 6, margin: 0,
});
s3.addText("Fr\u00e5 gotiske trestolar til 3D-printa plast \u2014 same funksjon, radikalt ulik form", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s3);
s3.addNotes("Alle desse stolane l\u00f8yser same oppg\u00e5ve: \u00e5 bere eit menneske i sitjande stilling. Ergonomien er konstant \u2014 menneskekroppen har ikkje endra seg p\u00e5 500 \u00e5r. Likevel varierer forma enormt. H\u00f8gda har falle fr\u00e5 95 til 75 centimeter i median. Proporsjonane \u2014 h\u00f8gde delt p\u00e5 breidde \u2014 har g\u00e5tt fr\u00e5 1,88 i 1600 til 1,36 i dag. Det er ikkje ein funksjonsdrift, det er ein formdrift. Og det er akkurat dette paradokset som gjer stolen til eit s\u00e5 godt laboratorium: funksjonen er kontrollert, forma varierer fritt, og vi kan m\u00e5le kvifor.");

// ============================================================
// SLIDE 4 — Seleksjonstrykk (uniformitet / MI)
// ============================================================
let s4 = pres.addSlide();
s4.background = { color: OFF };
// Two-column: left chart, right text/caption
s4.addImage({
  path: path.join(FIG, "fig-A.6.1-uniformitet.png"),
  x: 0.4, y: 0.85, w: 5.8, h: 4.2,
  sizing: { type: "contain", w: 5.8, h: 4.2 },
});
s4.addText("FIRE SELEKSJONSTRYKK", {
  x: 0.5, y: 0.12, w: 8, h: 0.55,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 6, margin: 0,
});
// Right column key findings
s4.addText("Stilperiode forklarer\n2,3\u00d7 meir", {
  x: 6.6, y: 1.1, w: 3.1, h: 0.9,
  fontSize: 28, fontFace: "Georgia", color: RUST,
  bold: true, lineSpacingMultiple: 1.1, margin: 0,
});
s4.addText("av h\u00f8gde-variasjonen enn\nmateriale \u2014 time beats substrate", {
  x: 6.6, y: 2.05, w: 3.1, h: 0.7,
  fontSize: 12, fontFace: "Georgia", color: DARK,
  lineSpacingMultiple: 1.2, margin: 0,
});
s4.addShape("rect", { x: 6.6, y: 2.85, w: 2.5, h: 0, line: { color: TEAL, width: 2 } });
s4.addText("Men materiale er heller\nikkje konfundert med tid\n(Cram\u00e9r's V = 0,33)", {
  x: 6.6, y: 3.0, w: 3.1, h: 0.85,
  fontSize: 11, fontFace: "Georgia", color: MUTED,
  lineSpacingMultiple: 1.2, margin: 0,
});
s4.addText("Gjensidig informasjon (bits) per seleksjonstrykk for alle tre dimensjonar", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s4);
s4.addNotes("Kva krefter formar stolen mest? Vi m\u00e5ler dette med gjensidig informasjon \u2014 kor mange bits om geometrien ein variabel gjev oss. Stilperiode slår materiale 1,9\u20132,3\u00d7 p\u00e5 alle tre dimensjonar. Men \u2014 avgjerande \u2014 material er ikkje konfundert med stilperiode: Cram\u00e9r\u2019s V er berre 0,33. Det tyder at materiale har ein eigenst\u00e5ande effekt p\u00e5 forma, sjsett fr\u00e5 tidsperioden. Det er dette vi meiner med seleksjonstrykk: kvar faktor \u2014 tid, materiale, nasjon, stil \u2014 forklarer noko unikt av formvariasjonen. Form er ikkje monokausal.");

// ============================================================
// SLIDE 5 — Bimodal morfospace
// ============================================================
let s5 = pres.addSlide();
s5.background = { color: WHITE };
s5.addImage({
  path: path.join(FIG, "fig-A.6-morfospace-bimodal.png"),
  x: 0.3, y: 0.85, w: 9.4, h: 4.25,
  sizing: { type: "contain", w: 9.4, h: 4.25 },
});
s5.addText("MORFOSPACE: TO VERDAR", {
  x: 0.5, y: 0.12, w: 6, h: 0.55,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 6, margin: 0,
});
s5.addText("Tradisjonell stol ~85\u201395 cm \u00b7 Modernistisk stol ~40\u201350 cm \u00b7 Attraktorpunkt 53\u00d786 cm", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s5);
s5.addNotes("Her ser de morforommet direkte: over 1\u2009600 stolar plotta i to projeksjonar \u2014 h\u00f8gde mot breidde og h\u00f8gde mot djupn. Det er to klare attraktorar: den tradisjonelle stolen kring 85\u201395 cm h\u00f8gde, og den modernistiske stolen kring 40\u201350 cm. Attraktorpunktet \u2014 det matematiske tyngdepunktet \u2014 ligg p\u00e5 53\u00d786 cm, mellom dei to klyngane. Rommet er bimodalt, ikkje unimodalt. Og det bimodale m\u00f8nsteret oppst\u00e5r p\u00e5 tvers av material \u2014 b\u00e5de tre og metall finst i begge klyngane. Det er ikkje materialet som avgjer h\u00f8gda, det er tidsepoken.");

// ============================================================
// SLIDE 6 — Kraftfeltet
// ============================================================
let s6 = pres.addSlide();
s6.background = { color: WHITE };
s6.addImage({
  path: path.join(FIG, "fig-A.6.19-kraftfelt.png"),
  x: 1.8, y: 0.25, w: 6.4, h: 5.1,
  sizing: { type: "contain", w: 6.4, h: 5.1 },
});
s6.addText("FORMROMMET SOM KRAFTFELT", {
  x: 0.5, y: 0.05, w: 8, h: 0.45,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 5, margin: 0,
});
s6.addText("Konturar = tettleik \u00b7 Pilar = gradient \u00b7 Bl\u00e5 linje = stiltrajektor 1530\u20132025", {
  x: 0.5, y: 5.28, w: 9, h: 0.28,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s6);
s6.addNotes("Dette er den viktigaste visualiseringa i heile prosjektet. Bakgrunnen er tettleiks-konturane for morforommet \u2014 kvar stolane faktisk klyngar seg. Pilane viser gradienten i kva retning \u00abformtyngdekrafta\u00bb trekkjer. Dei peikar mot Nyklassisisme og Historisme som attraktorar. Den bl\u00e5e linja er den faktiske trajektorien for den gjennomsnittlege stolen fr\u00e5 1530 til 2025. Trajekt\u00f8ren vandrar rundt attraktorane, kjem attende, vekslar. Banelengda er 84 cm, men netto skift berre 25 cm \u2014 tortuositeten er 3,45. Dette er signaturen til eit dynamisk system med m\u00f8nster, ikkje eit tilfeldig system. Det er designhistorie som fysikk.");

// ============================================================
// SLIDE 7 — Materiallatens
// ============================================================
let s7 = pres.addSlide();
s7.background = { color: WHITE };
s7.addImage({
  path: path.join(FIG, "fig-A.6.18-materiallatens.png"),
  x: 0.5, y: 0.75, w: 9, h: 4.5,
  sizing: { type: "contain", w: 9, h: 4.5 },
});
s7.addText("SUBSTRAT-SKIFTE OPNAR NYE FORMAR", {
  x: 0.5, y: 0.1, w: 8, h: 0.52,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 5, margin: 0,
});
s7.addText("St\u00e5l og aluminium ligg n\u00e6r tre-sona fram til 1900, s\u00e5 sprett dei til nye geometriske regionar", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s7);
s7.addNotes("Dette er substrat-skifte-hypotesen empirisk dokumentert. St\u00e5l, aluminium og kryssfinér ligg alle n\u00e6r den tradisjonelle tre-sentrumssona fr\u00e5 dei kjem inn \u2014 dei imiterer tre i byrjinga. Deretter, kring 1950\u20131970, skjer spranget: dei hoppar til heilt nye posisjonar i morforommet. St\u00e5l dreg mot lAgare, slankare stolar. Aluminium finn sine eigne geometriske nisjar. Den nedre grafen viser Latent-avvik fr\u00e5 det sentrale morforommet \u2014 alle material held seg innafor 12 cm fr\u00e5 senter fram til rundt 1900. Nye material opnar nye morfologiske rom. Det er dette som gjer industriell teknologi til eit formhistorisk vendepunkt \u2014 ikkje berre eit produksjonshistorisk vendepunkt.");

// ============================================================
// SLIDE 8 — Stilar er gradientar (silhouette)
// ============================================================
let s8 = pres.addSlide();
s8.background = { color: WHITE };
s8.addImage({
  path: path.join(FIG, "fig-A.6.3-silhouette.png"),
  x: 0.5, y: 0.85, w: 9, h: 4.15,
  sizing: { type: "contain", w: 9, h: 4.15 },
});
s8.addText("STILAR ER GRADIENTAR, IKKJE KATEGORIAR", {
  x: 0.5, y: 0.12, w: 9, h: 0.55,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 4, margin: 0,
});
s8.addText("Gjennomsnittleg silhouette-sk\u00e5re: \u22120,338 \u2014 stilperiodar overlappar massivt i formrommet", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s8);
s8.addNotes("Dette er kanskje det viktigaste enkeltfunnet. Silhouette-sk\u00e5ren m\u00e5ler kor distinkt kvar stilperiode er som morfologisk klynge. Gjennomsnittleg sk\u00e5re er minus 0,338, langt under null. Ein sk\u00e5re under null tyder at objekta er n\u00e6rare nabostilane enn sin eigen stil. Rokokko, barokk, empire \u2014 nyttige merkelappar, men dei skildrar ikkje reelle brot i morforommet. Berre H\u00e9pplewhite og R\u00e9gence har positiv sk\u00e5re \u2014 dei er morfologisk genuine. For designfaget: vi treng ikkje fleire stilkategoriar, vi treng betre kart over dei faktiske attraktorane i formrommet.");

// ============================================================
// SLIDE 9 — Form driftar (proporsjon)
// ============================================================
let s9 = pres.addSlide();
s9.background = { color: WHITE };
s9.addImage({
  path: path.join(FIG, "fig-A.6.10-proporsjon.png"),
  x: 0.5, y: 0.85, w: 9, h: 4.2,
  sizing: { type: "contain", w: 9, h: 4.2 },
});
s9.addText("FORM DRIFTAR UAVHENGIG AV FUNKSJON", {
  x: 0.5, y: 0.12, w: 9, h: 0.55,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 4, margin: 0,
});
s9.addText("H/B-medianen fell fr\u00e5 1,88 til 1,36 over 500 \u00e5r \u2014 ergonomien er konstant, forma driftar", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s9);
s9.addNotes("Denne grafen viser proporsjonen \u2014 h\u00f8gde delt p\u00e5 breidde \u2014 over 500 \u00e5r. Den r\u00f8de linja er rullande median. Linja fell systematisk fr\u00e5 1,88 til 1,36. Stolen har blitt flatare og breiare. Men mennesket har ikkje endra seg \u2014 seteflata er framleis tilpassa same kropp. Det er ikkje funksjon som driv endringa. Wasserstein-distansen mellom kvar 50-\u00e5rsperiode er gjennomsnittleg 15,8 cm. Ingen periode liknar den f\u00f8rre. Til h\u00f8gre ser de violinplots som viser korleis proporsjonfordelinga er per hundre\u00e5r \u2014 1600-stolane kjem aldri att. Formhistoria er irreversibel og dynamisk.");

// ============================================================
// SLIDE 10 — Materiale formar
// ============================================================
let s10 = pres.addSlide();
s10.background = { color: WHITE };
s10.addImage({
  path: path.join(FIG, "fig-A.6.11-materialnisjar.png"),
  x: 0.5, y: 0.85, w: 9, h: 4.2,
  sizing: { type: "contain", w: 9, h: 4.2 },
});
s10.addText("MATERIALE FORMAR \u2014 MEIR ENN IDEOLOGI", {
  x: 0.5, y: 0.1, w: 9, h: 0.6,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 4, margin: 0,
});
s10.addText("Trestolar ~85 cm \u00b7 St\u00e5l og plast ~67 cm \u2014 same sitjefunksjon, ulike geometriske nisjar", {
  x: 0.5, y: 5.1, w: 8.5, h: 0.3,
  fontSize: 9, fontFace: "Georgia", color: MUTED, margin: 0,
});
sig(s10);
s10.addNotes("Materiale er ikkje berre ein teknisk detalj \u2014 det er ein geometrisk akse i morforommet. Dei store fargede kulene er sentroidane for kvart materiale \u2014 det morfologiske tyngdepunktet. Trestolar i eik, n\u00f8ttetre og mahogni klyngar seg kring 85 cm h\u00f8gde. St\u00e5l- og plaststolar sit 18 cm l\u00e5gare, kring 67 cm. Same sitjefunksjon, men radikalt ulike formregionar. Cram\u00e9r\u2019s V mellom stilperiode og materiale er 0,33, langt under 0,9. Material har eigenst\u00e5ande form-effekt. For designfaget framover: n\u00e5r AI genererer mobler, vil det reprodusere desse materie-nisjar automatisk \u2014 om vi ikkje forstod dei empirisk f\u00f8rst.");

// ============================================================
// SLIDE 11 — Konklusjon
// ============================================================
let s11 = pres.addSlide();
s11.background = { color: DARK };
s11.addImage({
  path: path.join(FIG, "fig-A.6.21-gradient.png"),
  x: 0, y: 0, w: 10, h: 5.625,
  transparency: 82,
});
s11.addText("KVIFOR DETTE ER AVGJERANDE\nFOR DESIGNFAGET FRAMOVER", {
  x: 0.7, y: 0.45, w: 8.5, h: 1.5,
  fontSize: 27, fontFace: "Georgia", color: WHITE,
  bold: true, lineSpacingMultiple: 1.15, margin: 0,
});
s11.addShape("rect", { x: 0.7, y: 2.05, w: 2.5, h: 0, line: { color: RUST, width: 3 } });
const pts = [
  { n: "01", t: "Generativ design treng empiriske formkart", b: "AI-verkt\u00f8y l\u00e6rer fr\u00e5 det historiske arkivet. Utan m\u00e5lbare kart navigerer dei blindt." },
  { n: "02", t: "Data utfordrar etablerte narrativ", b: "Stilperiodar er gradientar, ikkje kategoriar. Materiale formar meir enn ideologi \u2014 empirisk s\u00e5 solid at det ikkje kan avvisast." },
  { n: "03", t: "Stolen er prototypen for metoden", b: "744 \u00e5r, 2\u2009300 individ, \u00e9in kontrollert funksjon. Det perfekte laboratoriet for kvantitativ formteori." },
];
pts.forEach((p, i) => {
  const y = 2.3 + i * 1.0;
  s11.addText(p.n, { x: 0.7, y, w: 0.6, h: 0.45, fontSize: 15, fontFace: "Georgia", color: RUST, bold: true, margin: 0 });
  s11.addText(p.t, { x: 1.4, y, w: 3.5, h: 0.45, fontSize: 13, fontFace: "Georgia", color: WHITE, bold: true, margin: 0 });
  s11.addText(p.b, { x: 5.2, y, w: 4.4, h: 0.8, fontSize: 10.5, fontFace: "Georgia", color: "AAAAAA", margin: 0 });
});
s11.addText(SIG, { x: 0.5, y: 5.15, w: 9.2, h: 0.35, fontSize: 8, fontFace: "Georgia", color: "666666", align: "right", margin: 0 });
s11.addNotes("For \u00e5 summere: kvifor er stolen som formhistorisk laboratorium relevant for designfaget framover? For det f\u00f8rste: generative verkt\u00f8y, AI-design og parametrisk modellering treng ikkje berre estetiske referansar \u2014 dei treng empiriske formkart. FORML\u00c6RE gjev det f\u00f8rste systematiske fors\u00f8ket p\u00e5 \u00e5 bygge slike kart fr\u00e5 reelle museumsdata. For det andre: kvantitativ empiri utfordrar etablerte narrativ. Stilperiodar er gradientar, materiale formar meir enn ideologi \u2014 desse funna er s\u00e5 solide at dei ikkje kan avvisast med estetisk argumentasjon. For det tredje: stolen er den perfekte prototypen \u2014 744 \u00e5r, 2\u2009300 individ, \u00e9in kontrollert funksjon. Takk for merksemda.");

// ============================================================
// SLIDE 12 — Referansar
// ============================================================
let s12 = pres.addSlide();
s12.background = { color: WHITE };
s12.addText("REFERANSAR", {
  x: 0.7, y: 0.25, w: 5, h: 0.5,
  fontSize: 13, fontFace: "Georgia", color: RUST,
  charSpacing: 6, margin: 0,
});
const refs = [
  "Finne, I. R. (2026). FORML\u00c6RE: Sju proposisjonar om korleis form oppst\u00e5r. Masteroppg\u00e5ve, AHO.",
  "Nasjonalmuseet for kunst, arkitektur og design. Digitalt Museum API. digitaltmuseum.org",
  "Victoria and Albert Museum. Collections API. api.vam.ac.uk",
  "Raup, D. M. (1966). \u00abGeometric analysis of shell coiling.\u00bb Journal of Paleontology, 40(5).",
  "Thompson, D. W. (1917). On Growth and Form. Cambridge University Press.",
  "Wright, S. (1932). \u00abRoles of mutation, inbreeding and selection in evolution.\u00bb Proc. 6th Int. Cong. Genetics.",
  "Kauffman, S. A. (2000). Investigations. Oxford University Press.",
  "Mitteroecker, P. & Huttegger, S. M. (2009). \u00abThe concept of morphospaces.\u00bb Evolution, 63(5).",
  "Shannon, C. E. (1948). \u00abA Mathematical Theory of Communication.\u00bb Bell System Technical Journal, 27(3).",
  "",
  "Bilete: Nasjonalmuseet og V&A Museum (opne samlingar). 3D-modellar: Hunyuan3D-2.",
  "Statistisk analyse: Python (scikit-learn, SciPy, matplotlib). Datasett: github.com/lukketsvane/stolar-db",
  "Interaktive utforskarar: stolar.iverfinne.no \u2014 turnable-db.iverfinne.no",
];
s12.addText(
  refs.map((r, i) => ({
    text: r,
    options: { breakLine: true, fontSize: r === "" ? 5 : 10, color: i >= 10 ? MUTED : DARK },
  })),
  { x: 0.7, y: 0.9, w: 8.5, h: 4.4, fontFace: "Georgia", valign: "top", margin: 0, paraSpaceAfter: 5 }
);
sig(s12);
s12.addNotes("Alle bilete er fr\u00e5 Nasjonalmuseet og Victoria & Albert Museum sine opne samlingar. 3D-modellane er genererte med Hunyuan3D-2. Statistisk analyse er gjort i Python med scikit-learn, SciPy og matplotlib. Fullstendig datasett og kode ligg ope p\u00e5 GitHub. Interaktive utforskarar p\u00e5 stolar.iverfinne.no og turnable-db.iverfinne.no. Takk for merksemda.");

// ============================================================
// WRITE
// ============================================================
const outPath = path.join(__dirname, "..", "output_pdfs", "Iver Raknes Finne 70142 V26.pptx");
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("DONE: " + outPath);
}).catch(err => { console.error(err); });
