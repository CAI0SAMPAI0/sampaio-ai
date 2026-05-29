'use client'

import { useRef, useEffect, useState } from 'react'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  // Cresce conforme o conteúdo
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  }, [value])

  function handleSubmit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    // Reseta altura
    if (ref.current) ref.current.style.height = 'auto'
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className='border-t border-zinc-700 bg-zinc-900 px-4 py-3'>
      <div className='flex items-end gap-2 max-w-3xl mx-auto'>
        <textarea
          ref={ref}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder='No que posso ajudar? (Enter para enviar, Shift+Enter para nova linha)'
          rows={1}
          className='flex-1 resize-none overflow-hidden bg-zinc-800 text-white text-sm
                     placeholder-zinc-500 rounded-xl px-4 py-3 max-h-48
                     focus:outline-none focus:ring-2 focus:ring-blue-500
                     disabled:opacity-50 transition-all'
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className='flex-shrink-0 bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                     text-white rounded-xl px-4 py-3 text-sm font-medium transition-colors'
        >
          Enviar
        </button>
      </div>
      <p className='text-center text-zinc-600 text-xs mt-2'>
        Shift+Enter para quebrar linha
      </p>
    </div>
  )
}