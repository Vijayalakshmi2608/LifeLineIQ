import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Camera, X, CheckCircle, AlertTriangle } from 'lucide-react'
import '../styles/visual-check.css'

const MAX_IMAGES = 3

const VisualCheck = () => {
  const navigate = useNavigate()
  const fileRef = useRef(null)
  const pasteRef = useRef(null)
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [quality, setQuality] = useState([])
  const [context, setContext] = useState({
    body_locations: [],
    duration: '1-2 days',
    associated_symptoms: [],
    patient_description: '',
    previous_treatment: '',
    allergies: '',
  })

  const apiBase = useMemo(
    () => import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000',
    [],
  )

  useEffect(() => {
    const handlePaste = (event) => {
      if (!event.clipboardData) return
      const files = Array.from(event.clipboardData.files || [])
      if (files.length === 0) return
      addFiles(files)
    }
    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [])

  const addFiles = (files) => {
    setError('')
    const allowed = ['image/jpeg', 'image/png', 'image/webp']
    const incoming = []
    files.forEach((file) => {
      if (!allowed.includes(file.type)) {
        setError('Only JPG, PNG, or WebP files are supported.')
        return
      }
      if (file.size > 5 * 1024 * 1024) {
        setError('Each image must be 5MB or smaller.')
        return
      }
      incoming.push({
        id: `${file.name}-${Date.now()}`,
        file,
        preview: URL.createObjectURL(file),
        name: file.name,
        size: Math.round(file.size / 1024),
      })
    })
    setImages((prev) => [...prev, ...incoming].slice(0, MAX_IMAGES))
  }

  const removeImage = (id) => {
    setImages((prev) => prev.filter((img) => img.id !== id))
  }

  const toggleListItem = (key, value) => {
    setContext((prev) => {
      const current = prev[key]
      const exists = current.includes(value)
      return {
        ...prev,
        [key]: exists ? current.filter((item) => item !== value) : [...current, value],
      }
    })
  }

  const handleAnalyze = async () => {
    setError('')
    if (images.length === 0) {
      setError('Please add at least one image.')
      return
    }
    setLoading(true)
    try {
      const formData = new FormData()
      images.forEach((img) => formData.append('files', img.file, img.name))
      formData.append('language', localStorage.getItem('preferred_language') || 'en')
      formData.append('body_locations', context.body_locations.join(','))
      formData.append('duration', context.duration)
      formData.append('associated_symptoms', context.associated_symptoms.join(','))
      formData.append('patient_description', context.patient_description)
      formData.append('previous_treatment', context.previous_treatment)
      formData.append('allergies', context.allergies)
      formData.append('patient_age', localStorage.getItem('patient_age') || '')
      formData.append('patient_gender', localStorage.getItem('patient_gender') || '')

      const response = await fetch(`${apiBase}/visual/analyze`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        throw new Error('Unable to analyze images right now.')
      }
      const data = await response.json()
      localStorage.setItem('visual_result', JSON.stringify(data))
      setQuality(data.quality || [])
      navigate('/visual-results')
    } catch (err) {
      setError(err.message || 'Unable to analyze images.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="visual-page">
      <header className="visual-header">
        <h1>Skin photo check</h1>
        <p className="muted">Upload up to 3 clear photos for fast guidance.</p>
      </header>

      <section className="visual-upload">
        <div className="upload-card">
          <div className="upload-actions">
            <button className="btn btn-primary" type="button" onClick={() => fileRef.current?.click()}>
              <Upload size={18} />
              Upload Photos
            </button>
            <button className="btn btn-outline" type="button" onClick={() => fileRef.current?.click()}>
              <Camera size={18} />
              Use Camera
            </button>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            capture="environment"
            style={{ display: 'none' }}
            onChange={(event) => {
              const files = Array.from(event.target.files || [])
              addFiles(files)
              event.target.value = ''
            }}
          />

          <div className="paste-zone" ref={pasteRef}>
            <p>Paste an image here (Ctrl+V)</p>
          </div>
        </div>

        <div className="preview-grid">
          {images.map((img) => (
            <div key={img.id} className="preview-card">
              <img src={img.preview} alt={img.name} />
              <div className="preview-meta">
                <span>{img.name}</span>
                <span>{img.size} KB</span>
              </div>
              <button className="icon-btn" type="button" onClick={() => removeImage(img.id)}>
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="visual-context">
        <h2>Context details</h2>
        <div className="context-grid">
          <div className="context-card">
            <h3>Body location</h3>
            {['face', 'neck', 'chest', 'back', 'arms', 'hands', 'legs', 'feet'].map((loc) => (
              <button
                key={loc}
                type="button"
                className={`pill ${context.body_locations.includes(loc) ? 'active' : ''}`}
                onClick={() => toggleListItem('body_locations', loc)}
              >
                {loc}
              </button>
            ))}
          </div>
          <div className="context-card">
            <h3>Duration</h3>
            {['today', '1-2 days', '3-7 days', '1-2 weeks', '2+ weeks', 'recurring'].map((dur) => (
              <button
                key={dur}
                type="button"
                className={`pill ${context.duration === dur ? 'active' : ''}`}
                onClick={() => setContext((prev) => ({ ...prev, duration: dur }))}
              >
                {dur}
              </button>
            ))}
          </div>
          <div className="context-card">
            <h3>Associated symptoms</h3>
            {[
              'itching',
              'pain',
              'burning',
              'swelling',
              'fever',
              'pus',
              'spreading',
              'worsening',
              'none',
            ].map((sym) => (
              <button
                key={sym}
                type="button"
                className={`pill ${context.associated_symptoms.includes(sym) ? 'active' : ''}`}
                onClick={() => toggleListItem('associated_symptoms', sym)}
              >
                {sym}
              </button>
            ))}
          </div>
          <div className="context-card">
            <h3>Description</h3>
            <textarea
              rows={4}
              value={context.patient_description}
              onChange={(event) => setContext((prev) => ({ ...prev, patient_description: event.target.value }))}
            />
          </div>
          <div className="context-card">
            <h3>Previous treatment</h3>
            <textarea
              rows={3}
              value={context.previous_treatment}
              onChange={(event) => setContext((prev) => ({ ...prev, previous_treatment: event.target.value }))}
            />
          </div>
          <div className="context-card">
            <h3>Allergies</h3>
            <input
              type="text"
              value={context.allergies}
              onChange={(event) => setContext((prev) => ({ ...prev, allergies: event.target.value }))}
            />
          </div>
        </div>
      </section>

      {error && (
        <div className="error-banner" role="alert">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="visual-actions">
        <button className="btn btn-primary" type="button" onClick={handleAnalyze} disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Photos'}
        </button>
        {quality.length > 0 && (
          <div className="quality-row">
            <CheckCircle size={18} />
            <span>Quality checked</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default VisualCheck
