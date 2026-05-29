'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { login } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      router.replace('/chat')
    } catch {
      setError('Credenciais inválidas. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='min-h-screen bg-zinc-900 flex items-center justify-center px-4'>
      <div className='w-full max-w-sm'>

        {/* Logo / título */}
        <div className='text-center mb-8'>
          <h1 className='text-2xl font-bold text-white'>Sampaio IA</h1>
          <p className='text-zinc-400 text-sm mt-1'>Assistente de programação</p>
        </div>

        {/* Card */}
        <div className='bg-zinc-800 rounded-2xl p-6 shadow-xl'>
          <h2 className='text-white font-semibold text-lg mb-6'>Entrar</h2>

          <form onSubmit={handleSubmit} className='space-y-4'>
            <div>
              <label className='block text-sm text-zinc-400 mb-1'>Usuário</label>
              <input
                type='text'
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                className='w-full bg-zinc-700 text-white text-sm rounded-xl px-4 py-3
                           placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500'
                placeholder='seu usuário'
              />
            </div>

            <div>
              <label className='block text-sm text-zinc-400 mb-1'>Senha</label>
              <input
                type='password'
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className='w-full bg-zinc-700 text-white text-sm rounded-xl px-4 py-3
                           placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500'
                placeholder='sua senha'
              />
            </div>

            {error && (
              <p className='text-red-400 text-sm'>{error}</p>
            )}

            <button
              type='submit'
              disabled={loading}
              className='w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50
                         text-white font-medium text-sm rounded-xl py-3 transition-colors'
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          <p className='text-zinc-500 text-sm text-center mt-4'>
            Não tem conta?{' '}
            <Link href='/register' className='text-blue-400 hover:text-blue-300'>
              Cadastre-se
            </Link>
          </p>
        </div>

      </div>
    </div>
  )
}