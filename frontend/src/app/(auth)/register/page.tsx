'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import PasswordInput from '@/components/ui/PasswordInput'
import { apiUrl } from '@/lib/config'

export default function RegisterPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (password !== confirm) {
      setError('As senhas não coincidem.')
      return
    }

    setLoading(true)

    try {
      const res = await fetch(apiUrl('/api/auth/register/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.error ?? 'Erro ao cadastrar.')
        return
      }

      // Salva o token e redireciona direto pro chat
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      router.push('/chat')
    } catch {
      setError('Erro ao conectar com o servidor.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='min-h-screen bg-zinc-900 flex items-center justify-center px-4'>
      <div className='w-full max-w-sm'>

        <div className='text-center mb-8'>
          <h1 className='text-2xl font-bold text-white'>Sampaio IA</h1>
          <p className='text-zinc-400 text-sm mt-1'>Crie sua conta</p>
        </div>

        <div className='bg-zinc-800 rounded-2xl p-6 shadow-xl'>
          <h2 className='text-white font-semibold text-lg mb-6'>Cadastro</h2>

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
                placeholder='escolha um usuário'
              />
            </div>

            <div>
              <label className='block text-sm text-zinc-400 mb-1'>Senha</label>
              <PasswordInput
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder='crie uma senha'
              />
            </div>

            <div>
              <label className='block text-sm text-zinc-400 mb-1'>Confirmar senha</label>
              <PasswordInput
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                placeholder='repita a senha'
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
              {loading ? 'Cadastrando...' : 'Cadastrar'}
            </button>
          </form>

          <p className='text-zinc-500 text-sm text-center mt-4'>
            Já tem conta?{' '}
            <Link href='/login' className='text-blue-400 hover:text-blue-300'>
              Entrar
            </Link>
          </p>
        </div>

      </div>
    </div>
  )
}