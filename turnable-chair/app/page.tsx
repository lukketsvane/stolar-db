"use client"

import type React from "react"

import { useState, useEffect, useCallback } from "react"
import { useRouter, useSearchParams } from "next/navigation"

function useOrientation() {
  const [isPortrait, setIsPortrait] = useState(false)

  useEffect(() => {
    const checkOrientation = () => {
      setIsPortrait(window.innerHeight > window.innerWidth)
    }

    checkOrientation()
    window.addEventListener("resize", checkOrientation)
    window.addEventListener("orientationchange", checkOrientation)

    return () => {
      window.removeEventListener("resize", checkOrientation)
      window.removeEventListener("orientationchange", checkOrientation)
    }
  }, [])

  return isPortrait
}

interface ChairItem {
  id: string
  symbol: string
  number: string
  name: string
  video: string
  thumbVideo: string
  thumb?: string
  source?: string
  text: string
  specs: string
  producer: string
  year: string
  materials: string
  techniques: string
  classification: string
  inventoryNr: string
  acquisition: string
  photo: string
  location: string
}

interface Translations {
  gallery: string
  info: string
  description: string
  specifications: string
  comingSoon: string
  [key: string]: string
}

const translations: { [key: string]: Translations } = {
  no: {
    gallery: "galleri",
    info: "info",
    description: "Beskrivelse",
    specifications: "SPESIFIKASJONER",
    comingSoon: "skildring kjem snart...",
  },
  en: {
    gallery: "gallery",
    info: "info",
    description: "Description",
    specifications: "SPECIFICATIONS",
    comingSoon: "description coming soon...",
  },
}

class Turntable {
  container: HTMLElement
  video: HTMLVideoElement
  isDragging = false
  startX = 0
  velocity = 0
  lastX = 0
  lastTime = 0
  animationFrameId: number | null = null
  friction: number
  ambientSpeed: number
  isAmbient: boolean
  targetTime: number
  velocityHistory: Array<{ velocity: number; time: number }> = []
  maxVelocityHistory = 5
  smoothingFactor = 0.15
  minVelocity = 0.001

  constructor(
    container: HTMLElement,
    video: HTMLVideoElement,
    options: { friction?: number; ambientSpeed?: number } = {},
  ) {
    this.container = container
    this.video = video
    this.friction = options.friction || 0.96
    this.ambientSpeed = options.ambientSpeed || 0
    this.isAmbient = !!options.ambientSpeed
    this.targetTime = 0

    this.video.addEventListener("ended", () => {
      this.video.currentTime = 0
      if (!this.isDragging && this.isAmbient) {
        this.video.play()
      }
    })

    this.bindEvents()
    if (this.isAmbient) this.startAmbientAnimation()
    this.animationFrameId = requestAnimationFrame(this.update.bind(this))
  }

  bindEvents() {
    this.container.style.userSelect = "none"
    ;(this.container.style as any).webkitUserSelect = "none"
    ;(this.container.style as any).MozUserSelect = "none"
    ;(this.container.style as any).msUserSelect = "none"
    ;(this.container.style as any).webkitTouchCallout = "none"
    ;(this.container.style as any).webkitTapHighlightColor = "transparent"

    this.container.addEventListener("selectstart", (e) => e.preventDefault())
    this.container.addEventListener("dragstart", (e) => e.preventDefault())
    this.container.addEventListener("contextmenu", (e) => e.preventDefault())

    this.container.addEventListener("mousedown", this.handleDragStart.bind(this))
    this.container.addEventListener("touchstart", this.handleDragStart.bind(this), { passive: false })
    document.addEventListener("mousemove", this.handleDragMove.bind(this))
    document.addEventListener("touchmove", this.handleDragMove.bind(this), { passive: false })
    document.addEventListener("mouseup", this.handleDragEnd.bind(this))
    document.addEventListener("touchend", this.handleDragEnd.bind(this))
  }

  handleDragStart(e: MouseEvent | TouchEvent) {
    if (!this.video.duration || !isFinite(this.video.duration) || this.video.duration === 0) return
    e.preventDefault()
    this.isDragging = true
    this.isAmbient = false
    this.startX = "touches" in e ? e.touches[0].pageX : e.pageX
    this.lastX = this.startX
    this.lastTime = performance.now()
    this.velocity = 0
    this.velocityHistory = []
    this.container.style.cursor = "grabbing"
    document.body.style.userSelect = "none"
    ;(document.body.style as any).webkitUserSelect = "none"
    ;(document.body.style as any).MozUserSelect = "none"
    ;(document.body.style as any).msUserSelect = "none"
    ;(document.body.style as any).webkitTouchCallout = "none"
    ;(document.body.style as any).webkitTapHighlightColor = "transparent"
  }

