import React from 'react'
import axios from 'axios'

type Props = {
  onUploaded?: (filenames: string[]) => void
}

export default function UploadPdfButton({ onUploaded }: Props) {
  const inputRef = React.useRef<HTMLInputElement | null>(null)

  const onClick = () => inputRef.current?.click()

  const onChange: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    const form = new FormData()
    for (const f of Array.from(files)) form.append('files', f)
    try {
      const api = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')
      
      // Step 1: Upload files
      const res = await axios.post(`${api}/upload`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const filenames: string[] = res.data?.saved ?? []
      
      // Step 2: Process each file (add to vector store)
      for (const filename of filenames) {
        try {
          await axios.post(`${api}/process`, null, {
            params: { filename }
          })
        } catch (err) {
          console.warn(`Processing ${filename} failed:`, err)
        }
      }
      
      onUploaded?.(filenames)
    } catch (err) {
      console.error('Upload failed', err)
    } finally {
      // reset to allow re-selecting the same file
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <>
      <button
        onClick={onClick}
        style={{
          padding: '8px 14px',
          borderRadius: 8,
          border: '1px solid var(--border-color)',
          background: 'var(--text-primary)',
          color: 'var(--bg-primary)',
          cursor: 'pointer',
        }}
      >
        Upload PDF
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        multiple
        onChange={onChange}
        style={{ display: 'none' }}
      />
    </>
  )
}
