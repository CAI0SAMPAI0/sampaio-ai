'use client'

import { useRef, useEffect, useState } from 'react'

interface Props {
  onSend: (message: string, file?: File) => void
  disabled: boolean
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 192) + 'px'  // max-h-48 = 192px
  }, [value])

  function handleSubmit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed, file ?? undefined)
    setValue('')
    setFile(null)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className='border-t border-zinc-700 bg-zinc-900 px-4 py-3'>
      {/* Preview do arquivo */}
      {file && (
        <div className='flex items-center gap-2 mb-2 bg-zinc-800 rounded-xl px-3 py-2 max-w-3xl mx-auto'>
          <span className='text-xs text-zinc-300 truncate flex-1'>📎 {file.name}</span>
          <button onClick={() => setFile(null)} className='text-zinc-500 hover:text-red-400 text-xs'>✕</button>
        </div>
      )}

      <div className='flex items-end gap-2 max-w-3xl mx-auto'>
        {/* Botão anexar */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={disabled}
          title='Anexar arquivo'
          className={`shrink-0 w-11 h-11 flex items-center justify-center rounded-xl
                      border transition-all duration-200 disabled:opacity-40
                      ${file
              ? 'border-blue-500 bg-blue-500/10 text-blue-400'
              : 'border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-zinc-500 hover:text-white hover:bg-zinc-700'
            }`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
        </button>

        <input
          ref={fileRef}
          type='file'
          className='hidden'
          accept='.pdf,.py,.js,.ts,.tsx,.jsx,.java,.cpp,.c,.cs,.go,.rs,.rb,.php,.html,.css,.json,.csv,.txt,.md,.yaml,.yml,.xml,.sql'
          onChange={e => setFile(e.target.files?.[0] ?? null)}
        />

        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder='No que posso ajudar?'
          rows={1}
          className='flex-1 resize-none overflow-y-auto bg-zinc-800 text-white text-sm
                     placeholder-zinc-500 rounded-xl px-4 py-3
                     focus:outline-none focus:ring-2 focus:ring-blue-500
                     disabled:opacity-50 transition-all'
          style={{ maxHeight: '192px' }}
        />

        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className='shrink-0 w-11 h-11 flex items-center justify-center
                     bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                     text-white rounded-xl transition-colors'
          title='Enviar'
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" />
          </svg>
        </button>

      </div>

      <p className='text-center text-zinc-600 text-xs mt-2'>
        Shift+Enter para quebrar linha
      </p>
    </div>
  )
}