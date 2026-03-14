const steps = [
  { icon: '✦', label: 'Gemini Pro is writing your reel script...' },
  { icon: '🎨', label: 'Generating background visuals with Flux...' },
  { icon: '🎙', label: 'Generating voiceover...' },
  { icon: '🎬', label: 'Composing your video reel...' },
]

export default function LoadingState({ step }) {
  return (
    <div
      className="w-full max-w-2xl mx-auto mt-6 px-4"
      style={{ animation: 'fade-in-up 0.5s ease forwards' }}
    >
      <div
        className="bg-surface border border-white/10 rounded-2xl p-6"
        style={{ animation: 'pulse-glow 3s ease-in-out infinite' }}
      >
        <div className="space-y-4">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center gap-3">
              {i < step ? (
                <span className="text-green-400 text-lg w-6 text-center">✓</span>
              ) : i === step ? (
                <span
                  className="inline-block w-5 h-5 border-2 border-purple border-t-transparent rounded-full"
                  style={{ animation: 'spin-slow 1s linear infinite' }}
                />
              ) : (
                <span className="text-slate-600 text-lg w-6 text-center">{s.icon}</span>
              )}
              <span
                className={`text-sm transition-colors duration-300 ${
                  i <= step ? 'text-white' : 'text-slate-600'
                }`}
              >
                {s.icon} {s.label}
              </span>
            </div>
          ))}
        </div>

        {/* Progress bar */}
        <div className="mt-5 w-full h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple to-cyan rounded-full"
            style={{ animation: 'progress-fill 60s linear forwards' }}
          />
        </div>
        <p className="text-slate-500 text-xs mt-2 text-center">
          This usually takes 60-90 seconds
        </p>
      </div>
    </div>
  )
}
