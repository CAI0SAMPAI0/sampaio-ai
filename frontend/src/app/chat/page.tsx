'use client'

import { useState, useEffect, useCallback, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Image from 'next/image'
import ChatWindow, { Message } from '@/components/chat/ChatWindow'
import ChatInput from '@/components/chat/ChatInput'
import {
  getConversations, createConversation,
  deleteConversation, getMessages, sendMessage,
  getProfile
} from '@/lib/api'

interface Conversation {
  id: number
  title: string
  created_at: string
}

function ChatPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [ready, setReady] = useState(false)
  const [userAvatar, setUserAvatar] = useState<string>('/user-avatar.jpg')

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations()
      setConversations(data)
      return data
    } catch {
      router.push('/login')
      return []
    }
  }, [router])

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { router.push('/login'); return }

    getProfile().then(data => {
      if (data.avatar) setUserAvatar(data.avatar)
    }).catch(() => { })

    setSidebarOpen(window.innerWidth >= 768)
    setReady(true)

    const convIdFromUrl = searchParams.get('id')
    loadConversations().then(async (data) => {
      if (convIdFromUrl) {
        const id = parseInt(convIdFromUrl)
        const exists = data.find((c: Conversation) => c.id === id)
        if (exists) {
          setActiveId(id)
          const msgs = await getMessages(id)
          setMessages(msgs.flatMap((c: { message: string; response: string }) => [
            { role: 'user' as const, content: c.message },
            { role: 'ai' as const, content: c.response },
          ]))
        }
      }
    })
  }, [router, loadConversations, searchParams])

  useEffect(() => {
    function handleResize() {
      if (window.innerWidth >= 768) setSidebarOpen(true)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  function setActiveConversation(id: number) {
    setActiveId(id)
    router.replace(`/chat?id=${id}`, { scroll: false })
  }

  async function handleNewConversation() {
    const conv = await createConversation()
    setConversations(prev => [conv, ...prev])
    setActiveConversation(conv.id)
    setMessages([])
    if (window.innerWidth < 768) setSidebarOpen(false)
  }

  async function handleSelectConversation(id: number) {
    setActiveConversation(id)
    setMessages([])
    const data = await getMessages(id)
    setMessages(data.flatMap((c: { message: string; response: string }) => [
      { role: 'user' as const, content: c.message },
      { role: 'ai' as const, content: c.response },
    ]))
    if (window.innerWidth < 768) setSidebarOpen(false)
  }

  async function handleDeleteConversation(id: number) {
    await deleteConversation(id)
    setConversations(prev => prev.filter(c => c.id !== id))
    if (activeId === id) {
      setActiveId(null)
      setMessages([])
      router.replace('/chat', { scroll: false })
    }
  }

  async function handleSend(text: string, files?: File[]) {
    let convId = activeId

    if (!convId) {
      const conv = await createConversation()
      setConversations(prev => [conv, ...prev])
      setActiveConversation(conv.id)
      convId = conv.id
    }

    // Show user bubble immediately — include file names as context hint
    const fileNote =
      files && files.length > 0
        ? `\n\n📎 ${files.map(f => f.name).join(', ')}`
        : ''
    setMessages(prev => [...prev, { role: 'user', content: text + fileNote }])
    setIsLoading(true)

    try {
      // Single request — all files go in one FormData (api.ts handles the keys)
      const data = await sendMessage(convId!, text, files)

      if (data.conversation_title) {
        setConversations(prev =>
          prev.map(c => c.id === convId ? { ...c, title: data.conversation_title } : c)
        )
      }

      setMessages(prev => [...prev, { role: 'ai', content: data.response }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: 'Erro ao conectar com o servidor.',
      }])
    } finally {
      setIsLoading(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/login')
  }

  if (!ready) return null

  return (
    <div className='flex h-screen bg-zinc-900 text-white overflow-hidden'>
      {sidebarOpen && (
        <div
          className='fixed inset-0 bg-black/50 z-10 md:hidden'
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`
        fixed md:relative z-20 flex flex-col h-full
        bg-zinc-950 border-r border-zinc-800
        transition-all duration-300 ease-in-out
        ${sidebarOpen ? 'w-64 translate-x-0' : 'w-64 -translate-x-full md:w-0 md:translate-x-0 md:overflow-hidden'}
      `}>
        <div className='flex items-center gap-2 p-4 border-b border-zinc-800'>
          <Image src='/ai-avatar.png' alt='Sampaio IA' width={28} height={28} className='rounded-full' />
          <span className='font-semibold text-sm flex-1'>Sampaio IA</span>
          <button onClick={() => setSidebarOpen(false)} className='text-zinc-500 hover:text-white md:hidden transition-colors'>✕</button>
        </div>

        <div className='p-3'>
          <button
            onClick={handleNewConversation}
            className='w-full flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700
                       text-sm text-zinc-300 rounded-xl px-3 py-2 transition-colors'
          >
            <span className='text-lg leading-none'>+</span> Nova conversa
          </button>
        </div>

        <div className='flex-1 overflow-y-auto px-2 space-y-1'>
          {conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => handleSelectConversation(conv.id)}
              className={`group flex items-center justify-between rounded-xl px-3 py-2 cursor-pointer
                text-sm transition-colors
                ${activeId === conv.id ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'}`}
            >
              <span className='truncate flex-1'>{conv.title}</span>
              <button
                onClick={e => { e.stopPropagation(); handleDeleteConversation(conv.id) }}
                className='opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 ml-2 transition-opacity text-xs'
              >✕</button>
            </div>
          ))}
        </div>

        <button
          onClick={() => router.push('/settings')}
          className='w-full flex items-center gap-2 text-left text-sm text-zinc-400 hover:text-white
             px-3 py-2 rounded-xl hover:bg-zinc-800 transition-colors'
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          Configurações
        </button>

        <div className='p-3 border-t border-zinc-800'>
          <button
            onClick={handleLogout}
            className='w-full flex items-center gap-2 text-left text-sm text-red-400 hover:text-red-300
                       px-3 py-2 rounded-xl hover:bg-zinc-800 transition-colors'
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" x2="9" y1="12" y2="12" />
            </svg>
            Sair
          </button>
        </div>
      </aside>

      <div className='flex flex-col flex-1 min-w-0 min-h-0'>
        <header className='flex items-center gap-3 px-4 py-4 border-b border-zinc-800 shrink-0'>
          <button
            onClick={() => setSidebarOpen(prev => !prev)}
            className='text-zinc-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-zinc-800'
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="4" x2="20" y1="12" y2="12" />
              <line x1="4" x2="20" y1="6" y2="6" />
              <line x1="4" x2="20" y1="18" y2="18" />
            </svg>
          </button>
          <span className='text-sm text-zinc-400 truncate'>
            {activeId ? conversations.find(c => c.id === activeId)?.title ?? 'Conversa' : 'Nova conversa'}
          </span>
        </header>

        <ChatWindow messages={messages} isLoading={isLoading} userAvatar={userAvatar} />
        <ChatInput onSend={handleSend} disabled={isLoading} />
      </div>
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatPageContent />
    </Suspense>
  )
}