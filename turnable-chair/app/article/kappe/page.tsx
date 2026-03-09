"use client"

import ArticleLayout from "../../../components/article-layout"
import Content from "../content/artikkel_5.mdx"

export default function ArticleFivePage() {
  const header = (
    <div className="w-full">
      <p className="text-xs font-mono font-black uppercase tracking-[0.5em] text-gray-300 mb-12">PhD-kappe</p>
      <h1 className="text-6xl md:text-[8rem] font-sans font-black tracking-tighter leading-[0.8] mb-16 text-black">
        Distribuert<br/>
        <span className="text-gray-200">intelligens.</span>
      </h1>
      <p className="text-2xl md:text-4xl font-sans font-black tracking-tight text-gray-400 leading-tight mt-8">
        Eit nytt paradigme for estetiske fag.
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
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Type</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">PhD-kappe</p>
        </div>
      </div>

      <div className="mt-16 py-8 border-t border-black">
        <p className="text-xl font-serif italic leading-relaxed text-black">
          <strong>Samandrag:</strong> I 130 år har estetiske fag operert under eit deterministisk aksiom: "form follows function". Denne kappa bind saman fire empiriske artiklar som til saman falsifiserer aksiomet og etablerer eit alternativ. Kappa formulerer Form Follows Fitness (FFF) som eit fullstendig paradigmeskifte der formgjeving vert forstått som ein distribuert intelligent prosess.
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
          <p>Clark, A. (2008). <em className="normal-case">Supersizing the Mind.</em> Oxford University Press.</p>
          <p>Corbusier, Le (1923). <em className="normal-case">Vers une architecture.</em> Cres.</p>
          <p>Kuhn, T. S. (1962). <em className="normal-case">The Structure of Scientific Revolutions.</em> University of Chicago Press.</p>
          <p>Levin, M. (2019). The computational boundary of a self. <em className="normal-case">Frontiers in Psychology.</em></p>
          <p>Nakagaki, T. et al. (2000). Intelligence: Maze-solving by an amoeboid organism. <em className="normal-case">Nature.</em></p>
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
