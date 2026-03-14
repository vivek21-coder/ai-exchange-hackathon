import VideoReel from './VideoReel'

export default function PhoneFrame({ videoUrl, videoStatus }) {
  return (
    <div
      className="flex justify-center"
      style={{ animation: 'float 6s ease-in-out infinite' }}
    >
      <div
        className="relative rounded-[36px] overflow-hidden bg-[#0f0f1a]"
        style={{
          width: 280,
          aspectRatio: '9/16',
          border: '8px solid #1e1e38',
          boxShadow:
            videoStatus === 'completed' && videoUrl
              ? undefined
              : 'inset 0 0 30px rgba(0,0,0,0.5), 0 20px 60px rgba(0,0,0,0.5)',
          animation:
            videoStatus === 'completed' && videoUrl
              ? 'pulse-glow 3s ease-in-out infinite'
              : undefined,
        }}
      >
        {/* Top notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-20 h-5 bg-[#1e1e38] rounded-b-2xl z-10" />
        <VideoReel videoUrl={videoUrl} videoStatus={videoStatus} />
      </div>
    </div>
  )
}
