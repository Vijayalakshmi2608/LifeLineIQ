import { useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Camera,
  UploadCloud,
  RotateCcw,
  ZoomIn,
  ShieldCheck,
} from 'lucide-react'
import '../styles/visual-triage.css'

const severityColor = {
  low: '#22C55E',
  medium: '#F59E0B',
  high: '#EF4444',
}

const VisualTriage = () => {
  const [image, setImage] = useState(null)
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [consent, setConsent] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')
  const uploadRef = useRef(null)
  const captureRef = useRef(null)

  const apiBase = useMemo(() => {
    return import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
  }, [])

  const handleFile = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setFile(file)
    const reader = new FileReader()
    reader.onload = () => setImage(reader.result)
    reader.readAsDataURL(file)
  }

  const handleAnalyze = async () => {
    if (!file || !consent) return
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${apiBase}/triage/visual`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        throw new Error('Analysis failed')
      }
      const data = await response.json()
      setResults(data.findings || [])
    } catch {
      setError('Image analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setImage(null)
    setFile(null)
    setLoading(false)
    setResults([])
  }

  return (
    <div className="visual-triage">
      <div className="visual-header">
        <div>
          <h2>Visual Symptom Analysis</h2>
          <p>
            Use your camera or upload a photo to help us assess visible symptoms.
          </p>
        </div>
        <ShieldCheck size={20} />
      </div>

      <div className="visual-grid">
        <div className="visual-upload card">
          <div className="visual-preview">
            {image ? (
              <img src={image} alt="Uploaded symptom" />
            ) : (
              <div className="preview-placeholder">
                <p>No image selected</p>
              </div>
            )}
          </div>

          <div className="visual-actions">
            <div className="file-action">
              <button className="btn btn-primary" type="button">
                <Camera size={18} />
                Capture
              </button>
              <input
                ref={captureRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFile}
                className="file-input-overlay"
              />
            </div>
            <div className="file-action">
              <button className="btn btn-outline" type="button">
                <UploadCloud size={18} />
                Upload
              </button>
              <input
                ref={uploadRef}
                type="file"
                accept="image/*"
                onChange={handleFile}
                className="file-input-overlay"
              />
            </div>
            <button className="btn btn-outline" onClick={handleReset} type="button">
              <RotateCcw size={18} />
              Retake
            </button>
          </div>

          <div className="visual-tools">
            <button className="icon-btn" type="button" aria-label="Zoom">
              <ZoomIn size={18} />
            </button>
            <button className="icon-btn" type="button" aria-label="Rotate">
              <RotateCcw size={18} />
            </button>
          </div>

          <div className="consent-row">
            <input
              id="consent"
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <label htmlFor="consent">
              I consent to image analysis. Images are deleted after analysis.
            </label>
          </div>

          <button
            className="btn btn-primary analyze-btn"
            type="button"
            onClick={handleAnalyze}
            disabled={!image || !consent || loading}
          >
            {loading ? 'Analyzing...' : 'Analyze Image'}
          </button>
        </div>

        <div className="visual-results card">
          <AnimatePresence>
            {loading ? (
              <motion.div
                className="visual-loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className="skeleton skeleton-bar" />
                <div className="skeleton skeleton-card" />
                <div className="skeleton skeleton-card" />
              </motion.div>
            ) : (
              <motion.div
                className="visual-results-inner"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h3>Analysis Results</h3>
                <p className="text-muted">
                  {results.length
                    ? 'Results generated from your image.'
                    : 'Results appear here after the image is analyzed.'}
                </p>
                {error && <p className="text-muted">{error}</p>}
                <div className="results-grid">
                  {results.map((result) => (
                    <div className="result-card" key={result.title}>
                      <div
                        className="result-indicator"
                        style={{ background: severityColor[result.severity] }}
                      />
                      <div>
                        <p className="result-title">{result.title}</p>
                        <p className="result-detail">{result.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="privacy-card">
                  <ShieldCheck size={18} />
                  <div>
                    <p className="result-title">Privacy Notice</p>
                    <p className="result-detail">
                      Images are processed securely and deleted after analysis.
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

export default VisualTriage
