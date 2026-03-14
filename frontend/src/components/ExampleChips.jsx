const examples = [
  { label: '⚛️ Quantum entanglement', topic: 'Explain quantum entanglement', language: 'English' },
  { label: '📈 How stock markets work', topic: 'How does the stock market work', language: 'English' },
  { label: '🧠 Machine learning in Hindi', topic: 'What is machine learning', language: 'Hindi' },
  { label: '🌊 Climate change basics', topic: 'Explain climate change and its causes', language: 'English' },
]

export default function ExampleChips({ onSelect }) {
  return (
    <div className="mt-6 text-center">
      <p className="text-slate-400 text-sm mb-3">Try an example →</p>
      <div className="flex flex-wrap justify-center gap-2">
        {examples.map((ex) => (
          <button
            key={ex.label}
            onClick={() => onSelect(ex.topic, ex.language)}
            className="border border-purple/30 rounded-full px-4 py-2 text-sm text-slate-300 hover:border-purple/80 hover:bg-purple/10 transition-all duration-300 cursor-pointer"
          >
            {ex.label}
          </button>
        ))}
      </div>
    </div>
  )
}
