const LOCAL_API_URL = 'http://localhost:8000'
const PRODUCTION_API_URL = 'https://sampaio-ai-production.up.railway.app'

function needsHttpProtocol(host: string) {
  return /^(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?($|\/)/.test(host)
}

export function normalizeApiUrl(url?: string) {
  const fallbackUrl = process.env.NODE_ENV === 'production' ? PRODUCTION_API_URL : LOCAL_API_URL
  let normalizedUrl = (url || fallbackUrl).trim()

  if (!normalizedUrl) {
    normalizedUrl = fallbackUrl
  }

  if (normalizedUrl.startsWith('//')) {
    normalizedUrl = `https:${normalizedUrl}`
  } else if (!/^https?:\/\//i.test(normalizedUrl)) {
    const protocol = needsHttpProtocol(normalizedUrl) ? 'http' : 'https'
    normalizedUrl = `${protocol}://${normalizedUrl}`
  }

  return normalizedUrl.replace(/\/+$/, '')
}

export const API_URL = normalizeApiUrl(process.env.NEXT_PUBLIC_API_URL)

export function apiUrl(path: string) {
  return `${API_URL}${path.startsWith('/') ? path : `/${path}`}`
}
