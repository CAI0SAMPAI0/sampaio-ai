'use client'

import { useRef, useEffect, useState } from 'react'

interface Props {
  onSend: (message: string, files?: File[]) => void
  disabled: boolean
}


function detectCodeLanguage(text: string): string | null {
  const trimmed = text.trim()

  if (trimmed.startsWith('```')) return null

  const lines = trimmed.split('\n')

  if (lines.length === 1) {
    const single = trimmed
    const singleLineCode = /^(import |from |def |class |const |let |var |function |return |if |for |while |#include|<\?php|SELECT |UPDATE |INSERT |DELETE )/i.test(single)
    if (!singleLineCode) return null
  }

  const codeSignals = [
    /^\s*(def |class |import |from |async def |@\w+)/m,           // Python
    /^\s*(const |let |var |function |import |export |=>)/m,        // JS/TS
    /^\s*(public |private |protected |class |interface |enum )/m,  // Java/C#/TS
    /^\s*(#include|#define|int main|void |printf|std::)/m,         // C/C++
    /^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b/im,     // SQL
    /^\s*(<\?php|\$\w+\s*=)/m,                                     // PHP
    /^\s*(func |package |import \()/m,                             // Go
    /^\s*(fn |let mut|use std|impl |pub fn)/m,                     // Rust
    /[{};]\s*$/m,                                                   // block endings
    /^\s{2,}|\t/m,                                                  // consistent indentation
  ]

  const signalCount = codeSignals.filter(r => r.test(trimmed)).length

  // Need at least 2 signals for multi-line to avoid false positives
  if (lines.length > 1 && signalCount < 2) return null

  // Guess language
  if (/def |import |from |:\s*$|^\s*#/m.test(trimmed)) return 'python'
  if (/const |let |var |=>|\.tsx?|\.jsx?/m.test(trimmed)) return 'typescript'
  if (/public class|System\.out|void main/m.test(trimmed)) return 'java'
  if (/#include|int main|printf|std::/m.test(trimmed)) return 'cpp'
  if (/SELECT|INSERT|UPDATE|DELETE/im.test(trimmed)) return 'sql'
  if (/<\?php|\$\w+/m.test(trimmed)) return 'php'
  if (/func |package main|fmt\./m.test(trimmed)) return 'go'
  if (/fn |let mut|impl /m.test(trimmed)) return 'rust'

  return '' // generic code block, no language hint
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 192) + 'px'
  }, [value])

  function handlePaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const pasted = e.clipboardData.getData('text')
    if (!pasted) return

    const lang = detectCodeLanguage(pasted)
    if (lang === null) return // not code, let default paste happen

    e.preventDefault()

    const fence = `\`\`\`${lang}\n${pasted.trim()}\n\`\`\``

    // Insert at cursor position
    const el = textareaRef.current!
    const start = el.selectionStart ?? value.length
    const end = el.selectionEnd ?? value.length
    const before = value.slice(0, start)
    const after = value.slice(end)

    // Add a blank line before the fence if there's content before it
    const separator = before.length > 0 && !before.endsWith('\n\n') ? '\n\n' : ''
    const newValue = before + separator + fence + (after.length > 0 ? '\n\n' + after : '')

    setValue(newValue)

    // Move cursor to end of inserted block
    requestAnimationFrame(() => {
      const pos = (before + separator + fence).length
      el.setSelectionRange(pos, pos)
      el.focus()
    })
  }

  function handleSubmit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed, files.length > 0 ? files : undefined)
    setValue('')
    setFiles([])
    if (fileRef.current) fileRef.current.value = ''
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? [])
    if (selected.length === 0) return
    setFiles(prev => {
      const existing = new Set(prev.map(f => `${f.name}-${f.size}`))
      const newFiles = selected.filter(f => !existing.has(`${f.name}-${f.size}`))
      return [...prev, ...newFiles]
    })
    e.target.value = ''
  }

  function removeFile(index: number) {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className='border-t border-zinc-700 bg-zinc-900 px-4 py-3'>
      {files.length > 0 && (
        <div className='flex flex-wrap gap-2 mb-2 max-w-3xl mx-auto'>
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className='flex items-center gap-2 bg-zinc-800 rounded-xl px-3 py-1.5 max-w-[220px]'
            >
              <span className='text-xs'>📎</span>
              <span className='text-xs text-zinc-300 truncate flex-1'>{file.name}</span>
              <button
                onClick={() => removeFile(i)}
                className='text-zinc-500 hover:text-red-400 text-xs shrink-0 transition-colors'
                title='Remover arquivo'
              >✕</button>
            </div>
          ))}
        </div>
      )}

      <div className='flex items-end gap-2 max-w-3xl mx-auto'>
        <button
          onClick={() => fileRef.current?.click()}
          disabled={disabled}
          title='Anexar arquivo(s)'
          className={`shrink-0 w-11 h-11 flex items-center justify-center rounded-xl
                      border transition-all duration-200 disabled:opacity-40
                      ${files.length > 0
              ? 'border-blue-500 bg-blue-500/10 text-blue-400'
              : 'border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-zinc-500 hover:text-white hover:bg-zinc-700'
            }`}
        >
          {files.length > 0 ? (
            <span className='text-xs font-bold text-blue-400'>{files.length}</span>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          )}
        </button>

        <input
          ref={fileRef}
          type='file'
          multiple
          className='hidden'
          accept='.pdf,.py,.js,.ts,.tsx,.jsx,.java,.cpp,.c,.cs,.go,.rs,.rb,.php,.html,.css,.json,.csv,.txt,.md,.yaml,.yml,.xml,.sql'
          onChange={handleFileChange}
        />

        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
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
        Criado por Caio Sampaio
      </p>
    </div>
  )
}