  handleDragMove(e: MouseEvent | TouchEvent) {
    if (!this.isDragging || !this.video.duration || !isFinite(this.video.duration)) return
    e.preventDefault()
    const currentTime = performance.now()
    const x = "touches" in e ? e.touches[0].pageX : e.pageX
    const delta = x - this.lastX
    const timeDelta = currentTime - this.lastTime
    if (timeDelta > 0) {
      const instantVelocity = (delta / timeDelta) * 16.67
      this.velocityHistory.push({ velocity: instantVelocity, time: currentTime })
      if (this.velocityHistory.length > this.maxVelocityHistory) this.velocityHistory.shift()
    }
    this.lastX = x
    this.lastTime = currentTime
    // Sensitivity adjustment for 4s duration to feel seamless
    this.targetTime += (delta / this.container.offsetWidth) * this.video.duration * 1.0
  }

  handleDragEnd() {
    if (!this.isDragging) return
    this.isDragging = false
    this.container.style.cursor = "grab"
    document.body.style.userSelect = ""
    ;(document.body.style as any).webkitUserSelect = ""
    ;(document.body.style as any).MozUserSelect = ""
    ;(document.body.style as any).msUserSelect = ""
    if (this.velocityHistory.length > 0) {
      const recentHistory = this.velocityHistory.slice(-3)
      const avgVelocity = recentHistory.reduce((s, it) => s + it.velocity, 0) / recentHistory.length
      this.velocity = avgVelocity * 3
    }
  }

  update() {
    if (!this.video.duration || !isFinite(this.video.duration) || this.video.duration === 0) {
      this.animationFrameId = requestAnimationFrame(this.update.bind(this))
      return
    }
    if (!this.isDragging) {
      if (Math.abs(this.velocity) > this.minVelocity) {
        this.targetTime += (this.velocity / this.container.offsetWidth) * this.video.duration
        this.velocity *= this.friction
      } else {
        this.velocity = 0
      }
    }
    if (!isFinite(this.targetTime)) this.targetTime = 0
    const smoothing = this.isDragging ? 0.3 : this.smoothingFactor
    let newTime = this.video.currentTime + (this.targetTime - this.video.currentTime) * smoothing
    if (!isFinite(newTime)) newTime = 0
    newTime = ((newTime % this.video.duration) + this.video.duration) % this.video.duration
    if (isFinite(newTime) && newTime >= 0 && newTime < this.video.duration) {
      this.video.currentTime = newTime
      this.targetTime = newTime
    }
    this.animationFrameId = requestAnimationFrame(this.update.bind(this))
  }
  startAmbientAnimation() {}
}

const formatName = (s: string) => {
  if (!s) return ""
  return s
    .split(/\s+/)
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1).toLowerCase() : w))
    .join(" ")
}

