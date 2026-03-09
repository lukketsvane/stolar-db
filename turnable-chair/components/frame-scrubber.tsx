"use client"

import type React from "react"
import { useEffect, useRef, useState, useCallback } from "react"

interface FrameScrubberProps {
  frames?: string[]
  fallback?: string
}

export default function FrameScrubber({ frames, fallback }: FrameScrubberProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  const [isDragging, setIsDragging] = useState(false)
  const [velocity, setVelocity] = useState(0)
  const [lastX, setLastX] = useState(0)
  const [lastTime, setLastTime] = useState(0)

  const [currentIndex, setCurrentIndex] = useState(0)
  const [isReady, setIsReady] = useState(false)

  const animationRef = useRef<number>(undefined)

  const totalSteps = frames && frames.length > 0 ? frames.length : 0

  // Preload images for instant feel
  useEffect(() => {
    if (frames && frames.length > 0) {
      let loadedCount = 0
      frames.forEach(f => {
        const img = new Image()
        img.src = f
        img.onload = () => {
          loadedCount++
          if (loadedCount === Math.min(frames.length, 5)) {
             setIsReady(true)
          }
        }
      })
      const timer = setTimeout(() => setIsReady(true), 500)
      return () => clearTimeout(timer)
    }
  }, [frames])

  const handleStart = useCallback((clientX: number) => {
    setIsDragging(true)
    setLastX(clientX)
    setLastTime(Date.now())
    setVelocity(0)
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
    }
  }, [])

  const updateIndex = useCallback((delta: number) => {
    if (totalSteps === 0) return
    setCurrentIndex(prev => {
      let next = prev + delta
      while (next < 0) next += totalSteps
      while (next >= totalSteps) next -= totalSteps
      return next
    })
  }, [totalSteps])

  const handleMove = useCallback(
    (clientX: number) => {
      if (!isDragging) return

      const deltaX = clientX - lastX
      const deltaTime = Date.now() - lastTime

      if (deltaTime > 0) {
        const newVelocity = deltaX / deltaTime
        setVelocity(newVelocity)
      }

      setLastX(clientX)
      setLastTime(Date.now())

      const container = containerRef.current
      if (container) {
        const stepChange = (deltaX / container.offsetWidth) * totalSteps * 1.5
        updateIndex(stepChange)
      }
    },
    [isDragging, lastX, lastTime, totalSteps, updateIndex],
  )

  const handleEnd = useCallback(() => {
    setIsDragging(false)

    const animate = () => {
      setVelocity((prev) => {
        const friction = 0.92
        const newVelocity = prev * friction

        if (Math.abs(newVelocity) < 0.05) {
          return 0
        }

        const container = containerRef.current
        if (container) {
          const stepChange = (newVelocity / container.offsetWidth) * totalSteps * 5
          updateIndex(stepChange)
        }

        animationRef.current = requestAnimationFrame(animate)
        return newVelocity
      })
    }

    if (Math.abs(velocity) > 0.05) {
      animate()
    }
  }, [velocity, totalSteps, updateIndex])

  // Wheel/Trackpad support
  const handleWheel = useCallback(
    (e: WheelEvent) => {
      e.preventDefault()
      const sensitivity = 0.1
      const stepChange = (e.deltaX + e.deltaY) * sensitivity
      updateIndex(stepChange)
    },
    [updateIndex],
  )

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    container.addEventListener("wheel", handleWheel, { passive: false })
    return () => container.removeEventListener("wheel", handleWheel)
  }, [handleWheel])

  useEffect(() => {
    if (!isDragging) return
    const onMouseMove = (e: MouseEvent) => handleMove(e.clientX)
    const onMouseUp = () => handleEnd()
    window.addEventListener("mousemove", onMouseMove)
    window.addEventListener("mouseup", onMouseUp)
    return () => {
      window.removeEventListener("mousemove", onMouseMove)
      window.removeEventListener("mouseup", onMouseUp)
    }
  }, [isDragging, handleMove, handleEnd])

  if (!frames || frames.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white">
        <img src={fallback} alt="Stol" className="w-full h-full object-contain" />
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="relative cursor-grab active:cursor-grabbing select-none w-full h-full flex items-center justify-center bg-white overflow-hidden"
      onMouseDown={(e) => { e.preventDefault(); handleStart(e.clientX); }}
      onTouchStart={(e) => handleStart(e.touches[0].clientX)}
      onTouchMove={(e) => handleMove(e.touches[0].clientX)}
      onTouchEnd={handleEnd}
    >
      <div className="w-full h-full relative">
        {frames.map((f, i) => (
          <img
            key={f}
            src={f}
            alt={`Frame ${i}`}
            className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-75 ${
              Math.floor(currentIndex) === i ? "opacity-100 z-10" : "opacity-0 z-0"
            }`}
            draggable={false}
          />
        ))}
      </div>

      {!isReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-white z-50">
          <div className="w-10 h-10 border-2 border-black/5 border-t-black rounded-full animate-spin" />
        </div>
      )}
    </div>
  )
}
