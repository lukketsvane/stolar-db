"use client"

import { useRouter } from "next/navigation"

export default function ArticlePage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-gray-50 text-black font-serif selection:bg-black selection:text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-md border-b border-gray-200 z-50 px-6 py-4">
        <button
          onClick={() => router.push('/')}
          className="flex items-center text-sm font-sans font-medium text-gray-600 hover:text-black transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Database
        </button>
      </nav>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto pt-32 pb-24 px-6 md:px-12">
        {/* Header */}
        <header className="mb-16 text-center">
          <p className="text-sm font-sans font-bold tracking-widest text-gray-500 uppercase mb-4">Research Article</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-6 font-sans">
            Norske Stoler: A Quantitative Analysis of Production and Material Diversity
          </h1>
          <p className="text-lg text-gray-600 italic">
            Exploring the Nasjonalmuseet collection through spatial and temporal lenses.
          </p>
          
          <div className="mt-8 flex items-center justify-center space-x-4 font-sans text-sm text-gray-500">
            <span>Published: March 2026</span>
            <span>&bull;</span>
            <span>Data from 121 Norwegian Chairs</span>
          </div>
        </header>

        {/* Abstract */}
        <section className="mb-12 text-lg leading-relaxed text-gray-800">
          <p>
            <strong>Abstract:</strong> This article presents a data-driven investigation into the production history of Norwegian chairs housed within the Nasjonalmuseet. By analyzing 121 cataloged items, we reveal significant geographic clustering of production facilities and distinct temporal trends in material usage and stylistic evolution from the mid-19th century to the late 20th century.
          </p>
        </section>

        {/* Section 1 */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold font-sans mb-6">1. Geographic Distribution of Production</h2>
          <p className="text-lg leading-relaxed text-gray-800 mb-8">
            The spatial analysis of chair manufacturing demonstrates a heavy concentration in specific regions. Historical centers of craftsmanship heavily influenced the stylistic output of the respective eras. As seen in the production geography data, the west coast and central eastern regions dominate the historical output.
          </p>
          
          {/* Figure 1 Placeholder */}
          <figure className="my-10 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="aspect-video bg-gray-100 flex items-center justify-center rounded mb-4 relative overflow-hidden text-gray-400 font-sans text-sm">
               <img src="/fig1 produksjonsgeografi.png" alt="Produksjonsgeografi" className="object-contain w-full h-full opacity-80" />
               <span className="absolute inset-0 flex items-center justify-center font-semibold tracking-widest bg-white/20">FIGURE 1: Produksjonsgeografi</span>
            </div>
            <figcaption className="text-sm text-gray-600 font-sans border-l-2 border-black pl-4">
              <strong>Figure 1:</strong> Map detailing the primary regions of chair production in Norway, indicating clusters of manufacturing excellence.
            </figcaption>
          </figure>
        </section>

        {/* Section 2 */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold font-sans mb-6">2. Temporal Diversity and Material Evolution</h2>
          <p className="text-lg leading-relaxed text-gray-800 mb-8">
            Tracing the materials over time provides insight into both resource availability and design philosophies. The transition from heavy, carved wood (such as oak and birch) in the early periods to the introduction of laminated wood and steel in the mid-20th century marks a defining shift in Norwegian industrial design.
          </p>
          
          {/* Figure 6 Placeholder */}
          <figure className="my-10 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="aspect-video bg-gray-100 flex items-center justify-center rounded mb-4 relative overflow-hidden text-gray-400 font-sans text-sm">
               <img src="/fig6 mangfald.png" alt="Mangfald Timeline" className="object-contain w-full h-full opacity-80" />
               <span className="absolute inset-0 flex items-center justify-center font-semibold tracking-widest bg-white/20">FIGURE 6: Mangfald</span>
            </div>
            <figcaption className="text-sm text-gray-600 font-sans border-l-2 border-black pl-4">
              <strong>Figure 6:</strong> Timeline showing the density of various material combinations and stylistic diversity across decades.
            </figcaption>
          </figure>
        </section>

        {/* Conclusion */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold font-sans mb-6">3. Conclusion</h2>
          <p className="text-lg leading-relaxed text-gray-800 mb-8">
            The dataset curated from the Nasjonalmuseet offers a rich tapestry of Norwegian design history. The 121 analyzed pieces serve not merely as functional objects, but as historical records documenting the interplay between geography, material science, and artistic vision in Norway.
          </p>
        </section>

        {/* Footer / Citation */}
        <footer className="pt-8 border-t border-gray-200 text-sm font-sans text-gray-500">
          <p>This article serves as a companion to the interactive 3D database.</p>
          <p className="mt-2 text-xs">Dataset provided by Nasjonalmuseet for kunst, arkitektur og design.</p>
        </footer>
      </main>
    </div>
  )
}
