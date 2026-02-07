import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  HeartPulse,
  ShieldCheck,
  MapPin,
  Clock,
  DollarSign,
  PhoneCall,
  Download,
  Share2,
  RefreshCcw,
} from 'lucide-react'
import '../styles/triage-results.css'
import { useTranslation } from 'react-i18next'
import MedicationChecker from '../components/MedicationChecker'

const urgencyConfig = {
  emergency: {
    label: 'Emergency',
    action: 'Visit ER Now',
    color: '#EF4444',
    icon: AlertTriangle,
    pulse: true,
  },
  urgent: {
    label: 'Urgent',
    action: 'See Doctor Today',
    color: '#F59E0B',
    icon: HeartPulse,
  },
  routine: {
    label: 'Routine',
    action: 'Schedule Appointment',
    color: '#F59E0B',
    icon: ShieldCheck,
  },
  selfcare: {
    label: 'Self-care',
    action: 'Self Care at Home',
    color: '#22C55E',
    icon: ShieldCheck,
  },
}

const TriageResults = ({ urgency = 'urgent' }) => {
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const stored = localStorage.getItem('triage_result')
  const apiResult = stored ? JSON.parse(stored) : null
  const normalizedUrgency = apiResult?.urgency_level
    ? apiResult.urgency_level.toLowerCase()
    : urgency
  const config = useMemo(
    () => urgencyConfig[normalizedUrgency] || urgencyConfig.urgent,
    [normalizedUrgency],
  )
  const Icon = config.icon
  const confidence = apiResult?.confidence_score
    ? Math.round(apiResult.confidence_score * 100)
    : 82
  const reasoning = apiResult?.reasoning
  const redFlags = apiResult?.red_flags || []
  const cost = apiResult?.cost_estimate_inr
  const storedFacility = localStorage.getItem('selected_facility')
  const selectedFacility = storedFacility ? JSON.parse(storedFacility) : null
  const currentMeds = apiResult?.current_medications || []
  const recommendedMed = apiResult?.recommended_medication || ''
  const [ttsLoading, setTtsLoading] = useState(false)

  const handleListen = async () => {
    if (!reasoning) return
    setTtsLoading(true)
    try {
      const formData = new FormData()
      formData.append('text', reasoning)
      formData.append('language', i18n.language || 'en')
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'}/i18n/text-to-speech`,
        { method: 'POST', body: formData },
      )
      if (!response.ok) throw new Error('tts')
      const blob = await response.blob()
      const audioUrl = URL.createObjectURL(blob)
      const audio = new Audio(audioUrl)
      audio.play()
    } finally {
      setTtsLoading(false)
    }
  }

  return (
    <div className="results-page">
      <motion.section
        className={`results-hero ${config.pulse ? 'pulse' : ''}`}
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="results-badge" style={{ background: config.color }}>
          <Icon size={20} />
          <span>{config.label}</span>
        </div>
        <h1>{config.action}</h1>
        <p>
          {reasoning ||
            'Based on your symptoms, this is the safest next step. If anything worsens, seek immediate care.'}
        </p>
      </motion.section>

      <section className="results-grid">
        <div className="card reasoning-card">
          <h2>Why this recommendation</h2>
          <ul>
            {redFlags.length > 0 ? (
              redFlags.map((flag) => <li key={flag}>{flag}</li>)
            ) : (
              <>
                <li>Symptoms reviewed with clinical safety rules</li>
                <li>Follow-up answers included in the assessment</li>
                <li>Severity and duration considered</li>
              </>
            )}
          </ul>
          <div className="confidence">
            <span>Confidence</span>
            <div className="confidence-bar">
              <span style={{ width: `${confidence}%` }} />
            </div>
            <strong>{confidence}%</strong>
          </div>
          <p className="muted">
            {reasoning || 'We ruled out immediate red flags based on your answers.'}
          </p>
        </div>

        <div className="card pathway-card">
          <h2>Care pathway</h2>
          <div className="path-item">
            <MapPin size={18} />
            <div>
              <p className="title">Nearest Facility</p>
              {selectedFacility ? (
                <p className="muted">
                  {selectedFacility.name} -{' '}
                  {selectedFacility.distance?.toFixed(1)} km away
                </p>
              ) : (
                <p className="muted">Pick a facility to see distance.</p>
              )}
              <button
                className="btn btn-outline"
                type="button"
                onClick={() => navigate('/facilities')}
              >
                View Nearby Facilities
              </button>
            </div>
          </div>
          {selectedFacility && (
            <div className="path-item">
              <PhoneCall size={18} />
              <div>
                <p className="title">Selected Facility</p>
                <p className="muted">{selectedFacility.type}</p>
                <p className="muted">{selectedFacility.phone}</p>
                <div className="results-actions" style={{ marginTop: '8px' }}>
                  <button
                    className="btn btn-outline"
                    type="button"
                    onClick={() => window.open(selectedFacility.directionsUrl, '_blank', 'noopener,noreferrer')}
                  >
                    Get Directions
                  </button>
                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={() => (window.location.href = selectedFacility.callUrl)}
                  >
                    Call Now
                  </button>
                </div>
              </div>
            </div>
          )}
          <div className="path-item">
            <Clock size={18} />
            <div>
              <p className="title">Estimated Wait Time</p>
              <p className="muted">
                {selectedFacility?.waitLabel || '25 - 40 minutes'}
              </p>
            </div>
          </div>
          <div className="path-item">
            <DollarSign size={18} />
            <div>
              <p className="title">Estimated Cost</p>
              <p className="muted">
                {cost
                  ? `INR ${cost.min_inr} - INR ${cost.max_inr} · ${cost.note}${
                      cost.facility_type ? ` (${cost.facility_type})` : ''
                    }`
                  : 'INR 300 - INR 1500 (typical outpatient visit)'}
              </p>
            </div>
          </div>
        </div>

        <div className="card warning-card">
          <h2>Seek immediate care if:</h2>
          <ul>
            <li>Severe chest pain</li>
            <li>Confusion or fainting</li>
            <li>Difficulty breathing</li>
            <li>Blue lips or face</li>
          </ul>
          <p className="muted">Follow up within 24 hours if symptoms persist.</p>
        </div>
      </section>

      <section className="results-actions">
        <button className="btn btn-outline" type="button">
          <Download size={18} />
          Save Results
        </button>
        <button className="btn btn-outline" type="button" onClick={handleListen}>
          {ttsLoading ? 'Loading...' : t('listen_result')}
        </button>
        <button className="btn btn-outline" type="button">
          <Share2 size={18} />
          Share with Doctor
        </button>
        {normalizedUrgency === 'emergency' && (
          <button className="btn btn-primary" type="button">
            <PhoneCall size={18} />
            Call Ambulance
          </button>
        )}
        <button className="btn btn-primary" type="button">
          <RefreshCcw size={18} />
          Start Over
        </button>
      </section>

      <section className="results-grid">
        <div className="card reasoning-card">
          <h2>Medication interaction check</h2>
          <MedicationChecker
            recommendedMed={recommendedMed}
            currentMeds={currentMeds}
          />
          {!recommendedMed && (
            <p className="muted">
              Add a recommended medicine to run interaction checks.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}

export default TriageResults
