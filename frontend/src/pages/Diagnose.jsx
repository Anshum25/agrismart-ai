import { useState } from 'react'
import toast from 'react-hot-toast'
import DropZone from '../components/DropZone.jsx'
import ResultCard from '../components/ResultCard.jsx'

export default function Diagnose() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile)
    setPreviewUrl(URL.createObjectURL(selectedFile))
    setResult(null)
  }

  const handleClear = () => {
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
  }

  const handleAnalyze = async () => {
    if (!file) return

    setLoading(true)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/predict/gradcam', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResult(data)
      
      if (!data.model_loaded) {
        toast('Running in Demo Mode (Cloud weights not loaded)', { icon: '💡' })
      } else {
        toast.success('Analysis complete!')
      }
      
      // Scroll to result slightly delayed to allow render
      setTimeout(() => {
        document.getElementById('diagnosis-result')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)

    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="section container">
      <div className="text-center mb-4">
        <h1 className="section-title" style={{ fontSize: '2rem' }}>Leaf Diagnostics</h1>
        <p className="section-sub mx-auto">Upload a photo of an affected plant leaf to get a real-time diagnosis.</p>
      </div>

      <div className="diagnose-layout">
        {/* Left Column: Upload & Actions */}
        <div>
          {!previewUrl ? (
            <DropZone onFileSelected={handleFileSelect} disabled={loading} />
          ) : (
            <div className="image-preview">
              <img src={previewUrl} alt="Leaf preview" />
              <div className="image-preview-overlay">Selected: {file?.name}</div>
            </div>
          )}

          <div className="flex gap-1 mt-2">
            <button
              className="btn btn-primary w-full justify-center"
              onClick={handleAnalyze}
              disabled={!file || loading}
            >
              {loading ? 'Analyzing...' : '🚀 Analyze Plant Health'}
            </button>
            {file && !loading && (
              <button className="btn btn-ghost" onClick={handleClear}>
                Clear
              </button>
            )}
          </div>

          {loading && (
            <div className="spinner-wrap">
              <div className="spinner"></div>
              <p className="spinner-text">Running ResNet50 Inference & computing Grad-CAM...</p>
            </div>
          )}
        </div>

        {/* Right Column: Results */}
        <div>
          {!loading && !result && (
            <div className="card" style={{ background: 'var(--sand)', border: 'none', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <p className="text-muted text-center">
                👈 Upload an image and click analyze to see results here.
              </p>
            </div>
          )}

          {result && <ResultCard result={result} />}
        </div>
      </div>
    </div>
  )
}
