'use client'

import { useEffect } from 'react'

export default function ThemeSync() {
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'system'
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    const applyTheme = () => {
      const currentTheme = localStorage.getItem('theme') || 'system'
      const isDark = currentTheme === 'dark' || (currentTheme === 'system' && mediaQuery.matches)
      if (isDark) {
        document.documentElement.classList.add('dark')
        document.documentElement.style.colorScheme = 'dark'
      } else {
        document.documentElement.classList.remove('dark')
        document.documentElement.style.colorScheme = 'light'
      }
    }

    applyTheme()

    const handleChange = () => {
      const currentTheme = localStorage.getItem('theme') || 'system'
      if (currentTheme === 'system') {
        applyTheme()
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return null
}
