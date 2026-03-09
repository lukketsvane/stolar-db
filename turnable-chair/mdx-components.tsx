import type { MDXComponents } from 'mdx/types'
import React from 'react'

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    // Allows customizing built-in components, e.g. to add styling.
    h2: ({ children }) => <h2 className="text-2xl md:text-4xl font-sans font-black text-black mb-8 tracking-tighter uppercase italic">{children}</h2>,
    h3: ({ children }) => <h3 className="text-xl font-sans font-black text-black mb-4 uppercase">{children}</h3>,
    p: ({ children }) => <p className="text-base md:text-lg lg:text-xl leading-relaxed mb-8 text-gray-800">{children}</p>,
    ol: ({ children }) => <ol className="list-decimal pl-8 mb-8 space-y-2 text-base md:text-lg">{children}</ol>,
    ul: ({ children }) => <ul className="list-disc pl-8 mb-8 space-y-2 text-base md:text-lg">{children}</ul>,
    
    // Custom components
    Figure: ({ src, caption, width = "w-full" }: { src: string, caption: string, width?: string }) => (
      <section className="not-prose my-24">
        <figure className="space-y-6">
          <img src={src} alt={caption} className={`${width} h-auto mx-auto rounded-xl shadow-sm border border-gray-100`} />
          <figcaption className="text-sm text-gray-500 font-sans italic text-center max-w-2xl mx-auto">
            {caption}
          </figcaption>
        </figure>
      </section>
    ),
    
    ...components,
  }
}
