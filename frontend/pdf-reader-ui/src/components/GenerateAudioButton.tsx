import React from 'react'
import axios from 'axios'

type Props = {
  getContext: () => Promise<{ text?: string; filename?: string; page_number?: number }>
}

export default function GenerateAudioButton({ getContext }: Props) {
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const audioRef = React.useRef<HTMLAudioElement | null>(null)

  const onClick = async () => {
    setError(null)
    setLoading(true)
    try {
      const payload = await getContext()
      const api = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')
      const res = await axios.post(`${api}/generate-audio`, payload)
      const relUrl: string = res.data?.url
      if (!relUrl) throw new Error('No audio URL returned')
      const full = `${api}${relUrl}`
      if (audioRef.current) {
        audioRef.current.src = full
        await audioRef.current.play()
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to generate audio')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      <button
        onClick={onClick}
        disabled={loading}
        title="Generate and play narration"
        style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #e5e7eb', background: '#fff', cursor: 'pointer' }}
      >
        {loading ? 'Generating…' : '🎙️ Narrate'}
      </button>
      <audio ref={audioRef} controls style={{ display: 'none' }} />
      {error && <span style={{ color: '#b91c1c' }}>{error}</span>}
    </div>
  )
}
