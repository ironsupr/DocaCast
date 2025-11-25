import React from 'react'
import './PodcastStudio.css'

// Icons
const PlayIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
const PauseIcon = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
const IconReplay15 = () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><text x="12" y="18" fontSize="8" textAnchor="middle" fill="currentColor" stroke="none">15</text></svg>
const IconForward15 = () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><text x="12" y="18" fontSize="8" textAnchor="middle" fill="currentColor" stroke="none">15</text></svg>
const IconVolume = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
const IconDownload = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
const IconPodcast = () => <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
const IconScript = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
const IconClose = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>

type Props = {
	meta: { url: string; parts?: string[]; chapters?: Array<{ index: number; speaker: string; text: string; start_ms?: number; end_ms?: number; part_url?: string }> }
	onClose?: () => void
}


export default function PodcastStudio({ meta, onClose }: Props) {
	const audioRef = React.useRef<HTMLAudioElement | null>(null)
	const transcriptRef = React.useRef<HTMLDivElement | null>(null)
	const api = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '')
	const mergedSrc = meta.url.startsWith('http') ? meta.url : `${api}${meta.url}`

	const [currentSrc, setCurrentSrc] = React.useState<string>(mergedSrc)
	const [duration, setDuration] = React.useState<number>(0)
	const [currentTime, setCurrentTime] = React.useState<number>(0)
	const [playing, setPlaying] = React.useState<boolean>(false)
	const [playbackRate, setPlaybackRate] = React.useState<number>(1)
	const [volume, setVolume] = React.useState<number>(1)
	const [errorMsg, setErrorMsg] = React.useState<string | null>(null)
	const [showTranscript, setShowTranscript] = React.useState(false)

	const chapters = Array.isArray(meta.chapters) ? meta.chapters : []
	
	// Derive title/speaker info from chapters or default
	const title = "AI Podcast"
	const speakers = chapters.length > 0 
		? Array.from(new Set(chapters.map(c => c.speaker))).join(", ") 
		: "AI Host"

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
				const mediaErr = (el as any)?.error
				setErrorMsg(mediaErr ? `Error ${mediaErr.code}` : 'Error')
			} catch { setErrorMsg('Error') }
		}
		el.addEventListener('loadedmetadata', onLoaded)
		el.addEventListener('timeupdate', onTime)
		el.addEventListener('play', onPlay)
		el.addEventListener('pause', onPause)
		el.addEventListener('error', onError)
		return () => {
			el.removeEventListener('loadedmetadata', onLoaded)
			el.removeEventListener('timeupdate', onTime)
			el.removeEventListener('play', onPlay)
			el.removeEventListener('pause', onPause)
			el.removeEventListener('error', onError)
		}
	}, [])

	// Auto-scroll transcript to active segment
	// (Removed auto-scroll logic as we now use a single subtitle line)

	const playPause = () => {
		const el = audioRef.current
		if (!el) return
		if (el.paused) el.play().catch(console.error)
		else el.pause()
	}

	const seek = (s: number) => {
		const el = audioRef.current
		if (!el) return
		el.currentTime = Math.max(0, Math.min(s, duration || s))
	}

	// Reset when source changes
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

	// Apply playback rate
	React.useEffect(() => {
		const el = audioRef.current
		if (!el) return
		try { el.playbackRate = playbackRate } catch {}
	}, [playbackRate])

	// Keyboard shortcuts
	React.useEffect(() => {
		const onKey = (e: KeyboardEvent) => {
			const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
			if (tag === 'input' || tag === 'textarea' || (e as any).isComposing) return
			if (e.code === 'Space') { e.preventDefault(); playPause(); }
		}
		window.addEventListener('keydown', onKey)
		return () => window.removeEventListener('keydown', onKey)
	}, [])

	// Find active segment for subtitle
	const activeSegment = chapters.find(c => 
		currentTime * 1000 >= (c.start_ms || 0) && 
		currentTime * 1000 < (c.end_ms || Infinity)
	)

	return (
		<>
			{/* Floating Subtitle */}
			{showTranscript && activeSegment && (
				<div className="transcript-subtitle-container">
					<div className="transcript-subtitle">
						<span className="speaker-label">{activeSegment.speaker}</span>
						{activeSegment.text}
					</div>
				</div>
			)}

			<div className="podcast-bottom-player">
				{/* Left: Info */}
				<div className="player-left">
					{/* Removed cover art as requested */}
					<div className="track-info">
						<div className="track-title" title={title}>{title}</div>
						<div className="track-speaker" title={speakers}>{speakers}</div>
					</div>
				</div>

				{/* Center: Controls */}
				<div className="player-center">
					<div className="player-controls-row">
						<button className="control-btn" onClick={() => seek(currentTime - 15)} title="-15s">
							<IconReplay15 />
						</button>
						<button className="control-btn main-play" onClick={playPause} title={playing ? "Pause" : "Play"}>
							{playing ? <PauseIcon /> : <PlayIcon />}
						</button>
						<button className="control-btn" onClick={() => seek(currentTime + 15)} title="+15s">
							<IconForward15 />
						</button>
					</div>
					<div className="progress-bar-container">
						<span>{fmt(currentTime)}</span>
						<div className="progress-track" onClick={(e) => {
							const rect = e.currentTarget.getBoundingClientRect()
							const pos = (e.clientX - rect.left) / rect.width
							seek(pos * duration)
						}}>
							<div className="progress-fill" style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }} />
						</div>
						<span>{fmt(duration)}</span>
					</div>
				</div>

				{/* Right: Volume & Extras */}
				<div className="player-right">
					{errorMsg && <span style={{ color: '#ef4444', fontSize: 11 }}>{errorMsg}</span>}
					
					<div className="volume-container">
						<div className="volume-icon"><IconVolume /></div>
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

					<select 
						className="speed-select"
						value={playbackRate}
						onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
					>
						<option value="0.75">0.75x</option>
						<option value="1">1x</option>
						<option value="1.25">1.25x</option>
						<option value="1.5">1.5x</option>
						<option value="2">2x</option>
					</select>

					<button 
						className={`control-btn ${showTranscript ? 'active' : ''}`} 
						onClick={() => setShowTranscript(!showTranscript)}
						title="Toggle Subtitles"
						style={{ color: showTranscript ? '#3b82f6' : undefined }}
					>
						<IconScript />
					</button>

					<a href={currentSrc} download target="_blank" rel="noreferrer" className="control-btn download-btn" title="Download">
						<IconDownload />
					</a>
					{onClose && (
						<button className="control-btn" onClick={onClose} title="Close Player">
							<IconClose />
						</button>
					)}
				</div>

				<audio ref={audioRef} src={currentSrc} crossOrigin="anonymous" preload="metadata" style={{ display: 'none' }} />
			</div>
		</>
	)
}