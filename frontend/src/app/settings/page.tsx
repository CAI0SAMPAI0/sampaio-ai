'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { getProfile, updateProfile, changePassword } from '@/lib/api'
import PasswordInput from '@/components/ui/PasswordInput'

export default function SettingsPage() {
  const router = useRouter()
  const fileRef = useRef<HTMLInputElement>(null)

  const [username, setUsername] = useState('')
  const [avatar, setAvatar] = useState<string | null>(null)
  const [previewFile, setPreviewFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')

  const [profileMsg, setProfileMsg] = useState('')
  const [pwMsg, setPwMsg] = useState('')
  const [loading, setLoading] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' || 'system'
    setTheme(savedTheme)
  }, [])

  function handleThemeChange(newTheme: 'light' | 'dark' | 'system') {
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    const isDark = newTheme === 'dark' || (newTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
    if (isDark) {
      document.documentElement.classList.add('dark')
      document.documentElement.style.colorScheme = 'dark'
    } else {
      document.documentElement.classList.remove('dark')
      document.documentElement.style.colorScheme = 'light'
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    getProfile().then(data => {
      setUsername(data.username)
      setAvatar(data.avatar)
    }).catch(() => {
    })
  }, [router])

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setPreviewFile(file)
    setPreviewUrl(URL.createObjectURL(file))
  }

  async function handleProfileSave() {
    setLoading(true)
    setProfileMsg('')
    try {
      const form = new FormData()
      form.append('username', username)
      if (previewFile) form.append('avatar', previewFile)
      const data = await updateProfile(form)
      setAvatar(data.avatar)
      setPreviewFile(null)
      setPreviewUrl(null)
      setProfileMsg('Perfil atualizado!')
    } catch (e: unknown) {
      setProfileMsg(e instanceof Error ? e.message : 'Erro ao salvar.')
    } finally {
      setLoading(false)
    }
  }

  async function handlePasswordSave() {
    setPwMsg('')
    if (newPw !== confirmPw) { setPwMsg('As senhas não coincidem.'); return }
    setLoading(true)
    try {
      await changePassword(currentPw, newPw)
      setPwMsg('Senha alterada com sucesso!')
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
    } catch (e: unknown) {
      setPwMsg(e instanceof Error ? e.message : 'Erro ao alterar senha.')
    } finally {
      setLoading(false)
    }
  }

  const displayAvatar = previewUrl ?? avatar ?? '/user-avatar.jpg'

  return (
    <div className='min-h-screen bg-zinc-900 text-zinc-100 px-4 py-10'>
      <div className='max-w-lg mx-auto space-y-8'>

        <div className='flex items-center gap-3'>
          <button onClick={() => router.push('/chat')}
            className='text-zinc-400 hover:text-white transition-colors'>
            ← Voltar
          </button>
          <h1 className='text-xl font-semibold'>Configurações</h1>
        </div>

        {/* Perfil */}
        <div className='bg-zinc-800 rounded-2xl p-6 space-y-5'>
          <h2 className='font-semibold text-lg'>Perfil</h2>

          {/* Avatar */}
          <div className='flex items-center gap-4'>
            <Image
              src={displayAvatar}
              alt='Avatar'
              width={72}
              height={72}
              className='rounded-full object-cover w-18 h-18'
            />
            <div>
              <button
                onClick={() => fileRef.current?.click()}
                className='bg-zinc-700 hover:bg-zinc-600 text-sm px-4 py-2 rounded-xl transition-colors'
              >
                Alterar foto
              </button>
              <p className='text-zinc-500 text-xs mt-1'>JPG ou PNG, máx 2MB</p>
            </div>
            <input
              ref={fileRef}
              type='file'
              accept='image/jpeg,image/png,image/webp'
              className='hidden'
              onChange={handleFileChange}
            />
          </div>

          {/* Username */}
          <div>
            <label className='text-sm text-zinc-400 block mb-1'>Nome de usuário</label>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              className='w-full bg-zinc-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
            />
          </div>

          {profileMsg && (
            <p className={`text-sm ${profileMsg.includes('!') ? 'text-green-400' : 'text-red-400'}`}>
              {profileMsg}
            </p>
          )}

          <button
            onClick={handleProfileSave}
            disabled={loading}
            className='w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium py-3 rounded-xl transition-colors'
          >
            Salvar perfil
          </button>
        </div>

        {/* Alterar senha */}
        <div className='bg-zinc-800 rounded-2xl p-6 space-y-4'>
          <h2 className='font-semibold text-lg'>Alterar senha</h2>

          <div>
            <label className='text-sm text-zinc-400 block mb-1'>Senha atual</label>
            <PasswordInput
              value={currentPw}
              onChange={e => setCurrentPw(e.target.value)}
              placeholder='Senha atual'
            />
          </div>

          <div>
            <label className='text-sm text-zinc-400 block mb-1'>Nova senha</label>
            <PasswordInput
              value={newPw}
              onChange={e => setNewPw(e.target.value)}
              placeholder='Nova senha'
            />
          </div>

          <div>
            <label className='text-sm text-zinc-400 block mb-1'>Confirmar nova senha</label>
            <PasswordInput
              value={confirmPw}
              onChange={e => setConfirmPw(e.target.value)}
              placeholder='Confirmar nova senha'
            />
          </div>

          {pwMsg && (
            <p className={`text-sm ${pwMsg.includes('!') ? 'text-green-400' : 'text-red-400'}`}>
              {pwMsg}
            </p>
          )}

          <button
            onClick={handlePasswordSave}
            disabled={loading}
            className='w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium py-3 rounded-xl transition-colors'
          >
            Alterar senha
          </button>
        </div>

        {/* Aparência (Tema) */}
        <div className='bg-zinc-800 rounded-2xl p-6 space-y-4 shadow-lg'>
          <h2 className='font-semibold text-lg'>Aparência</h2>
          <div>
            <label className='text-sm text-zinc-400 block mb-3'>Tema do aplicativo</label>
            <div className='grid grid-cols-3 gap-2.5'>
              {(['light', 'dark', 'system'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => handleThemeChange(t)}
                  className={`py-3 px-4 rounded-xl text-sm font-semibold border transition-all duration-200 cursor-pointer ${
                    theme === t
                      ? 'bg-blue-600 text-white border-blue-500 shadow-md transform scale-[1.02]'
                      : 'bg-zinc-700 text-zinc-300 border-zinc-600 hover:bg-zinc-600 hover:text-white'
                  }`}
                >
                  {t === 'light' ? 'Claro' : t === 'dark' ? 'Escuro' : 'Sistema'}
                </button>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}