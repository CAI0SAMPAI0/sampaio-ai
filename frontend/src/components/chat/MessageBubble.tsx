import Image from 'next/image'

interface Props {
    role: 'user' | 'ai'
    content: string
}

export default function MessageBubble({ role, content }: Props) {
    const isUser = role === 'user'

    return (
        <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
            {/* Avatar */}
            <Image
                src="/ai-avatar.png"
                alt={isUser ? "Você" : "Sampaio IA"}
                width={36}
                height={36}
                className="rounded-full"
            />

            {/* Balão */}
            <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed
        ${isUser
                    ? 'bg-blue-600 text-white rounded-tr-none'
                    : 'bg-zinc-800 text-zinc-100 rounded-tl-none'
                }`}>
                {/* Renderiza HTML do markdown vindo do Django */}
                <div dangerouslySetInnerHTML={{ __html: content }} />
            </div>
        </div>
    )
}