export default function Home() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isPortrait = useOrientation()

  const [currentView, setCurrentView] = useState<"gallery" | "detail">("gallery")
  const [currentItem, setCurrentItem] = useState<ChairItem | null>(null)
  const [detailTurntable, setDetailTurntable] = useState<Turntable | null>(null)

  const [language, setLanguage] = useState<"no" | "en">("no")
  const [galleryData, setGalleryData] = useState<ChairItem[]>([])

  const [isDraggingBack, setIsDraggingBack] = useState(false)
  const [dragStartPos, setDragStartPos] = useState({ x: 0, y: 0 })

  const copyCurrentUrl = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
    } catch (err) {
      console.error("Failed to copy URL:", err)
    }
  }, [])

  useEffect(() => {
    const savedLanguage = localStorage.getItem("chair-language") as "no" | "en" | null
    if (savedLanguage && (savedLanguage === "no" || savedLanguage === "en")) {
      setLanguage(savedLanguage)
    }
  }, [])

  const showHome = useCallback(() => {
    router.push("/")
  }, [router])

  const handleDragBackStart = useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      if (currentView !== "detail") return

      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY

      setIsDraggingBack(true)
      setDragStartPos({ x: clientX, y: clientY })
    },
    [currentView],
  )

  const handleDragBackMove = useCallback(
    (e: MouseEvent | TouchEvent) => {
      if (!isDraggingBack) return

      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY

      const deltaX = clientX - dragStartPos.x
      const deltaY = clientY - dragStartPos.y
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)

      if (distance > 50) {
        setIsDraggingBack(false)
        showHome()
      }
    },
    [isDraggingBack, dragStartPos, showHome],
  )

  const handleDragBackEnd = useCallback(() => {
    setIsDraggingBack(false)
  }, [])

  useEffect(() => {
    if (isDraggingBack) {
      document.addEventListener("mousemove", handleDragBackMove)
      document.addEventListener("touchmove", handleDragBackMove, { passive: false })
      document.addEventListener("mouseup", handleDragBackEnd)
      document.addEventListener("touchend", handleDragBackEnd)

      return () => {
        document.removeEventListener("mousemove", handleDragBackMove)
        document.removeEventListener("touchmove", handleDragBackMove)
        document.removeEventListener("mouseup", handleDragBackEnd)
        document.removeEventListener("touchend", handleDragBackEnd)
      }
    }
  }, [isDraggingBack, handleDragBackMove, handleDragBackEnd])

  const loadGalleryItems = useCallback(async () => {
    try {
      const res = await fetch("/data/chairs.json", { cache: "no-store" })
      const data: ChairItem[] = await res.json()
      setGalleryData(data)
    } catch (err) {
      console.error("Failed loading chairs gallery:", err)
      setGalleryData([])
    }
  }, [])

  useEffect(() => {
    loadGalleryItems()
  }, [loadGalleryItems])

  const showDetail = useCallback(
    (item: ChairItem) => {
      router.push(`/?item=${item.id}`)
    },
    [router],
  )

  const toggleLanguage = useCallback(() => {
    setLanguage((prev) => {
      const newLang = prev === "no" ? "en" : "no"
      localStorage.setItem("chair-language", newLang)
      return newLang
    })
  }, [])

  useEffect(() => {
    const itemId = searchParams.get("item")
    if (itemId) {
      const item = galleryData.find((d) => d.id === itemId)
      if (item) {
        setCurrentItem(item)
        setCurrentView("detail")
      }
    } else {
      setCurrentView("gallery")
      setCurrentItem(null)
    }
  }, [searchParams, galleryData])

  useEffect(() => {
    const handleKeydown = (e: KeyboardEvent) => {
      if (currentView !== "detail" || !currentItem) return
      const currentIndex = galleryData.findIndex((item) => item.id === currentItem.id)
      if (currentIndex === -1) return

      let nextIndex = -1
      if (e.key === "ArrowRight") nextIndex = (currentIndex + 1) % galleryData.length
      else if (e.key === "ArrowLeft") nextIndex = (currentIndex - 1 + galleryData.length) % galleryData.length
      else if (e.key === "Escape" || e.key === "ArrowUp" || e.key === "x" || e.key === "X") {
        router.push("/")
        return
      }

      if (nextIndex !== -1) {
        const nextItem = galleryData[nextIndex]
        router.push(`/?item=${nextItem.id}`)
      }
    }

    document.addEventListener("keydown", handleKeydown)
    return () => document.removeEventListener("keydown", handleKeydown)
  }, [currentView, currentItem, router, galleryData])

  useEffect(() => {
    if (currentView === "detail" && currentItem) {
      const detailVideo = document.getElementById("detail-video") as HTMLVideoElement
      const container = document.getElementById("turntable-container-detail")
      if (detailVideo && container) {
        if (detailTurntable?.animationFrameId) cancelAnimationFrame(detailTurntable.animationFrameId)
        setDetailTurntable(null)
        ;(container as any).dataset.turntableInit = ""

        if (detailVideo.src !== (currentItem.video || currentItem.thumb)) {
          detailVideo.src = currentItem.video || ""
          detailVideo.load()
        }

        const handleVideoReady = () => {
          setTimeout(() => {
            if (
              detailVideo.duration &&
              isFinite(detailVideo.duration) &&
              detailVideo.duration > 0 &&
              !(container as any).dataset.turntableInit
            ) {
              ;(container as any).dataset.turntableInit = "true"
              detailVideo.currentTime = 0
              const turntable = new Turntable(container as HTMLElement, detailVideo)
              setDetailTurntable(turntable)
            }
          }, 100)
        }

        detailVideo.addEventListener("loadeddata", handleVideoReady, { once: true })
        detailVideo.addEventListener("canplay", handleVideoReady, { once: true })
      }
    }
    return () => {
      if (detailTurntable?.animationFrameId) cancelAnimationFrame(detailTurntable.animationFrameId)
    }
  }, [currentView, currentItem])

  const renderGridElement = (item: ChairItem | null, position: number) => {
    if (!item) {
      return (
        <div
          key={`empty-${position}`}
          className="relative aspect-square border-black/10"
          style={{ borderWidth: "0.5px" }}
        />
      )
    }

    const handleVideoPlay = async (video: HTMLVideoElement) => {
      try {
        if (video && video.paused && document.contains(video)) {
          await video.play()
        }
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          console.warn("Video play error:", error)
        }
      }
    }

    const handleVideoPause = (video: HTMLVideoElement) => {
      try {
        if (video && !video.paused && document.contains(video)) {
          video.pause()
        }
      } catch (error) {}
    }

    return (
      <div
        key={item.id}
        className={`relative aspect-square border-black/50 cursor-pointer transition-opacity duration-200 bg-white opacity-100 hover:opacity-80`}
        style={{ borderWidth: "0.5px" }}
        onClick={() => showDetail(item)}
      >
        <div className="absolute top-1 left-1 text-black font-bold text-[10px] sm:text-xs z-10">{item.symbol}</div>
        <div className="absolute top-1 right-1 text-black font-bold text-[10px] sm:text-xs z-10">{item.number}</div>

        <div className="flex flex-col items-center justify-center h-full p-2">
          <div className="flex-1 flex items-center justify-center w-full max-w-full max-h-full overflow-hidden">
            {item.thumb ? (
              <img
                src={item.thumb}
                alt={item.name}
                className="max-w-full max-h-full object-contain w-full h-full"
              />
            ) : item.thumbVideo ? (
              <video
                src={item.thumbVideo}
                className="max-w-full max-h-full object-contain w-full h-full"
                muted
                loop
                playsInline
                onMouseEnter={(e) => handleVideoPlay(e.currentTarget)}
                onMouseLeave={(e) => handleVideoPause(e.currentTarget)}
              />
            ) : null}
          </div>
          <div className="text-black text-[9px] sm:text-xs text-center mt-1 font-medium truncate w-full px-1">
            {formatName(item.name)}
          </div>
        </div>
      </div>
    )
  }

  if (currentView === "detail" && currentItem) {
    return (
      <div className="min-h-screen bg-white text-black relative overflow-hidden">
        <div className="fixed top-8 left-8 z-40 pointer-events-none hidden md:block">
          <div className="text-black font-bold" style={{ fontFamily: "Helvetica Neue, Arial, sans-serif" }}>
            <div className="text-6xl lg:text-8xl leading-none">{currentItem.symbol}</div>
            <div className="text-3xl lg:text-4xl mt-2">{currentItem.number}</div>
            <div className="text-xl lg:text-2xl mt-1 max-w-xs">{formatName(currentItem.name)}</div>
          </div>
        </div>

        <button
          onClick={showHome}
          className="fixed top-4 left-4 z-50 w-10 h-10 bg-white/80 hover:bg-gray-100 border border-black/20 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-110 cursor-pointer shadow-sm"
          style={{ pointerEvents: "auto" }}
        >
          <svg className="w-5 h-5 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <button
          onClick={() => router.push('/article')}
          className="fixed top-4 right-4 z-40 px-4 py-2 bg-black/5 hover:bg-black/10 border border-black/20 rounded text-black text-sm transition-all duration-200"
        >
          Scientific Article
        </button>

        <button
          onClick={copyCurrentUrl}
          className="fixed top-4 right-20 z-40 w-10 h-10 hover:bg-black/5 rounded flex items-center justify-center transition-all duration-200 text-black"
          title="Copy URL"
        >
          <svg className="w-4 h-4 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
        </button>

        <div
          className="fixed top-0 left-0 w-32 h-32 z-40 cursor-grab active:cursor-grabbing"
          onMouseDown={handleDragBackStart}
          onTouchStart={handleDragBackStart}
          style={{ pointerEvents: "auto" }}
        />

        <div className="flex flex-col lg:flex-row h-screen">
          <div className="flex-1 relative bg-white">
            {currentItem.video ? (
              <div id="turntable-container-detail" className="w-full h-full flex items-center justify-center">
                <video id="detail-video" className="w-full h-full max-w-4xl max-h-[80vh] object-contain bg-transparent" muted playsInline />
              </div>
            ) : (
              <div className="w-full h-full flex items-center justify-center p-8">
                {currentItem.thumb ? (
                   <img src={currentItem.thumb} alt={currentItem.name} className="max-w-full max-h-[80vh] object-contain" />
                ) : (
                   <div className="text-gray-300">No image available</div>
                )}
              </div>
            )}
          </div>

          <div className="lg:w-96 bg-gray-50/90 border-l border-gray-200 p-8 flex flex-col justify-center overflow-y-auto">
            <div className="space-y-6">
              <div>
                <h1 className="text-3xl font-bold mb-2 text-black">{formatName(currentItem.name)}</h1>
                <div className="text-gray-600 text-sm font-medium">
                  {currentItem.symbol} {currentItem.number} {currentItem.year ? `— ${currentItem.year}` : ''}
                </div>
                {currentItem.producer && (
                  <div className="text-gray-800 font-medium mt-1">
                    {currentItem.producer}
                  </div>
                )}
              </div>

              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider mb-2 text-gray-500">{translations[language].description}</h2>
                <p className="text-gray-800 leading-relaxed text-sm whitespace-pre-wrap">{currentItem.text || translations[language].comingSoon}</p>
              </div>

              <div className="grid grid-cols-1 gap-y-4">
                 {currentItem.specs && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Mål</h2>
                      <p className="text-gray-900 text-sm font-mono">{currentItem.specs}</p>
                    </div>
                 )}
                 {currentItem.materials && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Materialer</h2>
                      <p className="text-gray-900 text-sm">{currentItem.materials}</p>
                    </div>
                 )}
                 {currentItem.techniques && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Teknikker</h2>
                      <p className="text-gray-900 text-sm">{currentItem.techniques}</p>
                    </div>
                 )}
                 {currentItem.location && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Produksjonssted</h2>
                      <p className="text-gray-900 text-sm">{currentItem.location}</p>
                    </div>
                 )}
                 {currentItem.inventoryNr && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Inventarnr</h2>
                      <p className="text-gray-900 text-sm font-mono">{currentItem.inventoryNr}</p>
                    </div>
                 )}
                 {currentItem.classification && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Klassifikasjon</h2>
                      <p className="text-gray-900 text-sm">{currentItem.classification}</p>
                    </div>
                 )}
                 {currentItem.acquisition && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Ervervelse</h2>
                      <p className="text-gray-800 text-xs italic">{currentItem.acquisition}</p>
                    </div>
                 )}
                 {currentItem.photo && (
                    <div>
                      <h2 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Foto</h2>
                      <p className="text-gray-700 text-xs">{currentItem.photo}</p>
                    </div>
                 )}
              </div>

              {currentItem.source && (
                <div className="pt-4 border-t border-gray-200">
                  <a href={currentItem.source} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 text-sm font-medium underline">
                    View in Nasjonalmuseet &rarr;
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const gridColumns = 9;
  const totalItems = galleryData.length;
  const targetGridSize = Math.ceil(totalItems / gridColumns) * gridColumns;
  const emptySlots = targetGridSize > totalItems ? targetGridSize - totalItems : 0;
  
  return (
    <div className="min-h-screen bg-white text-black font-sans selection:bg-black selection:text-white">
      {isPortrait && (
        <div className="fixed inset-0 bg-white/95 backdrop-blur-sm z-50 flex items-center justify-center p-8 text-black">
          <div className="text-center bg-gray-100 p-8 rounded-2xl shadow-lg border border-gray-200">
            <div className="text-4xl mb-4">📱</div>
            <p className="text-xl font-bold mb-2">Please rotate your device</p>
            <p className="text-sm text-gray-600">The grid is optimized for landscape orientation</p>
          </div>
        </div>
      )}

      <div className={`${isPortrait ? "hidden" : "block"}`}>
        <button
          onClick={() => router.push('/article')}
          className="fixed top-4 right-4 z-40 px-3 py-1 bg-black/5 hover:bg-black/10 border border-black/20 rounded text-sm font-medium transition-all duration-200"
        >
          Scientific Article
        </button>

        <div className="container mx-auto px-4" style={{ paddingTop: `calc(4rem + 8vh)`, paddingBottom: "6rem" }}>
          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-9 max-w-[1400px] mx-auto relative border-t border-l border-black/20 shadow-sm bg-gray-50/30">
            {galleryData.map((item, i) => renderGridElement(item, i))}
            {Array.from({ length: emptySlots }).map((_, i) => renderGridElement(null, totalItems + i))}

            <div className="absolute top-[-80px] left-0 z-30 flex items-center pointer-events-none">
              <h1
                className="text-4xl md:text-5xl lg:text-7xl font-bold text-black tracking-tight"
                style={{ fontFamily: "Helvetica Neue, Arial, sans-serif" }}
              >
                Nasjonalmuseet Chairs
              </h1>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
