"use client"

import React from "react"
import ArticleNav from "./article-nav"

interface ArticleLayoutProps {
  children: React.ReactNode
  header: React.ReactNode
}

export default function ArticleLayout({ children, header }: ArticleLayoutProps) {
  return (
    <div className="min-h-screen bg-white text-gray-900 font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      {/* Hero Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto pt-32 pb-16 px-6 md:px-12">
          {header}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12 md:py-16">
        <div className="prose prose-neutral prose-base md:prose-lg max-w-none 
          prose-headings:font-sans prose-headings:font-black prose-headings:tracking-tighter prose-headings:uppercase prose-headings:italic
          prose-p:leading-relaxed prose-p:mb-6 prose-p:text-gray-800
          prose-li:leading-relaxed prose-li:mb-2
          prose-blockquote:font-serif prose-blockquote:not-italic prose-blockquote:border-l-2 prose-blockquote:border-black prose-blockquote:pl-6 prose-blockquote:py-1 prose-blockquote:my-6 prose-blockquote:text-xl prose-blockquote:text-black
          prose-table:font-mono prose-table:text-xs prose-thead:border-b prose-thead:border-black
          space-y-6">
          {children}
        </div>
      </main>
    </div>
  )
}
