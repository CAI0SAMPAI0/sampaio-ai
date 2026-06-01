'use client'

import { useState, useEffect } from 'react'

export default function Lightbox() {
  const [data, setData] = useState<{ src: string; alt: string } | null>(null)

  useEffect(() => {
    const handleOpen = (e: Event) => {
      const customEvent = e as CustomEvent<{ src: string; alt: string }>
      setData(customEvent.detail)
    }
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setData(null)
      }
    }

    window.addEventListener('open-lightbox', handleOpen)
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('open-lightbox', handleOpen)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  if (!data) return null

  return (
    <div
      className='fixed inset-0 bg-black/85 backdrop-blur-md z-[100] flex items-center justify-center p-4 transition-all duration-300 animate-fade-in'
      onClick={() => setData(null)}
    >
      <button
        onClick={() => setData(null)}
        className='absolute top-4 right-4 text-zinc-300 hover:text-white bg-zinc-800/40 hover:bg-zinc-800/80 p-2.5 rounded-full transition-all text-lg cursor-pointer shadow-lg border border-zinc-700/30'
        title='Fechar visualizador'
      >
        ✕
      </button>
      <div
        className='relative max-w-5xl max-h-[85vh] overflow-hidden rounded-2xl border border-zinc-800/60 shadow-2xl scale-95 transition-transform duration-200 cursor-default'
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={data.src}
          alt={data.alt}
          className='w-full h-full object-contain max-h-[80vh] rounded-xl select-none'
        />
        {data.alt && (
          <div className='absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 text-white text-center text-xs font-semibold select-none'>
            {data.alt}
          </div>
        )}
      </div>
    </div>
  )
}
