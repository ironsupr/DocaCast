import React from 'react'
import UploadPdfButton from './components/UploadPdfButton'

export default function App() {
  const [availableFiles, setAvailableFiles] = React.useState<string[]>([])
  const [currentFile, setCurrentFile] = React.useState<string | null>(null)

  const onUploaded = (filenames: string[]) => {
    const next = Array.from(new Set([ ...availableFiles, ...filenames ]))
    setAvailableFiles(next)
    if (filenames.length > 0) setCurrentFile(filenames[0])
  }

  React.useEffect(() => {
    if (!currentFile) return
    const adobeAny: any = (window as any)
    const render = () => {
      const clientId = '2cd8f285a4654589a25a246b4bfbeec6' // Replace with your actual key
      const view = new adobeAny.AdobeDC.View({ clientId, divId: 'adobe-dc-view' })
      const url = `http://127.0.0.1:8001/document_library/${encodeURIComponent(currentFile)}`
      view.previewFile({
        content: { location: { url } },
        metaData: { fileName: currentFile },
      }, {})
    }
    if (adobeAny && adobeAny.AdobeDC) render()
    else document.addEventListener('adobe_dc_view_sdk.ready', render, { once: true })
  }, [currentFile])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderBottom: '1px solid #e5e7eb', background: '#ffffff' }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>Connecting the Dots</h1>
        <div>
          <UploadPdfButton onUploaded={onUploaded} />
        </div>
      </header>

      {/* Main content area: left (PDF viewer) + right (recommendations) */}
      <main style={{ display: 'flex', flex: 1, minHeight: 0, background: '#fafafa' }}>
        {/* PDF Viewer Column */}
        <section style={{ flex: 1, padding: 16, minWidth: 0 }}>
          <div id="adobe-dc-view" style={{ width: '100%', height: '100%', minHeight: 400, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8 }} />
        </section>

        {/* Recommendations Sidebar */}
        <aside style={{ width: 360, padding: 16, borderLeft: '1px solid #e5e7eb', background: '#ffffff', overflow: 'auto' }}>
          <h2 style={{ marginTop: 0, fontSize: 16 }}>Recommendations</h2>
          <div style={{ marginBottom: 12 }}>
            <strong>Uploaded PDFs</strong>
            <ul style={{ paddingLeft: 18 }}>
              {availableFiles.length === 0 ? (
                <li>Upload a PDF to see recommendations.</li>
              ) : (
                availableFiles.map((name) => (
                  <li key={name}>
                    <a href="#" onClick={(e) => { e.preventDefault(); setCurrentFile(name) }}>{name}</a>
                  </li>
                ))
              )}
            </ul>
          </div>
        </aside>
      </main>
    </div>
  )
}
