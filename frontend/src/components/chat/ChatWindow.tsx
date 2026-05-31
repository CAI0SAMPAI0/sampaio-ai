'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import MessageBubble from './MessageBubble'
import Image from 'next/image'

export interface Message {
    role: 'user' | 'ai'
    content: string
}

interface Props {
    messages: Message[]
    isLoading: boolean
    userAvatar: string
}

export default function ChatWindow({ messages, isLoading, userAvatar }: Props) {
    const containerRef = useRef<HTMLDivElement>(null)
    const bottomRef = useRef<HTMLDivElement>(null)
    const [showScrollBtn, setShowScrollBtn] = useState(false)
    const isAutoScrolling = useRef(false)

    const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
        isAutoScrolling.current = true
        bottomRef.current?.scrollIntoView({ behavior })
        setTimeout(() => { isAutoScrolling.current = false }, 500)
    }, [])

    const prevLengthRef = useRef(0)
    useEffect(() => {
        const container = containerRef.current
        if (!container) return

        const isNearBottom =
            container.scrollHeight - container.scrollTop - container.clientHeight < 120

        if (messages.length !== prevLengthRef.current) {
            // Conversation switched (length went down) → instant jump
            if (messages.length < prevLengthRef.current) {
                scrollToBottom('instant' as ScrollBehavior)
            } else if (isNearBottom) {
                // New message appended and user was near bottom → smooth follow
                scrollToBottom('smooth')
            }
            prevLengthRef.current = messages.length
        } else if (isLoading && isNearBottom) {
            // Loading indicator appeared
            scrollToBottom('smooth')
        }
    }, [messages, isLoading, scrollToBottom])

    useEffect(() => {
        scrollToBottom('instant' as ScrollBehavior)
        prevLengthRef.current = 0
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
        messages[0]?.content,
    ])

    const handleScroll = useCallback(() => {
        const container = containerRef.current
        if (!container) return
        const distanceFromBottom =
            container.scrollHeight - container.scrollTop - container.clientHeight
        setShowScrollBtn(distanceFromBottom > 200)
    }, [])

    useEffect(() => {
        const container = containerRef.current
        if (!container) return
        container.addEventListener('scroll', handleScroll, { passive: true })
        return () => container.removeEventListener('scroll', handleScroll)
    }, [handleScroll])

    return (
        <div className='relative flex-1 min-h-0'>
            <div
                ref={containerRef}
                className='h-full overflow-y-auto px-4 py-6 space-y-6'
            >
                {messages.length === 0 && (
                    <div className='flex flex-col items-center justify-center h-full text-zinc-500 gap-2'>
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
                    <MessageBubble
                        key={index}
                        role={msg.role}
                        content={msg.content}
                        userAvatar={userAvatar}
                    />
                ))}

                {isLoading && (
                    <div className='flex items-start gap-3'>
                        <Image
                            src='/ai-avatar.png'
                            alt='Sampaio IA'
                            width={32}
                            height={32}
                            className='rounded-full shrink-0'
                        />
                        <div className='bg-zinc-800 rounded-2xl rounded-tl-none px-4 py-3'>
                            <div className='flex gap-1 items-center h-4'>
                                <span className='w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:0ms]' />
                                <span className='w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:150ms]' />
                                <span className='w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:300ms]' />
                            </div>
                        </div>
                    </div>
                )}

                {/* Scroll anchor */}
                <div ref={bottomRef} />
            </div>

            {/* Scroll-to-bottom button */}
            {showScrollBtn && (
                <button
                    onClick={() => scrollToBottom('smooth')}
                    className='absolute bottom-4 left-1/2 -translate-x-1/2
                     flex items-center gap-1.5
                     bg-zinc-700 hover:bg-zinc-600 text-zinc-200 text-xs
                     px-3 py-1.5 rounded-full shadow-lg
                     border border-zinc-600
                     transition-all duration-200 z-10'
                    title='Ir para o final'
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
                        fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="m6 9 6 6 6-6" />
                    </svg>
                    Ir para o final
                </button>
            )}
        </div>
    )
}