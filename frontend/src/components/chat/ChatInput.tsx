'use client'

import { useRef, useEffect, useState } from 'react'

interface Props {
  onSend: (message: string, files?: File[]) => void
  disabled: boolean
}

// Sub-component to safely handle Object URL generation & clean up to prevent memory leaks
function FilePreviewItem({ file, onRemove }: { file: File; onRemove: () => void }) {
  const [preview, setPreview] = useState<string | null>(null)

  useEffect(() => {
    if (!file.type.startsWith('image/')) return
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  return (
    <div className='relative group flex flex-col items-center justify-center bg-zinc-800/80 border border-zinc-700/60 rounded-xl p-1 w-16 h-16 shrink-0 shadow-md transition-all hover:scale-[1.02]'>
      {preview ? (
        <img src={preview} alt={file.name} className='w-full h-full object-cover rounded-lg select-none' />
      ) : (
        <div className='flex flex-col items-center justify-center w-full h-full text-zinc-400 select-none'>
          <span className='text-lg leading-none'>📄</span>
          <span className='text-[8px] font-bold tracking-wider text-zinc-400 mt-1 max-w-[50px] truncate uppercase'>
            {file.name.split('.').pop() || 'ARQ'}
          </span>
        </div>
      )}
      <button
        onClick={onRemove}
        className='absolute -top-1.5 -right-1.5 bg-red-600 hover:bg-red-500 text-white rounded-full w-4.5 h-4.5 flex items-center justify-center text-[9px] font-bold shadow-md border border-zinc-900 transition-transform hover:scale-110 cursor-pointer'
        title='Remover arquivo'
      >
        ✕
      </button>
    </div>
  )
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

  // Height auto-resize for textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 192) + 'px'
  }, [value])

  // Drag and drop hook integration
  useEffect(() => {
    const handleDroppedFiles = (e: Event) => {
      const customEvent = e as CustomEvent<File[]>
      const selected = customEvent.detail
      if (selected && selected.length > 0) {
        setFiles(prev => {
          const existing = new Set(prev.map(f => `${f.name}-${f.size}`))
          const newFiles = selected.filter(f => !existing.has(`${f.name}-${f.size}`))
          return [...prev, ...newFiles]
        })
      }
    }
    window.addEventListener('files-dropped', handleDroppedFiles)
    return () => window.removeEventListener('files-dropped', handleDroppedFiles)
  }, [])

  // Clipboard Paste support
  function handlePaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    // 1. Scan clipboard for files (Images, etc.)
    const items = e.clipboardData.items
    let hasFiles = false
    
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1 || items[i].kind === 'file') {
        const file = items[i].getAsFile()
        if (file) {
          e.preventDefault()
          hasFiles = true
          
          // Generate a custom placeholder name for copied clipboard images if needed
          let finalFile = file
          if (file.name === 'image.png') {
            const timestamp = new Date().getTime()
            const ext = file.type.split('/')[1] || 'png'
            finalFile = new File([file], `colado-${timestamp}.${ext}`, { type: file.type })
          }

          setFiles(prev => {
            const existing = new Set(prev.map(f => `${f.name}-${f.size}`))
            if (existing.has(`${finalFile.name}-${finalFile.size}`)) return prev
            return [...prev, finalFile]
          })
        }
      }
    }

    if (hasFiles) return

    // 2. Scan clipboard for standard code syntax and block-format it
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
      {/* File Previews Grid with Thumbnails */}
      {files.length > 0 && (
        <div className='flex flex-wrap gap-2.5 mb-3 max-w-3xl mx-auto overflow-x-auto py-1 max-h-24 scrollbar-thin'>
          {files.map((file, i) => (
            <FilePreviewItem
              key={`${file.name}-${i}`}
              file={file}
              onRemove={() => removeFile(i)}
            />
          ))}
        </div>
      )}

      <div className='flex items-end gap-2 max-w-3xl mx-auto'>
        <button
          onClick={() => fileRef.current?.click()}
          disabled={disabled}
          title='Anexar arquivo(s)'
          className={`shrink-0 w-11 h-11 flex items-center justify-center rounded-xl
                      border transition-all duration-200 disabled:opacity-40 cursor-pointer
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
          accept='.pdf,.py,.js,.ts,.tsx,.jsx,.java,.cpp,.c,.cs,.go,.rs,.rb,.php,.html,.css,.json,.csv,.txt,.md,.yaml,.yml,.xml,.sql,.png,.jpg,.jpeg,.gif,.webp'
          onChange={handleFileChange}
        />

        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          disabled={disabled}
          placeholder='No que posso ajudar? (Ctrl+V para colar imagens ou arraste arquivos aqui)'
          rows={1}
          className='flex-1 resize-none overflow-y-auto bg-zinc-800 text-zinc-100 text-sm
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
                     text-white rounded-xl transition-colors cursor-pointer'
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