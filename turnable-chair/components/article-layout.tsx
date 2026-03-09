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
        <div className="max-w-screen-xl mx-auto pt-32 pb-16 px-6 md:px-12 lg:px-24">
          {header}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-screen-xl mx-auto px-6 py-12 md:py-16 lg:px-24">
        <div className="prose prose-neutral prose-lg lg:prose-xl max-w-none 
          prose-headings:font-sans prose-headings:font-black prose-headings:tracking-tighter prose-headings:uppercase prose-headings:italic
          prose-p:leading-relaxed prose-p:mb-8 prose-p:text-gray-800 prose-p:text-xl md:prose-p:text-2xl
          prose-li:leading-relaxed prose-li:mb-2 prose-li:text-lg md:prose-li:text-xl
          prose-blockquote:font-serif prose-blockquote:not-italic prose-blockquote:border-l-4 prose-blockquote:border-black prose-blockquote:pl-8 prose-blockquote:py-2 prose-blockquote:my-8 prose-blockquote:text-3xl prose-blockquote:text-black
          prose-table:font-mono prose-table:text-sm prose-thead:border-b-2 prose-thead:border-black
          space-y-8">
          {children}
        </div>
      </main>
    </div>
  )
}
