'use client'

import { useState, useEffect } from 'react'

export default function DragDropOverlay() {
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    let dragCounter = 0

    const handleDragEnter = (e: DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      dragCounter++
      setIsDragging(true)
    }

    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      dragCounter--
      if (dragCounter === 0) {
        setIsDragging(false)
      }
    }

    const handleDragOver = (e: DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
    }

    const handleDrop = (e: DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)
      dragCounter = 0

      const droppedFiles = Array.from(e.dataTransfer?.files ?? [])
      if (droppedFiles.length > 0) {
        const event = new CustomEvent('files-dropped', { detail: droppedFiles })
        window.dispatchEvent(event)
      }
    }

    window.addEventListener('dragenter', handleDragEnter)
    window.addEventListener('dragleave', handleDragLeave)
    window.addEventListener('dragover', handleDragOver)
    window.addEventListener('drop', handleDrop)

    return () => {
      window.removeEventListener('dragenter', handleDragEnter)
      window.removeEventListener('dragleave', handleDragLeave)
      window.removeEventListener('dragover', handleDragOver)
      window.removeEventListener('drop', handleDrop)
    }
  }, [])

  if (!isDragging) return null

  return (
    <div className='fixed inset-0 bg-black/60 backdrop-blur-md z-[90] flex flex-col items-center justify-center p-4 pointer-events-none transition-all duration-300 animate-fade-in'>
      <div className='flex flex-col items-center gap-4 bg-zinc-900/90 border-2 border-dashed border-blue-500/50 p-10 rounded-3xl shadow-2xl scale-95 transition-transform duration-200 pointer-events-none select-none max-w-sm'>
        <div className='w-16 h-16 bg-blue-600/10 text-blue-400 rounded-full flex items-center justify-center text-3xl animate-bounce'>
          📥
        </div>
        <h3 className='text-lg font-bold text-white text-center'>Solte seus arquivos aqui</h3>
        <p className='text-xs text-zinc-400 text-center leading-relaxed'>
          Solte imagens, códigos ou PDFs para anexá-los instantaneamente à conversa no Sampaio IA.
        </p>
      </div>
    </div>
  )
}
