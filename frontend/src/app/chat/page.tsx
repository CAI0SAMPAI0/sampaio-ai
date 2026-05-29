'use client'

import { useState } from 'react'
import ChatWindow, { Message } from '@/components/chat/ChatWindow'
import ChatInput from '@/components/chat/ChatInput'
import Image from 'next/image'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)

  async function handleSend(text: string) {
    // Adiciona mensagem do usuário
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setIsLoading(true)

    try {
      const res = await fetch('http://localhost:8000/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: text }),
      })

      const data = await res.json()

      setMessages(prev => [...prev, { role: 'ai', content: data.response }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: '<p class="text-red-400">Erro ao conectar com o servidor.</p>'
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className='flex flex-col h-screen bg-zinc-900 text-white'>
      {/* Header */}
      <header className='flex items-center gap-3 px-6 py-4 border-b border-zinc-700 bg-zinc-900'>
        {/* Foto da IA vem aqui depois */}
        <Image
          src="/ai-avatar.png"
          alt="PyIA"
          width={36}
          height={36}
          className="rounded-full"
        />
        <div>
          <h1 className='font-semibold text-sm'>Sampaio IA</h1>
          <p className='text-xs text-zinc-400'>Assistente de programação</p>
        </div>
      </header>

      {/* Mensagens */}
      <ChatWindow messages={messages} isLoading={isLoading} />

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}