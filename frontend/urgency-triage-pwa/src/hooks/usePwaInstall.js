import { useEffect, useMemo, useState } from 'react'

const DISMISS_KEY = 'pwa_install_dismissed'

const isStandalone = () => {
  if (window.matchMedia('(display-mode: standalone)').matches) return true
  if (window.navigator.standalone) return true
  return false
}

export const usePwaInstall = () => {
  const [promptEvent, setPromptEvent] = useState(null)
  const [installed, setInstalled] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    setInstalled(isStandalone())
    setDismissed(localStorage.getItem(DISMISS_KEY) === 'true')

    const handleBeforeInstall = (event) => {
      event.preventDefault()
      setPromptEvent(event)
    }

    const handleInstalled = () => {
      setInstalled(true)
      setPromptEvent(null)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall)
    window.addEventListener('appinstalled', handleInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
      window.removeEventListener('appinstalled', handleInstalled)
    }
  }, [])

  const canInstall = useMemo(() => {
    return Boolean(promptEvent) && !installed && !dismissed
  }, [promptEvent, installed, dismissed])

  const promptInstall = async () => {
    if (!promptEvent) return { outcome: 'dismissed' }
    promptEvent.prompt()
    const choice = await promptEvent.userChoice
    setPromptEvent(null)
    return choice
  }

  const dismissInstall = () => {
    localStorage.setItem(DISMISS_KEY, 'true')
    setDismissed(true)
  }

  return {
    canInstall,
    installed,
    dismissed,
    promptInstall,
    dismissInstall,
  }
}
