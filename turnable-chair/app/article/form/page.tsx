"use client"

import ArticleLayout from "../../../components/article-layout"
import Content from "../content/artikkel_2.mdx"

export default function FormArticlePage() {
  const header = (
    <div className="w-full">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel II</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Form follows<br/>
        <span className="text-gray-200">fitness.</span>
      </h1>
      <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight mt-8">
        Mot ein evolusjonær formteori for stolen.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16 font-sans">
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">
            Institutt for design, Arkitektur- og designhøgskolen i Oslo (AHO)
          </p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Formkurveanalyse</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed">
            Kvantitativ analyse av dimensjonar over 740 år med stoldesign.
          </p>
        </div>
      </div>

      <div className="mt-16 py-8 border-t border-black">
        <p className="text-xl font-serif italic leading-relaxed text-black">
          <strong>Samandrag:</strong> Denne artikkelen introduserer <em>form follows fitness</em> som eit evolusjonært rammeverk for å analysere formutvikling i industridesign, med Nasjonalmuseet si stolsamling som empirisk grunnlag. Mot Le Corbusier sin maskinanalogi og Sullivan sitt "form follows function" set artikkelen ein tredje posisjon: form fylgjer ikkje funksjon som eit logisk resultat, men <em>fitness</em> som eit seleksjonstrykk. Hovudfunnet er <em>fitness-konvergensen</em>: ein empirisk demonstrerbar tendens der stolar frå ulike stilperiodar konvergerer mot eit felles dimensjonsområde etter industrialiseringa.
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
          <p>Darwin, C. (1859). <em className="normal-case">On the Origin of Species.</em> Murray.</p>
          <p>Dennett, D. C. (1995). <em className="normal-case">Darwin's Dangerous Idea.</em> Simon & Schuster.</p>
          <p>Finne, I. R. (2026a). <em className="normal-case">Materialhistorie: Kolonialt arkiv.</em> AHO Working Paper.</p>
          <p>Manovich, L. (2020). <em className="normal-case">Cultural Analytics.</em> MIT Press.</p>
          <p>Pye, D. (1968). <em className="normal-case">The Nature and Art of Workmanship.</em> Cambridge University Press.</p>
          <p>Steadman, P. (2008). <em className="normal-case">The Evolution of Designs.</em> Routledge.</p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case">Lippincott's Magazine.</em></p>
          <p>Thompson, D. W. (1917). <em className="normal-case">On Growth and Form.</em> Cambridge University Press.</p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
