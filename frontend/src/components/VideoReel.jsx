export default function VideoReel({ videoUrl, videoStatus }) {
  if (videoStatus === 'processing') {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#0f0f1a] text-center p-6">
        <div
          className="w-12 h-12 border-3 border-purple border-t-cyan rounded-full mb-4"
          style={{ borderWidth: '3px', animation: 'spin-slow 1.2s linear infinite' }}
        />
        <span className="text-4xl mb-3">🎬</span>
        <p className="text-slate-400 text-sm mb-2">Rendering your reel...</p>
        <div className="flex gap-1.5 mb-4">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-purple"
              style={{
                animation: `pulse-glow 1.5s ease-in-out ${i * 0.3}s infinite`,
                opacity: 0.5,
              }}
            />
          ))}
        </div>
        <p className="text-slate-600 text-xs">~60-90 seconds</p>
      </div>
    )
  }

  if (videoStatus === 'completed' && videoUrl) {
    return (
      <div
        className="w-full h-full"
        style={{ animation: 'fade-in-up 0.6s ease forwards' }}
      >
        <video
          src={videoUrl}
          autoPlay
          loop
          controls
          className="w-full h-full object-cover"
        />
      </div>
    )
  }

  if (videoStatus === 'failed') {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#0f0f1a] text-center p-6">
        <div className="w-12 h-12 rounded-full border-2 border-red-500 flex items-center justify-center mb-3">
          <span className="text-red-500 text-xl">✕</span>
        </div>
        <p className="text-red-400 text-sm mb-1">Generation failed</p>
        <p className="text-slate-500 text-xs">Try again with a different topic</p>
      </div>
    )
  }

  /* Idle placeholder */
  return (
    <div className="w-full h-full flex flex-col items-center justify-center bg-[#0f0f1a] text-center p-6">
      <span className="text-5xl mb-3 opacity-20">🎬</span>
      <p className="text-slate-600 text-sm">Your reel will appear here</p>
    </div>
  )
}
