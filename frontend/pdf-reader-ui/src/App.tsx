import React from 'react'
import axios from 'axios'
import UploadPdfButton from './components/UploadPdfButton'
import GenerateAudioButton from './components/GenerateAudioButton'
import RecommendationsSidebar, { type Recommendation } from './components/RecommendationsSidebar'
import FilePicker from './components/FilePicker'

type InsightsData = {
  summary?: string
  insights: string[]
  facts: string[]
  contradictions: string[]
  citations?: { filename?: string; page_number?: number; snippet?: string }[]
}

export default function App() {
  const [availableFiles, setAvailableFiles] = React.useState<string[]>([])
  const [currentFile, setCurrentFile] = React.useState<string | null>(null)
  const [recs, setRecs] = React.useState<Recommendation[]>([])
  const viewerApiRef = React.useRef<any>(null)
  const pendingPageRef = React.useRef<number | null>(null)
  const [adobeClientId, setAdobeClientId] = React.useState<string>('')
  const [lastSelection, setLastSelection] = React.useState<string>('')
  const [lastPage, setLastPage] = React.useState<number | null>(null)
  const [showInsights, setShowInsights] = React.useState(false)
  const [insightsData, setInsightsData] = React.useState<InsightsData | null>(null)
  const [insightsLoading, setInsightsLoading] = React.useState(false)
  const [insightsError, setInsightsError] = React.useState<string | null>(null)

  const onUploaded = (filenames: string[]) => {
    const next = Array.from(new Set([ ...availableFiles, ...filenames ]))
    setAvailableFiles(next)
    if (filenames.length > 0) setCurrentFile(filenames[0])
  }

  // Load public config (Adobe client ID) from backend once
  React.useEffect(() => {
    const api = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')
    axios.get(`${api}/config/public`).then((res) => {
      const cid = res.data?.adobeClientId?.toString?.() || ''
      if (cid) setAdobeClientId(cid)
    }).catch(() => {
      // ignore, fallback to VITE var
    })
  }, [])

  React.useEffect(() => {
    if (!currentFile) return
    const adobeAny: any = (window as any)
    const render = () => {
  const clientId = adobeClientId || import.meta.env.VITE_ADOBE_CLIENT_ID || 'YOUR_ADOBE_CLIENT_ID'
      const view = new adobeAny.AdobeDC.View({ clientId, divId: 'adobe-dc-view' })
  const api = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')
  const url = `${api}/document_library/${encodeURIComponent(currentFile)}`
      const previewPromise = view.previewFile({
        content: { location: { url } },
        metaData: { fileName: currentFile },
      }, {})

      // Capture viewer APIs when ready
      previewPromise.then((apis: any) => {
        viewerApiRef.current = apis
        if (pendingPageRef.current) {
          apis.gotoLocation({ pageNumber: pendingPageRef.current })
          pendingPageRef.current = null
        }
      })

  // Listen for viewer events
      view.registerCallback(
        adobeAny.AdobeDC.View.Enum.CallbackType.EVENT_LISTENER,
        async (event: any) => {
          if (!currentFile) return
          if (event?.type === 'TEXT_COPY') {
            const text = event?.data?.text || event?.data?.copiedText || event?.data?.selectedText || ''
            if (text && text.trim().length > 0) {
      setLastSelection(text)
              try {
                const res = await axios.post(`${(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')}/recommendations`, { text, k: 5 })
                setRecs(res.data?.results ?? [])
              } catch (e) {
                console.error('Recommendations failed', e)
              }
            }
          } else if (event?.type === 'PAGE_VIEW') {
            const page = event?.data?.pageNumber || event?.pageNumber
            if (page) {
      setLastPage(page)
              try {
                const res = await axios.post(`${(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')}/recommendations`, { filename: currentFile, page_number: page, k: 5 })
                setRecs(res.data?.results ?? [])
              } catch (e) {
                console.error('Recommendations failed', e)
              }
            }
          }
        },
        { enablePDFAnalytics: true }
      )
    }
    if (adobeAny && adobeAny.AdobeDC) render()
    else document.addEventListener('adobe_dc_view_sdk.ready', render, { once: true })
  }, [currentFile, adobeClientId])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderBottom: '1px solid #e5e7eb', background: '#ffffff' }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>Connecting the Dots</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <FilePicker currentFile={currentFile} onChange={(f) => setCurrentFile(f)} />
          <GenerateAudioButton
            getContext={async () => {
              if (lastSelection && lastSelection.trim().length > 0) {
                return { text: lastSelection }
              }
              if (currentFile && lastPage) {
                return { filename: currentFile, page_number: lastPage }
              }
              if (currentFile) {
                return { filename: currentFile, page_number: 1 }
              }
              throw new Error('No context available')
            }}
          />
          <button
            onClick={async () => {
              setInsightsError(null)
              setInsightsData(null)
              setInsightsLoading(true)
              try {
                const payload: any = {}
                if (lastSelection && lastSelection.trim().length > 0) {
                  payload.text = lastSelection
                } else if (currentFile && lastPage) {
                  payload.filename = currentFile
                  payload.page_number = lastPage
                } else if (currentFile) {
                  payload.filename = currentFile
                  payload.page_number = 1
                } else {
                  throw new Error('No context available')
                }
                const res = await axios.post(`${(import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')}/insights`, { ...payload, k: 5 })
                setInsightsData(res.data as InsightsData)
              } catch (e: any) {
                console.error('Insights failed', e)
                setInsightsError(e?.response?.data?.detail || e?.message || 'Insights failed')
              } finally {
                setInsightsLoading(false)
                setShowInsights(true)
              }
            }}
            title="Get insights (from selection or current page)"
            style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #e5e7eb', background: '#fff', cursor: 'pointer' }}
          >
            💡 Insights
          </button>
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
        <RecommendationsSidebar
          items={recs}
          onClickItem={(item) => {
            if (item.filename && item.filename !== currentFile) {
              pendingPageRef.current = item.page_number ?? null
              setCurrentFile(item.filename)
              return
            }
            if (item.page_number && viewerApiRef.current?.gotoLocation) {
              viewerApiRef.current.gotoLocation({ pageNumber: item.page_number })
            }
          }}
        />
      </main>

      {/* Insights Modal */}
      {showInsights && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16
          }}
          onClick={() => setShowInsights(false)}
        >
          <div
            style={{ width: 'min(800px, 95vw)', maxHeight: '85vh', overflow: 'auto', background: '#fff', borderRadius: 10, border: '1px solid #e5e7eb', padding: 16 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h2 style={{ margin: 0, fontSize: 18 }}>Insights</h2>
              <button onClick={() => setShowInsights(false)} style={{ background: 'transparent', border: 'none', fontSize: 18, cursor: 'pointer' }}>✖</button>
            </div>

            {insightsLoading && <div>Analyzing…</div>}
            {insightsError && <div style={{ color: '#b91c1c' }}>Error: {insightsError}</div>}

            {insightsData && (
              <div style={{ display: 'grid', gap: 12 }}>
                {insightsData.summary && (
                  <section>
                    <h3 style={{ margin: '8px 0' }}>Summary</h3>
                    <p style={{ margin: 0 }}>{insightsData.summary}</p>
                  </section>
                )}
                <section>
                  <h3 style={{ margin: '8px 0' }}>Key insights</h3>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {insightsData.insights?.map((s, i) => <li key={`ins-${i}`}>{s}</li>)}
                  </ul>
                </section>
                <section>
                  <h3 style={{ margin: '8px 0' }}>Facts</h3>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {insightsData.facts?.map((s, i) => <li key={`fact-${i}`}>{s}</li>)}
                  </ul>
                </section>
                <section>
                  <h3 style={{ margin: '8px 0' }}>Contradictions</h3>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {insightsData.contradictions?.map((s, i) => <li key={`con-${i}`}>{s}</li>)}
                  </ul>
                </section>
                {insightsData.citations && insightsData.citations.length > 0 && (
                  <section>
                    <h3 style={{ margin: '8px 0' }}>Citations</h3>
                    <ul style={{ margin: 0, paddingLeft: 18 }}>
                      {insightsData.citations.map((c, i) => (
                        <li key={`cit-${i}`}>
                          <button
                            onClick={() => {
                              if (!c) return
                              if (c.filename && c.filename !== currentFile) {
                                pendingPageRef.current = c.page_number ?? null
                                setCurrentFile(c.filename)
                              } else if (c.page_number && viewerApiRef.current?.gotoLocation) {
                                viewerApiRef.current.gotoLocation({ pageNumber: c.page_number })
                              }
                            }}
                            style={{ background: 'transparent', border: 'none', color: '#2563eb', cursor: 'pointer', padding: 0 }}
                            title={`Open ${c.filename || ''} p.${c.page_number || ''}`}
                          >
                            {c.filename || 'document'} p.{c.page_number}
                          </button>
                          {c.snippet && <div style={{ color: '#6b7280', fontSize: 12, marginTop: 2 }}>{c.snippet}</div>}
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
