export default function Hero() {
  return (
    <div className="relative overflow-hidden text-center px-4">
      {/* Gradient orbs */}
      <div
        className="absolute -top-20 -left-20 w-96 h-96 rounded-full opacity-10 blur-3xl pointer-events-none bg-purple"
        style={{ animation: 'orb-drift 25s ease-in-out infinite' }}
      />
      <div
        className="absolute -bottom-20 -right-20 w-96 h-96 rounded-full opacity-10 blur-3xl pointer-events-none bg-cyan"
        style={{ animation: 'orb-drift 35s ease-in-out infinite reverse' }}
      />

      {/* Content */}
      <div className="relative z-10">
        <div className="inline-flex items-center gap-2 border border-purple/40 text-purple rounded-full px-4 py-1.5 text-sm mb-6">
          ✦ AI-Powered Learning
        </div>

        <h1 className="text-5xl md:text-7xl font-bold leading-tight">
          <span className="text-white">Learn Anything</span>
          <br />
          <span className="bg-gradient-to-r from-purple to-cyan bg-clip-text text-transparent">
            In 60 Seconds
          </span>
        </h1>

        <p className="text-lg text-slate-400 max-w-lg mx-auto mt-4">
          Type a topic. Get a personalised 30-60 second video lesson — in your language, in seconds.
        </p>

        <div className="mt-6 flex gap-3 justify-center flex-wrap">
          {['🎬 Lip-sync Avatar', '🌍 70+ Languages', '⚡ 60 Seconds'].map((label) => (
            <span
              key={label}
              className="bg-surface border border-white/10 rounded-full px-4 py-1.5 text-sm text-slate-400"
            >
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
