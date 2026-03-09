"use client"

import ArticleLayout from "../../../components/article-layout"
import Content from "../content/artikkel_3.mdx"

export default function ArticleThreePage() {
  const header = (
    <div className="w-full">
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

      <div className="mt-16 py-8 border-t border-black">
        <p className="text-xl font-serif italic leading-relaxed text-black">
          <strong>Samandrag:</strong> Dersom funksjonalismen sitt dogme stemmer, at form fylgjer funksjon, burde stolar frå ulike nasjonar og tidsaldrar ikkje låt seg skilje geometrisk, sidan sitjefunksjonen er universell. Denne artikkelen testar påstanden empirisk gjennom maskinlæring på tredimensjonale punktsskyer frå 401 GLB-modellar i Nasjonalmuseet si samling. Funna falsifiserer funksjonalismen si nøytrale formlære: form kodar kulturell identitet og historisk tid romleg og geometrisk.
        </p>
      </div>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <Content />
      <footer className="max-w-5xl mx-auto py-40 px-8 border-t border-gray-100 mt-40">
        <p className="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-16">Referansar</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm font-sans font-bold text-gray-500 leading-relaxed uppercase tracking-tighter">
          <p>Corbusier, Le (1923). <em className="normal-case">Vers une architecture.</em> Cres.</p>
          <p>Finne, I. R. (2026a). <em className="normal-case">Materialhistorie: Kolonialt arkiv.</em> AHO Working Paper.</p>
          <p>Finne, I. R. (2026b). <em className="normal-case">Form follows fitness.</em> AHO Working Paper.</p>
          <p>Lucie-Smith, E. (1979). <em className="normal-case">A History of Furniture.</em> William Morrow.</p>
          <p>Manovich, L. (2020). <em className="normal-case">Cultural Analytics.</em> MIT Press.</p>
          <p>Osada, R. et al. (2002). Shape distributions. <em className="normal-case">ACM Transactions on Graphics.</em></p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
