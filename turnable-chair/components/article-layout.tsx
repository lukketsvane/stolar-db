"use client"

import React from "react"
import ArticleNav from "./article-nav"

interface ArticleLayoutProps {
  children: React.ReactNode
  header: React.ReactNode
}

export default function ArticleLayout({ children, header }: ArticleLayoutProps) {
  return (
    <div className="min-h-screen bg-[#fafafa] text-gray-900 font-serif selection:bg-black selection:text-white pb-40 overflow-x-hidden">
      <ArticleNav />

      {/* Hero Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-screen-xl mx-auto pt-48 pb-32 px-6 md:px-12 lg:px-24">
          {header}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-prose mx-auto px-6 py-24 md:py-32">
        <div className="prose prose-neutral prose-lg lg:prose-xl max-w-none 
          prose-headings:font-sans prose-headings:font-black prose-headings:tracking-tighter prose-headings:uppercase prose-headings:italic
          prose-p:leading-relaxed prose-p:mb-12 prose-p:text-gray-800
          prose-li:leading-relaxed prose-li:mb-4
          prose-blockquote:font-sans prose-blockquote:not-italic prose-blockquote:font-bold prose-blockquote:text-3xl prose-blockquote:tracking-tight prose-blockquote:leading-tight
          prose-table:font-mono prose-table:text-sm prose-thead:border-b-2 prose-thead:border-black
          space-y-12">
          {children}
        </div>
      </main>
    </div>
  )
}
