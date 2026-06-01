'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import rehypeRaw from 'rehype-raw'
import remarkGfm from 'remark-gfm'
import 'highlight.js/styles/github-dark.css'
import Image from 'next/image'

interface Props {
  role: 'user' | 'ai'
  content: string
  userAvatar: string
  onResend?: (text: string) => void
}

function MarkdownContent({ content, isUser }: { content: string; isUser: boolean }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw, rehypeHighlight]}
      components={{
        h1: ({ children }) => <h1 className='text-xl font-bold mt-4 mb-2'>{children}</h1>,
        h2: ({ children }) => <h2 className='text-lg font-bold mt-3 mb-2'>{children}</h2>,
        h3: ({ children }) => <h3 className='text-base font-bold mt-2 mb-1'>{children}</h3>,
        p: ({ children }) => <p className='mb-2 last:mb-0 whitespace-pre-wrap'>{children}</p>,
        ul: ({ children }) => <ul className='list-disc list-inside mb-2 space-y-1'>{children}</ul>,
        ol: ({ children }) => <ol className='list-decimal list-inside mb-2 space-y-1'>{children}</ol>,
        li: ({ children }) => <li className='ml-2'>{children}</li>,
        strong: ({ children }) => <strong className='font-bold text-white'>{children}</strong>,
        em: ({ children }) => <em className='italic'>{children}</em>,
        blockquote: ({ children }) => (
          <blockquote className={`border-l-2 pl-3 my-2 italic ${isUser ? 'border-blue-300 text-blue-100' : 'border-zinc-500 text-zinc-400'}`}>
            {children}
          </blockquote>
        ),
        code: ({ className, children, ...props }) => {
          const isInline = !className
          return isInline ? (
            <code className={`px-1.5 py-0.5 rounded text-xs font-mono ${isUser ? 'bg-blue-700/60 text-blue-100' : 'bg-zinc-700 text-blue-300'}`}>
              {children}
            </code>
          ) : (
            <code className={`${className} text-xs`} {...props}>{children}</code>
          )
        },
        pre: ({ children }) => (
          <pre className='bg-zinc-950 rounded-xl p-4 my-3 overflow-x-auto text-xs'
            style={{ maxWidth: '100%', wordBreak: 'break-all' }}>
            {children}
          </pre>
        ),
        a: ({ href, children }) => (
          <a href={href} target='_blank' rel='noopener noreferrer'
            className={`underline ${isUser ? 'text-blue-200 hover:text-white' : 'text-blue-400 hover:text-blue-300'}`}>
            {children}
          </a>
        ),
        table: ({ children }) => (
          <div className='overflow-x-auto my-3'>
            <table className='w-full text-xs border-collapse'>{children}</table>
          </div>
        ),
        th: ({ children }) => (
          <th className='border border-zinc-600 bg-zinc-700 px-3 py-2 text-left font-semibold'>{children}</th>
        ),
        td: ({ children }) => (
          <td className='border border-zinc-600 px-3 py-2'>{children}</td>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

export default function MessageBubble({ role, content, userAvatar, onResend }: Props) {
  const isUser = role === 'user'
  const hasCodeBlock = content.includes('```')
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(content)
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  function handleResend() {
    onResend?.(content)
  }

  function handleEditSubmit() {
    if (editValue.trim()) {
      onResend?.(editValue.trim())
    }
    setEditing(false)
  }

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <Image
        src={isUser ? userAvatar : '/ai-avatar.png'}
        alt={isUser ? 'Você' : 'Sampaio IA'}
        width={32} height={32}
        className='rounded-full shrink-0 mt-1'
      />

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} gap-1 min-w-0 overflow-hidden`}>
        {/* Bubble ou editor */}
        {editing ? (
          <div className='flex flex-col gap-2 w-full max-w-sm'>
            <textarea
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleEditSubmit() }
                if (e.key === 'Escape') setEditing(false)
              }}
              autoFocus
              rows={3}
              className='w-full bg-zinc-800 text-white text-sm rounded-xl px-4 py-3
                         border border-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none'
            />
            <div className='flex gap-2 justify-end'>
              <button
                onClick={() => setEditing(false)}
                className='text-xs text-zinc-400 hover:text-white px-3 py-1.5
                           border border-zinc-700 rounded-lg transition-colors'
              >
                Cancelar
              </button>
              <button
                onClick={handleEditSubmit}
                className='text-xs text-white bg-blue-600 hover:bg-blue-500
                           px-3 py-1.5 rounded-lg transition-colors'
              >
                Enviar
              </button>
            </div>
          </div>
        ) : (
          <div className={`
            rounded-2xl px-4 py-3 text-sm leading-relaxed
            min-w-0 overflow-hidden
            ${hasCodeBlock ? 'max-w-[90%] w-full' : 'max-w-[75%]'}
            ${isUser ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-zinc-800 text-zinc-100 rounded-tl-none'}
          `}>
            <MarkdownContent content={content} isUser={isUser} />
          </div>
        )}

        {/* Botões de ação */}
        {!editing && (
          <div className='flex gap-1'>
            <button
              onClick={handleCopy}
              className='flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300
                         px-2 py-1 rounded-lg hover:bg-zinc-800 transition-colors'
              title='Copiar'
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
                <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
              </svg>
              {copied ? 'Copiado!' : 'Copiar'}
            </button>
            
            {isUser && (
              <>
                <button
                  onClick={() => { setEditValue(content); setEditing(true) }}
                  className='flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300
                             px-2 py-1 rounded-lg hover:bg-zinc-800 transition-colors'
                  title='Editar e reenviar'
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                  Editar
                </button>
                <button
                  onClick={handleResend}
                  className='flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300
                             px-2 py-1 rounded-lg hover:bg-zinc-800 transition-colors'
                  title='Reenviar'
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
                    <path d="M21 3v5h-5" />
                  </svg>
                  Reenviar
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}