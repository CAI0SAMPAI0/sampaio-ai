'use client'

import React, { useEffect, useRef } from 'react'

interface Props {
    value: string
    onChange: (value: string) => void
    onSubmit: () => void
    placeholder?: string
}

export function AutoResizeTextarea({ value, onChange, onSubmit, placeholder }: Props) {
    const ref = useRef<HTMLTextAreaElement>(null)

    useEffect(() => {
        const el = ref.current
        if (!el) return

        el.style.height = 'auto' // reseta
        el.style.height = el.scrollHeight + 'px' // ajusta
    }, [value])

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            onSubmit()
        }
    }

    return (
        <textarea
            ref={ref}
            value={value}
            onChange={e => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            className='w-full resize-none overflow-hidden rounded-xl border border-zinc-700
                 bg-zinc-800 px-4 py-3 text-sm text-white placeholder-zinc-500
                 focus:outline-none focus:ring-2 focus:ring-blue-500
                 max-h-48 transition-all duration-100'
        />
    )
}