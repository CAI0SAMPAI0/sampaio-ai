'use client'

import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import Image from 'next/image'

export interface Message {
    role: 'user' | 'ai'
    content: string
}

interface Props {
    messages: Message[]
    isLoading: boolean
}

export default function ChatWindow({ messages, isLoading }: Props) {
    const bottomRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, isLoading])

    return (
        <div className='flex-1 overflow-y-auto px-4 py-6 space-y-6' ref={bottomRef}>
            {messages.length === 0 && (
                <div className='flex flex-col items-center justify-center h-full text-zinc-500 gap-2'>
                    {/* Aqui você coloca a foto da IA depois */}
                    <Image
                        src="/ai-avatar.png"
                        alt="Sampaio IA"
                        width={64}
                        height={64}
                        className="rounded-full"
                    />
                    <p className='text-sm'>Como posso ajudar você hoje?</p>
                </div>
            )}

            {messages.map((msg, index) => (
                <MessageBubble key={index} role={msg.role} content={msg.content} />
            ))}

            {isLoading && (
                <div className='flex items-start gap-3'>
                    <div className='w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm font-bold text-zinc-300'>
                        AI
                    </div>
                    <div className='bg-zinc-800 rounded-2xl rounded-tl-none px-4 py-3'>
                        <div className='flex gap-1 items-center h-4'>
                            <span className='w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:0ms]' />
                            <span className='w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:150ms]' />
                            <span className='w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:300ms]' />
                        </div>
                    </div>
                </div>
            )}

            <div ref={bottomRef} />
        </div>
    )
}