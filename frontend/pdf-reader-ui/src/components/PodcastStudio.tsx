import React from 'react'

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

	const chapters = Array.isArray(meta.chapters) ? meta.chapters : []

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
			el.addEventListener('ended', onEnded)
		return () => {
			el.removeEventListener('loadedmetadata', onLoaded)
			el.removeEventListener('timeupdate', onTime)
			el.removeEventListener('play', onPlay)
			el.removeEventListener('pause', onPause)
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

	const ensurePlay = () => {
		const el = audioRef.current
		if (!el) return
		setTimeout(() => { void el.play().catch(() => {}) }, 0)
	}

		const playPause = () => {
		const el = audioRef.current
		if (!el) return
		if (el.paused) el.play().catch(() => {})
		else el.pause()
	}

	const seek = (s: number) => {
		const el = audioRef.current
		if (!el) return
		el.currentTime = Math.max(0, Math.min(s, duration || s))
	}

		const playChapter = (c: any, idx?: number) => {
		const el = audioRef.current
		if (!el) return
		const p = c?.part_url
		if (p) {
			const abs = p.startsWith('http') ? p : `${api}${p}`
			setCurrentSrc(abs)
			el.src = abs
				setIsPartMode(true)
				if (typeof idx === 'number') setActiveChapter(idx)
			ensurePlay()
			return
		}
		if (typeof c?.start_ms === 'number') {
				setIsPartMode(false)
			if (currentSrc !== mergedSrc) {
				setCurrentSrc(mergedSrc)
				el.src = mergedSrc
				el.onloadeddata = () => {
					el.currentTime = (c.start_ms || 0) / 1000
					ensurePlay()
				}
				el.load()
			} else {
				el.currentTime = (c.start_ms || 0) / 1000
				ensurePlay()
			}
				if (typeof idx === 'number') setActiveChapter(idx)
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
		<div style={{ display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0, height: '100%' }}>
			{/* Enhanced Transport Controls */}
			<div style={{ 
				display: 'flex', 
				alignItems: 'center', 
				gap: 10,
				padding: '12px 16px',
				background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
				borderRadius: 12,
				border: '1px solid #e2e8f0'
			}}>
				<button 
					onClick={gotoPrev} 
					title="Previous chapter" 
					style={{ 
						padding: '8px 10px', 
						borderRadius: 8, 
						border: '1px solid #d1d5db', 
						background: '#fff', 
						cursor: 'pointer',
						fontSize: 14,
						fontWeight: 500,
						boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
						transition: 'all 0.15s ease'
					}}
				>⏮</button>
				
				<button 
					onClick={() => skip(-15)} 
					title="Back 15s" 
					style={{ 
						padding: '6px 8px', 
						borderRadius: 8, 
						border: '1px solid #d1d5db', 
						background: '#fff', 
						cursor: 'pointer',
						fontSize: 11,
						fontWeight: 500,
						color: '#6b7280',
						boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
					}}
				>-15s</button>
				
				<button 
					onClick={playPause} 
					title={playing ? 'Pause' : 'Play'} 
					style={{ 
						padding: '10px 16px', 
						borderRadius: 999, 
						border: 'none',
						background: playing ? '#ef4444' : '#3b82f6', 
						color: '#fff', 
						cursor: 'pointer', 
						fontWeight: 600,
						fontSize: 14,
						boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
						transition: 'all 0.2s ease'
					}}
				>
					{playing ? 'Pause' : 'Play'}
				</button>
				
				<button 
					onClick={() => skip(15)} 
					title="Forward 15s" 
					style={{ 
						padding: '6px 8px', 
						borderRadius: 8, 
						border: '1px solid #d1d5db', 
						background: '#fff', 
						cursor: 'pointer',
						fontSize: 11,
						fontWeight: 500,
						color: '#6b7280',
						boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
					}}
				>+15s</button>
				
				<button 
					onClick={gotoNext} 
					title="Next chapter" 
					style={{ 
						padding: '8px 10px', 
						borderRadius: 8, 
						border: '1px solid #d1d5db', 
						background: '#fff', 
						cursor: 'pointer',
						fontSize: 14,
						fontWeight: 500,
						boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
						transition: 'all 0.15s ease'
					}}
				>⏭</button>
				
				<div style={{ 
					marginLeft: 12, 
					fontSize: 12, 
					fontWeight: 600,
					color: '#374151', 
					width: 44, 
					textAlign: 'right',
					fontVariantNumeric: 'tabular-nums'
				}}>
					{fmt(currentTime)}
				</div>
				
				<input
					type="range"
					min={0}
					max={Math.max(1, Math.floor(duration || 0))}
					value={Math.floor(currentTime || 0)}
					onChange={(e) => seek(parseInt(e.target.value || '0', 10))}
					style={{ 
						flex: 1,
						height: 6,
						borderRadius: 3,
						background: '#e2e8f0',
						outline: 'none',
						cursor: 'pointer'
					}}
				/>
				
				<div style={{ 
					fontSize: 12, 
					fontWeight: 600,
					color: '#6b7280', 
					width: 44,
					fontVariantNumeric: 'tabular-nums'
				}}>
					{fmt(duration)}
				</div>
				
				<select
					value={String(playbackRate)}
					onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
					title="Playback speed"
					style={{ 
						fontSize: 12, 
						fontWeight: 500,
						border: '1px solid #d1d5db', 
						borderRadius: 8, 
						padding: '6px 8px', 
						background: '#fff', 
						marginLeft: 8,
						boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
					}}
				>
					<option value="0.75">0.75×</option>
					<option value="1">1×</option>
					<option value="1.25">1.25×</option>
					<option value="1.5">1.5×</option>
					<option value="2">2×</option>
				</select>
				
				<a 
					href={currentSrc} 
					target="_blank" 
					rel="noreferrer" 
					title="Download audio"
					style={{ 
						fontSize: 14, 
						marginLeft: 8,
						padding: '6px 8px',
						borderRadius: 8,
						background: '#f3f4f6',
						color: '#374151',
						textDecoration: 'none',
						border: '1px solid #d1d5db',
						boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
					}}
				>⬇️</a>
			</div>

			{/* Hidden native element */}
			<audio ref={audioRef} src={currentSrc} style={{ display: 'none' }} />

			{/* Enhanced Chapters List */}
			{chapters.length > 0 ? (
				<div style={{ overflow: 'auto', flex: 1 }}>
					<div style={{ 
						display: 'flex', 
						alignItems: 'center', 
						justifyContent: 'space-between', 
						marginBottom: 12,
						padding: '0 4px'
					}}>
						<div style={{ 
							fontSize: 13, 
							fontWeight: 700, 
							color: '#374151',
							letterSpacing: '-0.025em'
						}}>
							Chapters ({chapters.length})
						</div>
						{activeChapter !== null && (
							<div style={{
								fontSize: 11,
								fontWeight: 600,
								color: '#059669',
								padding: '2px 8px',
								borderRadius: 999,
								background: '#ecfdf5',
								border: '1px solid #10b981'
							}}>
								Chapter {activeChapter + 1}
							</div>
						)}
					</div>
					
					<div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
						{chapters.map((c, i) => {
							const active = i === activeChapter
							const badge = (c.speaker || '').toString().trim()
							const speakerColors = {
								alex: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
								jordan: { bg: '#ede9fe', border: '#8b5cf6', text: '#6d28d9' },
								a: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
								b: { bg: '#ede9fe', border: '#8b5cf6', text: '#6d28d9' }
							}
							const defaultColors = { bg: '#f3f4f6', border: '#9ca3af', text: '#374151' }
							const colors = speakerColors[badge.toLowerCase() as keyof typeof speakerColors] || defaultColors
							
							return (
								<div 
									key={c.index}
									style={{ 
										display: 'flex', 
										alignItems: 'flex-start', 
										gap: 12, 
										background: active ? '#f0f9ff' : '#fff', 
										border: '1px solid ' + (active ? '#0ea5e9' : '#e5e7eb'), 
										borderRadius: 12, 
										padding: 14,
										boxShadow: active ? '0 4px 12px rgba(14, 165, 233, 0.15)' : '0 1px 3px rgba(0,0,0,0.05)',
										transition: 'all 0.2s ease'
									}}
								>
									<div style={{ 
										fontSize: 11, 
										fontWeight: 600,
										fontVariantNumeric: 'tabular-nums',
										width: 50, 
										color: active ? '#0369a1' : '#6b7280',
										paddingTop: 2
									}}>
										{typeof c.start_ms === 'number' ? 
											`${Math.floor(c.start_ms/1000/60)}:${String(Math.floor(c.start_ms/1000)%60).padStart(2,'0')}` : 
											'--:--'
										}
									</div>
									
									<div style={{ 
										display: 'inline-block', 
										padding: '4px 10px', 
										borderRadius: 999, 
										background: colors.bg, 
										border: `1px solid ${colors.border}`,
										fontSize: 11, 
										fontWeight: 600,
										color: colors.text,
										minWidth: 60,
										textAlign: 'center'
									}}>
										{badge || 'Speaker'}
									</div>
									
									<div style={{ 
										flex: 1, 
										fontSize: 13, 
										lineHeight: 1.5,
										color: '#374151'
									}}>
										{c.text}
									</div>
									
									<button 
										onClick={() => playChapter(c, i)} 
										style={{ 
											fontSize: 11, 
											fontWeight: 600,
											padding: '6px 12px', 
											border: '1px solid #d1d5db', 
											borderRadius: 8, 
											background: '#fff', 
											cursor: 'pointer',
											color: '#374151',
											boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
											transition: 'all 0.15s ease'
										}}
									>
										▶ Play
									</button>
								</div>
							)
						})}
					</div>
				</div>
			) : (
				<div style={{ 
					color: '#9ca3af', 
					fontSize: 13,
					textAlign: 'center',
					padding: 24,
					background: '#f9fafb',
					borderRadius: 12,
					border: '1px solid #e5e7eb'
				}}>
					No chapters available.
				</div>
			)}
		</div>
	)
}
