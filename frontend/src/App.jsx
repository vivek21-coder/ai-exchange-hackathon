import { useState, useEffect, useRef } from 'react'
import Hero from './components/Hero'
import GenerateForm from './components/GenerateForm'
import ExampleChips from './components/ExampleChips'
import LoadingState from './components/LoadingState'
import PhoneFrame from './components/PhoneFrame'
import ScriptCard from './components/ScriptCard'

export default function App() {
  const [topic, setTopic] = useState('')
  const [language, setLanguage] = useState('English')
  const [level, setLevel] = useState('beginner')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [script, setScript] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)
  const [videoStatus, setVideoStatus] = useState('idle')
  const [error, setError] = useState(null)

  const loadingTimers = useRef([])
  const resultsRef = useRef(null)

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic to learn about.')
      return
    }

    setIsLoading(true)
    setError(null)
    setVideoUrl(null)
    setVideoStatus('idle')
    setScript(null)
    setLoadingStep(0)

    loadingTimers.current.forEach(clearTimeout)
    loadingTimers.current = [
      setTimeout(() => setLoadingStep(1), 5000),
      setTimeout(() => setLoadingStep(2), 25000),
      setTimeout(() => setLoadingStep(3), 35000),
    ]

    const controller = new AbortController()
    // No timeout for the fetch request, as video generation can take several minutes
    // and the user has indicated they are willing to wait.

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, language, level }),
        signal: controller.signal,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `Server error (${res.status})`)
      }

      const data = await res.json()
      setScript(data.script)
      setVideoUrl(data.video_url)
      setVideoStatus('completed')
      setIsLoading(false)
    } catch (err) {
      setError(err.name === 'AbortError' ? 'Request timed out. Please try again.' : err.message)
      setIsLoading(false)
    }

    loadingTimers.current.forEach(clearTimeout)
    loadingTimers.current = []
  }

  // Scroll to results when script appears
  useEffect(() => {
    if (script && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
    }
  }, [script])

  const handleExampleSelect = (exTopic, exLanguage) => {
    setTopic(exTopic)
    setLanguage(exLanguage)
    document.getElementById('generate-form')?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleGenerateAnother = () => {
    setScript(null)
    setVideoUrl(null)
    setVideoStatus('idle')
    setError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-[#08080f]">
      {/* Section 1: Hero + Form */}
      <section className="min-h-screen flex flex-col items-center justify-center py-20">
        <Hero />
        <GenerateForm
          topic={topic}
          setTopic={setTopic}
          language={language}
          setLanguage={setLanguage}
          level={level}
          setLevel={setLevel}
          onSubmit={handleGenerate}
          isLoading={isLoading}
          error={error}
          setError={setError}
        />
        <ExampleChips onSelect={handleExampleSelect} />
        {isLoading && <LoadingState step={loadingStep} />}
      </section>

      {/* Section 2: Results */}
      {script && (
        <section
          ref={resultsRef}
          className="py-20 px-4"
          style={{ animation: 'fade-in-up 0.6s ease forwards' }}
        >
          <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl md:text-3xl font-bold text-center mb-12">
              <span className="bg-gradient-to-r from-purple to-cyan bg-clip-text text-transparent">
                Your Reel is Ready
              </span>
            </h2>

            <div className="flex flex-col md:flex-row items-center md:items-start justify-center gap-10">
              <PhoneFrame videoUrl={videoUrl} videoStatus={videoStatus} />
              <ScriptCard script={script} topic={topic} language={language} level={level} />
            </div>

            {/* Generate Another */}
            <div className="text-center mt-12">
              <button
                onClick={handleGenerateAnother}
                className="px-8 py-3 rounded-2xl border border-purple/40 text-purple hover:bg-purple/10 hover:border-purple transition-all duration-300 cursor-pointer font-medium"
              >
                Generate Another Reel →
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="py-10 text-center">
        <p className="text-slate-500/40 text-xs">
          LearnCast AI — Learn anything in 60 seconds
        </p>
        <p className="text-slate-500/40 text-xs mt-1">
          Powered by Gemini + Flux + Edge TTS + FFmpeg
        </p>
      </footer>
    </div>
  )
}
