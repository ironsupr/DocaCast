import React from 'react'
import SkyToggle from './ui/SkyToggle'

type Theme = 'light' | 'dark'

const STORAGE_KEY = 'docacast-theme'

function getSystemTheme(): Theme {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

function getInitialTheme(): Theme {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light' || stored === 'dark') {
      return stored
    }
  }
  return getSystemTheme()
}

export function useTheme() {
  const [theme, setThemeState] = React.useState<Theme>(getInitialTheme)

  const setTheme = React.useCallback((newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem(STORAGE_KEY, newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }, [])

  const toggleTheme = React.useCallback(() => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }, [theme, setTheme])

  // Apply theme on mount and listen for system changes
  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  // Listen for system theme changes (when no preference stored)
  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) {
        const systemTheme = mediaQuery.matches ? 'dark' : 'light'
        setThemeState(systemTheme)
        document.documentElement.setAttribute('data-theme', systemTheme)
      }
    }
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return { theme, setTheme, toggleTheme }
}

type Props = {
  theme: Theme
  onToggle: () => void
}

export default function ThemeToggle({ theme, onToggle }: Props) {
  return (
    <SkyToggle 
      checked={theme === 'dark'} 
      onChange={() => onToggle()} 
    />
  )
}
