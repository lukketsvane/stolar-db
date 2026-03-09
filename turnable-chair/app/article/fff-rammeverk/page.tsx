"use client"

import ArticleLayout from "../../../components/article-layout"
import Content from "../content/artikkel_4.mdx"

export default function ArticleFourPage() {
  const header = (
    <div className="w-full">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">Forskingsartikkel IV</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Form Follows<br/>
        <span className="text-gray-200">Fitness.</span>
      </h1>
      <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight mt-8">
        Empirisk grunnlag for eit evolusjonært rammeverk i estetiske fag.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-20 border-y border-gray-100 py-16 my-16 font-sans">
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Forfattar</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Iver Raknes Finne</p>
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">AHO</p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Metode</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">Informasjonsteori</p>
        </div>
      </div>

      <div className="mt-16 py-8 border-t border-black">
        <p className="text-xl font-serif italic leading-relaxed text-black">
          <strong>Samandrag:</strong> Det modernistiske dogmet "form follows function" impliserer at form er deduserbar frå funksjon. Denne artikkelen falsifiserer dette empirisk ved å analysere 93 stolar frå Nasjonalmuseet si samling gjennom 21 geometriske og 30 materielle eigenskapar utrekna frå 3D-modellar. Artikkelen presenterer Form Follows Fitness (FFF) som eit alternativ.
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
          <p>Alexander, C. (1964). <em className="normal-case">Notes on the Synthesis of Form.</em> Harvard University Press.</p>
          <p>Clark, A. (2008). <em className="normal-case">Supersizing the Mind.</em> Oxford University Press.</p>
          <p>Giedion, S. (1948). <em className="normal-case">Mechanization Takes Command.</em> Oxford University Press.</p>
          <p>Kauffman, S. A. (1993). <em className="normal-case">The Origins of Order.</em> Oxford University Press.</p>
          <p>Sullivan, L. H. (1896). The tall office building artistically considered. <em className="normal-case">Lippincott's Magazine.</em></p>
        </div>
        <div className="mt-40 pt-16 border-t border-gray-50 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
          <p>&copy; 2026 Iver Raknes Finne</p>
          <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
        </div>
      </footer>
    </ArticleLayout>
  )
}
