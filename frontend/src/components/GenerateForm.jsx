const languages = [
  'English', 'Hindi', 'Spanish', 'French', 'German', 'Mandarin Chinese',
  'Arabic', 'Portuguese', 'Japanese', 'Korean', 'Italian', 'Russian',
  'Dutch', 'Turkish', 'Polish', 'Swedish',
]

const levels = ['beginner', 'intermediate', 'advanced']

export default function GenerateForm({
  topic, setTopic, language, setLanguage, level, setLevel,
  onSubmit, isLoading, error, setError,
}) {
  return (
    <div id="generate-form" className="w-full max-w-2xl mx-auto mt-10 px-4">
      <div className="bg-surface border border-white/10 rounded-2xl p-6 space-y-5">
        {/* Topic textarea */}
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="What do you want to learn? e.g. 'Explain how black holes form' or 'Teach me about the Roman Empire'"
          rows={3}
          className="w-full bg-[#08080f] border border-white/10 rounded-2xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-purple/60 transition-all duration-300 resize-none"
        />

        {/* Language & Level row */}
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Language */}
          <div className="flex-1">
            <label className="text-slate-400 text-sm mb-2 block">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-[#08080f] border border-white/10 rounded-xl px-4 py-2.5 text-white cursor-pointer focus:outline-none focus:border-purple/60 transition-all duration-300 appearance-none"
            >
              {languages.map((lang) => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
          </div>

          {/* Level */}
          <div className="flex-1">
            <label className="text-slate-400 text-sm mb-2 block">Level</label>
            <div className="flex gap-2">
              {levels.map((l) => (
                <button
                  key={l}
                  onClick={() => setLevel(l)}
                  className={`flex-1 rounded-full px-5 py-2 text-sm border transition-all duration-300 cursor-pointer capitalize ${
                    level === l
                      ? 'bg-purple text-white border-purple'
                      : 'bg-transparent text-slate-400 border-white/20 hover:border-white/40'
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Submit button */}
        <button
          onClick={onSubmit}
          disabled={isLoading}
          className={`w-full py-4 rounded-2xl bg-gradient-to-r from-purple-600 to-cyan-500 font-semibold text-white transition-all duration-300 ${
            isLoading
              ? 'opacity-50 cursor-not-allowed'
              : 'hover:scale-[1.02] hover:shadow-lg hover:shadow-purple/25 cursor-pointer'
          }`}
        >
          ✨ Generate My Reel
        </button>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 flex items-center justify-between">
            <span className="text-red-400 text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300 ml-3 cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
