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
}

export default function MessageBubble({ role, content, userAvatar }: Props) {
  const isUser = role === 'user'

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <Image
        src={isUser ? userAvatar : '/ai-avatar.png'}
        alt={isUser ? 'Você' : 'Sampaio IA'}
        width={32}
        height={32}
        className='rounded-full shrink-0'
      />

      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed
        ${isUser
          ? 'bg-blue-600 text-white rounded-tr-none'
          : 'bg-zinc-800 text-zinc-100 rounded-tl-none'
        }`}>
        {isUser ? (
          <p>{content}</p>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeHighlight]}
            components={{
              h1: ({ children }) => <h1 className='text-xl font-bold mt-4 mb-2'>{children}</h1>,
              h2: ({ children }) => <h2 className='text-lg font-bold mt-3 mb-2'>{children}</h2>,
              h3: ({ children }) => <h3 className='text-base font-bold mt-2 mb-1'>{children}</h3>,
              p: ({ children }) => <p className='mb-2 last:mb-0'>{children}</p>,
              ul: ({ children }) => <ul className='list-disc list-inside mb-2 space-y-1'>{children}</ul>,
              ol: ({ children }) => <ol className='list-decimal list-inside mb-2 space-y-1'>{children}</ol>,
              li: ({ children }) => <li className='ml-2'>{children}</li>,
              strong: ({ children }) => <strong className='font-bold text-white'>{children}</strong>,
              em: ({ children }) => <em className='italic'>{children}</em>,
              blockquote: ({ children }) => (
                <blockquote className='border-l-2 border-zinc-500 pl-3 my-2 text-zinc-400 italic'>
                  {children}
                </blockquote>
              ),
              code: ({ className, children, ...props }) => {
                const isInline = !className
                return isInline ? (
                  <code className='bg-zinc-700 text-blue-300 px-1.5 py-0.5 rounded text-xs font-mono'>
                    {children}
                  </code>
                ) : (
                  <code className={`${className} text-xs`} {...props}>
                    {children}
                  </code>
                )
              },
              pre: ({ children }) => (
                <pre className='bg-zinc-950 rounded-xl p-4 my-3 overflow-x-auto text-xs'>
                  {children}
                </pre>
              ),
              a: ({ href, children }) => (
                <a href={href} target='_blank' rel='noopener noreferrer'
                  className='text-blue-400 hover:text-blue-300 underline'>
                  {children}
                </a>
              ),
              table: ({ children }) => (
                <div className='overflow-x-auto my-3'>
                  <table className='w-full text-xs border-collapse'>{children}</table>
                </div>
              ),
              th: ({ children }) => (
                <th className='border border-zinc-600 bg-zinc-700 px-3 py-2 text-left font-semibold'>
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className='border border-zinc-600 px-3 py-2'>{children}</td>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  )
}