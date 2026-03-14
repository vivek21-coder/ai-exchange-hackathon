import { useState } from 'react'

function highlightHook(script) {
  if (!script) return script
  const firstPeriod = script.indexOf('.')
  const cutoff = firstPeriod > 0 && firstPeriod < 80 ? firstPeriod + 1 : script.split(/\s+/).slice(0, 8).join(' ').length
  const hook = script.slice(0, cutoff)
  const rest = script.slice(cutoff)
  return (
    <>
      <span className="text-purple-400 font-medium">{hook}</span>
      {rest}
    </>
  )
}

export default function ScriptCard({ script, topic, language, level }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(script)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const shareText = `I just learned about ${topic} in 60 seconds with LearnCast AI 🎬 #LearnCastAI #LearnOnTheGo`

  return (
    <div
      className="bg-surface border border-white/10 rounded-2xl p-6 max-w-sm w-full"
      style={{ animation: 'fade-in-up 0.6s ease forwards' }}
    >
      {/* Header */}
      <h3 className="font-semibold text-lg text-white truncate">{topic}</h3>
      <div className="flex gap-2 mt-2">
        <span className="text-xs px-3 py-1 rounded-full border border-cyan/30 text-cyan">
          {language}
        </span>
        <span className="text-xs px-3 py-1 rounded-full border border-purple/30 text-purple capitalize">
          {level}
        </span>
      </div>

      {/* Script */}
      <p className="text-slate-400 text-sm mt-4 mb-2">📝 Reel Script</p>
      <p className="text-white/90 leading-relaxed text-sm">
        {highlightHook(script)}
      </p>

      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="mt-4 flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors duration-300 cursor-pointer"
      >
        {copied ? (
          <span className="text-green-400">Copied! ✓</span>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" strokeWidth="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" strokeWidth="2" />
            </svg>
            Copy script
          </>
        )}
      </button>

      {/* Share */}
      <div className="mt-5 pt-4 border-t border-white/5">
        <p className="text-slate-400 text-sm mb-2">🚀 Share this concept</p>
        <div className="flex gap-2">
          <button
            onClick={() =>
              window.open(
                `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}`,
                '_blank'
              )
            }
            className="text-xs px-4 py-2 rounded-full border border-white/10 text-slate-400 hover:border-purple/60 hover:text-white transition-all duration-300 cursor-pointer"
          >
            Twitter/X
          </button>
          <button
            onClick={() =>
              window.open(
                `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent('https://learncast.ai')}&summary=${encodeURIComponent(shareText)}`,
                '_blank'
              )
            }
            className="text-xs px-4 py-2 rounded-full border border-white/10 text-slate-400 hover:border-cyan/60 hover:text-white transition-all duration-300 cursor-pointer"
          >
            LinkedIn
          </button>
        </div>
      </div>
    </div>
  )
}
