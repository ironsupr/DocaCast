import React from 'react'
import './PodcastStudio.css'

type Props = {
	meta: { url: string; parts?: string[]; chapters?: Array<{ index: number; speaker: string; text: string; start_ms?: number; end_ms?: number; part_url?: string }> }
}

export default function PodcastStudio({ meta }: Props) {
	const audioRef = React.useRef<HTMLAudioElement | null>(null)
	const api = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')
	const mergedSrc = meta.url.startsWith('http') ? meta.url : `${api}${meta.url}`

	const [currentSrc, setCurrentSrc] = React.useState<string>(mergedSrc)
	const [duration, setDuration] = React.useState<number>(0)
	const [currentTime, setCurrentTime] = React.useState<number>(0)
	const [playing, setPlaying] = React.useState<boolean>(false)
	const [activeChapter, setActiveChapter] = React.useState<number | null>(null)
	const [playbackRate, setPlaybackRate] = React.useState<number>(1)
	const [isPartMode, setIsPartMode] = React.useState<boolean>(false)
	const [errorMsg, setErrorMsg] = React.useState<string | null>(null)
	const [showTranscript, setShowTranscript] = React.useState<boolean>(true)
	const [transcriptMode, setTranscriptMode] = React.useState<'chapters' | 'fullText'>('chapters')
	const [volume, setVolume] = React.useState<number>(1)
	const [isMinimized, setIsMinimized] = React.useState<boolean>(false)
	const [showSubtitles, setShowSubtitles] = React.useState<boolean>(true)
	const [subtitleSize, setSubtitleSize] = React.useState<'small' | 'medium' | 'large'>('medium')
	const activeChapterRef = React.useRef<HTMLDivElement | null>(null)

	const chapters = Array.isArray(meta.chapters) ? meta.chapters : []

	// Get current subtitle text based on playback time
	const getCurrentSubtitle = () => {
		if (!chapters.length || isPartMode) return null
		const tms = currentTime * 1000
		for (let i = 0; i < chapters.length; i++) {
			const c = chapters[i]
			const start = typeof c.start_ms === 'number' ? c.start_ms : null
			const end = typeof c.end_ms === 'number' ? c.end_ms : null
			if (start !== null && end !== null && tms >= start && tms < end) {
				return { text: c.text, speaker: c.speaker || 'Unknown Speaker' }
			}
		}
		return null
	}

	const currentSubtitle = getCurrentSubtitle()

	// Generate full transcript text from chapters
	const generateFullTranscript = () => {
		if (!chapters.length) return 'No transcript available.'
		
		return chapters.map((c) => {
			const timestamp = typeof c.start_ms === 'number' ? 
				`${Math.floor(c.start_ms/1000/60)}:${String(Math.floor(c.start_ms/1000)%60).padStart(2,'0')}` : 
				'--:--'
			const speaker = (c.speaker || 'Unknown Speaker').toString().trim()
			return `[${timestamp}] ${speaker}: ${c.text}`
		}).join('\n\n')
	}

	const fmt = (sec: number) => {
		const s = Math.max(0, Math.floor(sec || 0))
		const m = Math.floor(s / 60)
		const r = s % 60
		return `${m}:${String(r).padStart(2, '0')}`
	}

	React.useEffect(() => {
		const el = audioRef.current
		if (!el) return
		const onLoaded = () => setDuration(el.duration || 0)
		const onTime = () => setCurrentTime(el.currentTime || 0)
		const onPlay = () => setPlaying(true)
		const onPause = () => setPlaying(false)
		const onError = () => {
			try {
				// Provide a helpful error and link to open directly
				const mediaErr = (el as any)?.error
				setErrorMsg(mediaErr ? `Audio error ${mediaErr.code || ''}` : 'Audio failed to load')
			} catch { setErrorMsg('Audio failed to load') }
		}
			const onEnded = () => {
				// If playing a part file, auto-advance to next chapter
				if (!chapters.length) return
				if (isPartMode && activeChapter != null) {
					const nextIdx = Math.min(chapters.length - 1, activeChapter + 1)
					if (nextIdx !== activeChapter) playChapter(chapters[nextIdx], nextIdx)
				}
			}
		el.addEventListener('loadedmetadata', onLoaded)
		el.addEventListener('timeupdate', onTime)
		el.addEventListener('play', onPlay)
		el.addEventListener('pause', onPause)
		el.addEventListener('error', onError)
			el.addEventListener('ended', onEnded)
		return () => {
			el.removeEventListener('loadedmetadata', onLoaded)
			el.removeEventListener('timeupdate', onTime)
			el.removeEventListener('play', onPlay)
			el.removeEventListener('pause', onPause)
			el.removeEventListener('error', onError)
				el.removeEventListener('ended', onEnded)
		}
	}, [])

		// Highlight active chapter based on current time (only when playing merged audio)
	React.useEffect(() => {
			if (!chapters.length || isPartMode) return
		const tms = currentTime * 1000
		let idx: number | null = null
		for (let i = 0; i < chapters.length; i++) {
			const c = chapters[i]
			const start = typeof c.start_ms === 'number' ? c.start_ms : null
			const end = typeof c.end_ms === 'number' ? c.end_ms : null
			if (start !== null && end !== null && tms >= start && tms < end) {
				idx = i
				break
			}
		}
		setActiveChapter(idx)
		}, [currentTime, chapters, isPartMode])

	// Auto-scroll to active chapter when in transcript mode
	React.useEffect(() => {
		if (showTranscript && transcriptMode === 'chapters' && activeChapter !== null && activeChapterRef.current) {
			activeChapterRef.current.scrollIntoView({
				behavior: 'smooth',
				block: 'center'
			})
		}
	}, [activeChapter, showTranscript, transcriptMode])

	const ensurePlay = () => {
		const el = audioRef.current
		if (!el) {
			console.error('Audio element not found')
			return
		}
		console.log('Attempting to play audio:', el.src)
		setTimeout(() => { 
			el.play().catch((error) => {
				console.error('Play failed:', error)
				setErrorMsg(`Playback failed: ${error.message}`)
			}) 
		}, 0)
	}

		const playPause = () => {
		const el = audioRef.current
		if (!el) {
			console.error('Audio element not found for playPause')
			return
		}
		console.log('Play/Pause clicked, current state:', el.paused ? 'paused' : 'playing')
		if (el.paused) {
			el.play().catch((error) => {
				console.error('Play failed in playPause:', error)
				setErrorMsg(`Playback failed: ${error.message}`)
			})
		} else {
			el.pause()
		}
	}

	const seek = (s: number) => {
		const el = audioRef.current
		if (!el) return
		el.currentTime = Math.max(0, Math.min(s, duration || s))
	}

	// When the mergedSrc changes (new generation), reset the player source cleanly
	React.useEffect(() => {
		setErrorMsg(null)
		setPlaying(false)
		setCurrentSrc(mergedSrc)
		const el = audioRef.current
		if (el) {
			try {
				el.pause()
				el.src = mergedSrc
				el.load()
			} catch {}
		}
	}, [mergedSrc])

		const playChapter = (c: any, idx?: number) => {
		const el = audioRef.current
		if (!el) {
			console.error('Audio element not found for playChapter')
			return
		}
		console.log('Playing chapter:', c, 'index:', idx)
		const p = c?.part_url
		if (p) {
			const abs = p.startsWith('http') ? p : `${api}${p}`
			console.log('Playing chapter part:', abs)
			setCurrentSrc(abs)
			el.src = abs
				setIsPartMode(true)
				if (typeof idx === 'number') setActiveChapter(idx)
			ensurePlay()
			return
		}
		if (typeof c?.start_ms === 'number') {
			console.log('Seeking to timestamp:', c.start_ms)
				setIsPartMode(false)
			if (currentSrc !== mergedSrc) {
				console.log('Loading merged audio and seeking')
				setCurrentSrc(mergedSrc)
				el.src = mergedSrc
				el.onloadeddata = () => {
					el.currentTime = (c.start_ms || 0) / 1000
					ensurePlay()
				}
				el.load()
			} else {
				console.log('Seeking in current audio')
				el.currentTime = (c.start_ms || 0) / 1000
				ensurePlay()
			}
				if (typeof idx === 'number') setActiveChapter(idx)
		} else {
			console.warn('Chapter has no start_ms or part_url:', c)
		}
	}

	const gotoPrev = () => {
		if (!chapters.length) return
			const idx = activeChapter == null ? 0 : Math.max(0, activeChapter - 1)
			playChapter(chapters[idx], idx)
	}
	const gotoNext = () => {
		if (!chapters.length) return
			const idx = activeChapter == null ? 0 : Math.min(chapters.length - 1, activeChapter + 1)
			playChapter(chapters[idx], idx)
	}

		const skip = (deltaSec: number) => {
			const el = audioRef.current
			if (!el) return
			el.currentTime = Math.max(0, Math.min((el.currentTime || 0) + deltaSec, duration || (el.currentTime || 0) + deltaSec))
		}

		// Apply playback rate
		React.useEffect(() => {
			const el = audioRef.current
			if (!el) return
			try { el.playbackRate = playbackRate } catch {}
		}, [playbackRate])

		// Keyboard shortcuts: Space (play/pause), [ / ] skip, , / . prev/next chapter
		React.useEffect(() => {
			const onKey = (e: KeyboardEvent) => {
				const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
				if (tag === 'input' || tag === 'textarea' || (e as any).isComposing) return
				if (e.code === 'Space') { e.preventDefault(); playPause(); }
				else if (e.key === '[') { e.preventDefault(); skip(-15); }
				else if (e.key === ']') { e.preventDefault(); skip(15); }
				else if (e.key === ',') { e.preventDefault(); gotoPrev(); }
				else if (e.key === '.') { e.preventDefault(); gotoNext(); }
			}
			window.addEventListener('keydown', onKey)
			return () => window.removeEventListener('keydown', onKey)
		}, [playPause, gotoPrev, gotoNext])

	return (
		<div className="podcast-studio-container">
			{/* Modern Header */}
			<div className="podcast-header">
				<div className="podcast-header-content">
					<div className="podcast-icon">🎧</div>
					<div className="podcast-title">
						<h2>Podcast Studio</h2>
						<p>AI-Generated Content Player</p>
					</div>
				</div>
				
				<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
					<button
						onClick={() => setIsMinimized(!isMinimized)}
						title={isMinimized ? 'Expand' : 'Minimize'}
						className="minimize-btn"
					>
						{isMinimized ? '↗️' : '↙️'}
					</button>
				</div>
			</div>

			{!isMinimized && (
				<>
					{/* Live Subtitle Display */}
					{showSubtitles && currentSubtitle && (
						<div className="live-subtitle">
							<div className="live-indicator-bar" />
							<div className="subtitle-header">
								<div className="live-badge">
									<div className="live-dot" />
									LIVE SUBTITLE
								</div>
								<div className="speaker-badge">
									{currentSubtitle.speaker}
								</div>
							</div>
							<div className="subtitle-text" style={{
								fontSize: subtitleSize === 'small' ? 14 : subtitleSize === 'large' ? 18 : 16
							}}>
								{currentSubtitle.text}
							</div>
						</div>
					)}

					{/* Main Player Controls */}
					<div className="player-controls">
						{/* Progress Bar */}
						<div className="progress-container">
							<div className="time-labels">
								<span>{fmt(currentTime)}</span>
								<span>{fmt(duration)}</span>
							</div>
							<div className="progress-bar-wrapper" onClick={(e) => {
								const rect = e.currentTarget.getBoundingClientRect()
								const pos = (e.clientX - rect.left) / rect.width
								seek(pos * duration)
							}}>
								<div className="progress-fill" style={{
									width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`
								}} />
								{/* Chapter markers */}
								{chapters.map((c, i) => {
									if (typeof c.start_ms !== 'number' || !duration) return null
									const pos = (c.start_ms / 1000) / duration * 100
									return (
										<div
											key={i}
											className="chapter-marker"
											style={{ left: `${pos}%` }}
										/>
									)
								})}
							</div>
						</div>

						{/* Transport Controls */}
						<div className="transport-controls">
							<button 
								onClick={gotoPrev} 
								title="Previous chapter"
								className="control-btn secondary"
							>⏮</button>
							
							<button 
								onClick={() => skip(-15)} 
								title="Back 15s"
								className="control-btn secondary"
							>-15</button>
							
							<button 
								onClick={playPause} 
								title={playing ? 'Pause' : 'Play'}
								className="play-btn"
							>
								{playing ? '⏸️' : '▶️'}
							</button>
							
							<button 
								onClick={() => skip(15)} 
								title="Forward 15s"
								className="control-btn secondary"
							>+15</button>
							
							<button 
								onClick={gotoNext} 
								title="Next chapter"
								className="control-btn secondary"
							>⏭</button>
						</div>

						{/* Secondary Controls */}
						<div className="secondary-controls">
							<div className="control-group">
								<span className="control-label">Speed:</span>
								<select
									value={String(playbackRate)}
									onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
									className="styled-select"
								>
									<option value="0.75">0.75×</option>
									<option value="1">1×</option>
									<option value="1.25">1.25×</option>
									<option value="1.5">1.5×</option>
									<option value="2">2×</option>
								</select>
							</div>
							
							<div className="control-group">
								<span className="control-label">Volume:</span>
								<input
									type="range"
									min={0}
									max={1}
									step={0.1}
									value={volume}
									onChange={(e) => {
										const vol = parseFloat(e.target.value)
										setVolume(vol)
										if (audioRef.current) audioRef.current.volume = vol
									}}
									className="volume-slider"
								/>
							</div>
							
							<div className="control-group">
								<button
									onClick={() => setShowSubtitles(!showSubtitles)}
									title="Toggle subtitles"
									className={`action-btn ${showSubtitles ? 'active' : ''}`}
								>📝</button>
								
								<a 
									href={currentSrc} 
									target="_blank" 
									rel="noreferrer" 
									title="Download audio"
									className="action-btn"
								>⬇️</a>
							</div>
						</div>
					</div>

					{/* Subtitle Settings */}
					{showSubtitles && (
						<div style={{
							background: '#f8fafc',
							margin: '0 32px 16px',
							padding: '12px 20px',
							borderRadius: 12,
							border: '1px solid #e2e8f0',
							display: 'flex',
							justifyContent: 'flex-end'
						}}>
							<div className="control-group">
								<span className="control-label">Size:</span>
								<select
									value={subtitleSize}
									onChange={(e) => setSubtitleSize(e.target.value as 'small' | 'medium' | 'large')}
									className="styled-select"
								>
									<option value="small">Small</option>
									<option value="medium">Medium</option>
									<option value="large">Large</option>
								</select>
							</div>
						</div>
					)}

					{/* Audio Element */}
					<audio ref={audioRef} src={currentSrc} crossOrigin="anonymous" preload="metadata" style={{ display: 'none' }} />

					{/* Error Display */}
					{errorMsg && (
						<div style={{
							margin: '0 32px 16px',
							padding: '16px 20px',
							borderRadius: 12,
							border: '1px solid #fecaca',
							background: 'rgba(254, 242, 242, 0.95)',
							color: '#991b1b',
							fontSize: 13,
							display: 'flex',
							alignItems: 'center',
							gap: 12
						}}>
							<span style={{ fontWeight: 600 }}>⚠️ {errorMsg}</span>
							<a href={currentSrc} target="_blank" rel="noreferrer" style={{ 
								fontWeight: 700, 
								color: '#b91c1c',
								textDecoration: 'underline'
							}}>Open Audio Directly</a>
						</div>
					)}

					{/* Enhanced Transcript & Chapters */}
					{chapters.length > 0 && (
						<div className="transcript-container">
							{/* Transcript Header */}
							<div className="transcript-header">
								<div className="transcript-title">
									<h3>Interactive Transcript</h3>
									<p>{chapters.length} chapters • Click to jump to section</p>
								</div>
								
								<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
									<button
										onClick={() => setShowTranscript(!showTranscript)}
										className={`action-btn ${showTranscript ? 'active' : ''}`}
										style={{ color: '#64748b', background: showTranscript ? '#eff6ff' : '#fff', borderColor: '#e2e8f0' }}
									>
										{showTranscript ? 'Hide' : 'Show'}
									</button>
									
									{showTranscript && (
										<>
											<select
												value={transcriptMode}
												onChange={(e) => setTranscriptMode(e.target.value as 'chapters' | 'fullText')}
												className="styled-select"
												style={{ color: '#334155', background: '#fff', borderColor: '#e2e8f0' }}
											>
												<option value="chapters">Chapters</option>
												<option value="fullText">Full Text</option>
											</select>
											
											<button
												onClick={() => {
													const transcript = generateFullTranscript()
													navigator.clipboard.writeText(transcript).catch(() => {
														const textArea = document.createElement('textarea')
														textArea.value = transcript
														document.body.appendChild(textArea)
														textArea.select()
														document.execCommand('copy')
														document.body.removeChild(textArea)
													})
												}}
												title="Copy transcript"
												className="action-btn"
												style={{ color: '#64748b', background: '#fff', borderColor: '#e2e8f0' }}
											>
												📋
											</button>
										</>
									)}
								</div>
							</div>

							{/* Transcript Content */}
							{showTranscript && (
								<div className="transcript-content">
									{transcriptMode === 'fullText' ? (
										<div style={{
											padding: '24px',
											fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, monospace',
											fontSize: 13,
											lineHeight: 1.8,
											color: '#374151',
											whiteSpace: 'pre-wrap',
											wordBreak: 'break-word'
										}}>
											{generateFullTranscript()}
										</div>
									) : (
										<div style={{ padding: '12px 0' }}>
											{chapters.map((c, i) => {
												const active = i === activeChapter
												const badge = (c.speaker || 'Unknown Speaker').toString().trim()
												const speakerColors = {
													alex: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
													jordan: { bg: '#ede9fe', border: '#8b5cf6', text: '#6d28d9' },
													charon: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
													puck: { bg: '#ede9fe', border: '#8b5cf6', text: '#6d28d9' },
													a: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
													b: { bg: '#ede9fe', border: '#8b5cf6', text: '#6d28d9' },
													'speaker 1': { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
													'speaker 2': { bg: '#ede9fe', border: '#8b5cf6', text: '#6d28d9' },
													'speaker a': { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
													'speaker b': { bg: '#ede9fe', border: '#8b5cf6', text: '#6d28d9' }
												}
												const defaultColors = { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' }
												const colors = speakerColors[badge.toLowerCase() as keyof typeof speakerColors] || defaultColors
												
												return (
													<div 
														key={c.index}
														ref={active ? activeChapterRef : null}
														className={`chapter-item ${active ? 'active' : ''}`}
														onClick={() => playChapter(c, i)}
													>
														<div className="chapter-header">
															<div className="chapter-time">
																{typeof c.start_ms === 'number' ? 
																	`${Math.floor(c.start_ms/1000/60)}:${String(Math.floor(c.start_ms/1000)%60).padStart(2,'0')}` : 
																	'--:--'
																}
															</div>
															<div className="chapter-speaker" style={{
																background: colors.bg,
																color: colors.text
															}}>
																{badge}
															</div>
														</div>
														
														<div className="chapter-text">
															{c.text}
														</div>
														
														<div className="chapter-actions">
															<button
																onClick={(e) => {
																	e.stopPropagation()
																	const chapterText = `[${typeof c.start_ms === 'number' ? 
																		`${Math.floor(c.start_ms/1000/60)}:${String(Math.floor(c.start_ms/1000)%60).padStart(2,'0')}` : 
																		'--:--'
																	}] ${badge}: ${c.text}`
																	navigator.clipboard.writeText(chapterText).catch(() => {})
																}}
																title="Copy chapter"
																className="chapter-action-btn"
															>📋</button>
															
															<div className="chapter-action-btn" style={{
																background: active && playing ? '#ef4444' : '#10b981',
																color: '#fff',
																borderColor: 'transparent'
															}}>
																{active && playing ? '⏸️' : '▶️'}
															</div>
														</div>
													</div>
												)
											})}
										</div>
									)}
								</div>
							)}
						</div>
					)}

					{/* No Chapters Message */}
					{chapters.length === 0 && (
						<div className="empty-state">
							<div className="empty-icon">🎙️</div>
							<h3>No Chapters Available</h3>
							<p>Generate a podcast to see interactive chapters and subtitles</p>
						</div>
					)}
				</>
			)}
		</div>
	)
}
