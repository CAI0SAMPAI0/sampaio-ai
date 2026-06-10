import { apiUrl } from './config'

function getToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

function authHeader(): Record<string, string> {
  const token = getToken()
  if (!token) return {}
  return { 'Authorization': `Bearer ${token}` }
}

async function refreshToken(): Promise<boolean> {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) return false

  try {
    const res = await fetch(apiUrl('/api/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) return false
    const data = await res.json()
    localStorage.setItem('access_token', data.access)
    return true
  } catch {
    return false
  }
}

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  console.log('fetchWithAuth', url)
  const headers = { ...authHeader(), ...(options.headers ?? {}) }
  let res = await fetch(url, { ...options, headers })
  console.log('status:', res.status, url)

  // Token expirado — tenta renovar
  if (res.status === 401) {
    const refreshed = await refreshToken()
    if (refreshed) {
      const retryHeaders = { ...authHeader(), ...(options.headers ?? {}) }
      res = await fetch(url, { ...options, headers: retryHeaders })
    } else {
      // Refresh também expirou — força logout
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
  }

  return res
}

export async function login(username: string, password: string) {
  console.log('Logging in', username)
  const res = await fetch(apiUrl('/api/auth/login/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) throw new Error('Credenciais inválidas')
  const data = await res.json()
  localStorage.setItem('access_token', data.access)
  localStorage.setItem('refresh_token', data.refresh)
  return data
}

export async function getConversations() {
  const res = await fetchWithAuth(apiUrl('/api/conversations'))
  if (!res.ok) throw new Error('Erro ao buscar conversas')
  return res.json()
}

export async function createConversation() {
  const res = await fetchWithAuth(apiUrl('/api/conversations'), { method: 'POST' })
  if (!res.ok) throw new Error('Erro ao criar conversa')
  return res.json()
}

export async function deleteConversation(id: number) {
  await fetchWithAuth(apiUrl(`/api/conversations/${id}/`), { method: 'DELETE' })
}

export async function getMessages(conversationId: number) {
  const res = await fetchWithAuth(apiUrl(`/api/conversations/${conversationId}/messages`))
  if (!res.ok) throw new Error('Erro ao buscar mensagens')
  return res.json()
}

export async function sendMessage(
  conversationId: number,
  message: string,
  files?: File[],
) {
  const formData = new FormData()
  formData.append('message', message)

  if (files && files.length > 0) {
    files.forEach(f => formData.append('files', f))
  }

  const res = await fetchWithAuth(
    apiUrl(`/api/conversations/${conversationId}/messages`),
    { method: 'POST', body: formData },
  )
  if (!res.ok) throw new Error('Erro ao enviar mensagem')
  return res.json()
}

export async function getProfile() {
  const res = await fetchWithAuth(apiUrl('/api/auth/me'))
  if (!res.ok) throw new Error('Erro ao buscar perfil')
  return res.json()
}

export async function updateProfile(data: FormData) {
  const res = await fetchWithAuth(apiUrl('/api/auth/me/update'), {
    method: 'PATCH',
    body: data,
  })
  if (!res.ok) throw new Error('Erro ao atualizar perfil')
  return res.json()
}

export async function changePassword(current: string, newPass: string) {
  const res = await fetchWithAuth(apiUrl('/api/auth/me/password'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_password: current, new_password: newPass }),
  })
  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.error ?? 'Erro ao alterar senha')
  }
  return res.json()
}