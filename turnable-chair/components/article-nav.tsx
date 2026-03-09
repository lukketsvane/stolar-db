"use client"

import { useRouter, usePathname } from "next/navigation"

export default function ArticleNav() {
  const router = useRouter()
  const pathname = usePathname()

  const navItems = [
    { label: "I. Material", path: "/article" },
    { label: "II. Form", path: "/article/form" },
    { label: "III. Klassifikasjon", path: "/article/form-klassifikasjon" },
    { label: "IV. FFF-rammeverk", path: "/article/fff-rammeverk" },
    { label: "V. Kappe", path: "/article/kappe" },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white/90 backdrop-blur-md border-b border-gray-100 z-50 px-8 py-6 flex flex-col md:flex-row justify-between items-center gap-4">
      <button
        onClick={() => router.push("/")}
        className="flex items-center text-[10px] font-mono font-black uppercase tracking-widest text-black hover:line-through transition-all"
      >
        &larr; Stol-database
      </button>
      <div className="flex overflow-x-auto w-full md:w-auto pb-2 md:pb-0 gap-4 md:gap-8 no-scrollbar scroll-smooth">
        {navItems.map((item) => (
          <button
            key={item.path}
            onClick={() => router.push(item.path)}
            className={`text-[10px] font-mono font-black tracking-[0.2em] uppercase whitespace-nowrap transition-all border-b-2 pb-1 ${
              pathname === item.path
                ? "text-black border-black"
                : "text-gray-300 border-transparent hover:text-black"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
