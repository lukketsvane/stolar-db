"use client"

import { useRouter } from "next/navigation"
import ArticleLayout from "../../../components/article-layout"

export default function ArticleFivePage() {
  const router = useRouter()

  const header = (
    <div className="max-w-4xl">
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
          <p className="text-sm text-gray-500 mt-4 leading-relaxed max-w-xs">AHO</p>
        </div>
        <div>
          <p className="text-xs font-mono font-black uppercase tracking-widest text-gray-400 mb-6">Type</p>
          <p className="text-3xl font-black tracking-tight leading-none uppercase">PhD-kappe</p>
        </div>
      </div>

      <blockquote className="bg-gray-50 p-8 md:p-16 lg:p-20 rounded-2xl md:rounded-[3rem] border border-gray-100">
        <strong>Samandrag:</strong> I 130 år har estetiske fag operert under eit deterministisk aksiom: "form follows function". Denne kappa bind saman fire empiriske artiklar som til saman falsifiserer aksiomet og etablerer eit alternativ.
      </blockquote>
    </div>
  )

  return (
    <ArticleLayout header={header}>
      <section>
        <h2>1. Innleiing: Ein revolusjon i fire akter</h2>
        <p>
          Denne avhandlinga starta med eit enkelt eksperiment: å stille Sullivan sitt aksiom "form ever follows function" (1896) på prøve mot eit reelt datasett.
        </p>
      </section>

      <section>
        <h2>2. Det gamle paradigmet</h2>
        <h3>2.1 Sullivan, Le Corbusier og det deterministiske aksiomet</h3>
        <p>
          Louis Sullivan sin formulering frå 1896, "form ever follows function", var meint som ein poetisk observasjon av naturen. Men etterfylgjande generasjonar gjorde han til eit <em>aksiom</em>.
        </p>
      </section>

      <section>
        <h2>3. Det nye paradigmet: Form Follows Fitness</h2>
        <p>
          <em>Form Follows Fitness</em> (FFF) seier: Forma på eit objekt er ikkje dedusert frå funksjonen, men <strong>selektert</strong> av eit fleirdimensjonalt fitnesslandskap.
        </p>
      </section>

      <section>
        <h2>4. Konklusjon</h2>
        <p>
          461 stolar. 401 tredimensjonale modellar. 740 år med data. Fire artiklar. Éin konklusjon: <strong>Form follows fitness.</strong>
        </p>
      </section>

      <footer className="mt-32 pt-16 border-t border-gray-100 flex justify-between items-center text-[10px] font-mono font-black text-gray-200 uppercase tracking-[0.3em]">
        <p>&copy; 2026 Iver Raknes Finne</p>
        <p>AHO &bull; Arkitektur- og designhøgskolen i Oslo</p>
      </footer>
    </ArticleLayout>
  )
}
