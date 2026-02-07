import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, Upload, X, ArrowLeft, AlertCircle, Activity, Plus } from 'lucide-react'
import '../styles/symptom-input.css'
import { useTranslation } from 'react-i18next'

const suggestedSymptoms = [
  'Fever',
  'Cough',
  'Headache',
  'Sore throat',
  'Nausea',
  'Shortness of breath',
]

const durations = ['Hours', '1-2 Days', '3-5 Days', '1+ Week']

const SymptomInput = () => {
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const [recording, setRecording] = useState(false)
  const [symptomText, setSymptomText] = useState('')
  const [chips, setChips] = useState([])
  const [severity, setSeverity] = useState(5)
  const [duration, setDuration] = useState(durations[1])
  const [answers, setAnswers] = useState({})
  const [followUpQuestions, setFollowUpQuestions] = useState([])
  const [questionsLoading, setQuestionsLoading] = useState(false)
  const [questionsError, setQuestionsError] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [patientAge, setPatientAge] = useState(
    Number(localStorage.getItem('patient_age')) || 30
  )
  const [patientGender, setPatientGender] = useState(
    localStorage.getItem('patient_gender') || 'male'
  )
  const [takingMeds, setTakingMeds] = useState(
    localStorage.getItem('taking_meds') === 'true'
  )
  const [medQuery, setMedQuery] = useState('')
  const [medSuggestions, setMedSuggestions] = useState([])
  const [medLoading, setMedLoading] = useState(false)
  const [medError, setMedError] = useState('')
  const [currentMeds, setCurrentMeds] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('current_medications') || '[]')
    } catch {
      return []
    }
  })
  const [recentMeds, setRecentMeds] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('recent_medications') || '[]')
    } catch {
      return []
    }
  })

  const selectedLanguage = useMemo(() => {
    return localStorage.getItem('preferred_language') || i18n.language || 'en'
  }, [i18n.language])

  const apiBase = useMemo(() => {
    return import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
  }, [])

  const handleAddChip = (value) => {
    const trimmed = value.trim()
    if (!trimmed || chips.includes(trimmed)) return
    setChips((prev) => [...prev, trimmed])
    setSymptomText('')
  }

  const handleRemoveChip = (value) => {
    setChips((prev) => prev.filter((chip) => chip !== value))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    setError('')
    if (chips.length === 0 && symptomText.trim().length < 3) {
      setError('Please describe at least one symptom to continue.')
      return
    }
    setLoading(true)
    const payload = {
      symptoms: [...chips, symptomText].filter(Boolean),
      patient_age: Number(patientAge) || 30,
      patient_gender: patientGender,
      language: selectedLanguage,
      follow_up_answers: answers,
      severity,
      duration_days: duration === 'Hours' ? 0 : duration === '1-2 Days' ? 2 : duration === '3-5 Days' ? 5 : 7,
      current_medications: takingMeds ? currentMeds : [],
    }
    fetch(`${apiBase}/triage/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Triage request failed')
        }
        return response.json()
      })
      .then((data) => {
        const next = {
          ...data,
          current_medications: takingMeds ? currentMeds : [],
        }
        localStorage.setItem('triage_result', JSON.stringify(next))
        navigate('/results')
      })
      .catch(() => {
        setError('Unable to complete triage right now.')
      })
      .finally(() => {
        setLoading(false)
      })
  }

  const handleVoiceInput = async () => {
    if (recording) return
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = async () => {
        setRecording(false)
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const formData = new FormData()
        formData.append('audio', blob, 'voice.webm')
        formData.append('language', selectedLanguage)
        try {
          const response = await fetch(`${apiBase}/i18n/voice-to-text`, {
            method: 'POST',
            body: formData,
          })
          if (!response.ok) {
            throw new Error('voice failed')
          }
          const data = await response.json()
          setSymptomText((prev) =>
            prev ? `${prev}, ${data.text}` : data.text || prev,
          )
        } catch {
          setError('Unable to transcribe audio. Please try again.')
        }
      }
      recorder.start()
      setRecording(true)
      setTimeout(() => {
        recorder.stop()
        stream.getTracks().forEach((track) => track.stop())
      }, 60000)
    } catch {
      setError('Microphone access denied.')
    }
  }

  useEffect(() => {
    localStorage.setItem('patient_age', String(patientAge))
    localStorage.setItem('patient_gender', patientGender)
    localStorage.setItem('taking_meds', String(takingMeds))
  }, [patientAge, patientGender])

  useEffect(() => {
    localStorage.setItem('current_medications', JSON.stringify(currentMeds))
  }, [currentMeds])

  useEffect(() => {
    localStorage.setItem('recent_medications', JSON.stringify(recentMeds))
  }, [recentMeds])

  useEffect(() => {
    if (!takingMeds) {
      setMedSuggestions([])
      setMedQuery('')
      setMedError('')
      return
    }
    if (!medQuery.trim()) {
      setMedSuggestions([])
      setMedError('')
      return
    }
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      setMedLoading(true)
      setMedError('')
      try {
        const response = await fetch(
          `${apiBase}/medications/search?q=${encodeURIComponent(medQuery.trim())}`,
          { signal: controller.signal },
        )
        if (!response.ok) {
          throw new Error('search failed')
        }
        const data = await response.json()
        setMedSuggestions(data.items || [])
      } catch (err) {
        if (err.name !== 'AbortError') {
          setMedError('Unable to load medication suggestions.')
        }
      } finally {
        setMedLoading(false)
      }
    }, 350)

    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [medQuery, takingMeds, apiBase])

  const addMedication = (name) => {
    const trimmed = String(name || '').trim()
    if (!trimmed) return
    if (currentMeds.includes(trimmed)) {
      setMedQuery('')
      setMedSuggestions([])
      return
    }
    setCurrentMeds((prev) => [...prev, trimmed])
    setRecentMeds((prev) => {
      const next = [trimmed, ...prev.filter((item) => item !== trimmed)]
      return next.slice(0, 6)
    })
    setMedQuery('')
    setMedSuggestions([])
  }

  const removeMedication = (name) => {
    setCurrentMeds((prev) => prev.filter((item) => item !== name))
  }

  const handleMedicationVoice = async () => {
    if (recording) return
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = async () => {
        setRecording(false)
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const formData = new FormData()
        formData.append('audio', blob, 'meds.webm')
        formData.append('language', selectedLanguage)
        try {
          const response = await fetch(`${apiBase}/i18n/voice-to-text`, {
            method: 'POST',
            body: formData,
          })
          if (!response.ok) {
            throw new Error('voice failed')
          }
          const data = await response.json()
          setMedQuery(data.text || '')
        } catch {
          setMedError('Unable to transcribe medication audio.')
        }
      }
      recorder.start()
      setRecording(true)
      setTimeout(() => {
        recorder.stop()
        stream.getTracks().forEach((track) => track.stop())
      }, 20000)
    } catch {
      setMedError('Microphone access denied.')
    }
  }

  useEffect(() => {
    const hasSymptoms = chips.length > 0 || symptomText.trim().length >= 3
    if (!hasSymptoms) {
      setFollowUpQuestions([])
      return
    }

    const controller = new AbortController()
    const timer = setTimeout(async () => {
      setQuestionsLoading(true)
      setQuestionsError('')
      try {
        const payload = {
          symptoms: [...chips, symptomText].filter(Boolean),
          patient_age: Number(patientAge) || 30,
          patient_gender: patientGender,
          language: selectedLanguage,
          previous_answers: answers,
        }
        const response = await fetch(`${apiBase}/triage/followup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: controller.signal,
        })
        if (!response.ok) {
          throw new Error('Follow-up request failed')
        }
        const data = await response.json()
        setFollowUpQuestions(data.questions || [])
      } catch (err) {
        if (err.name !== 'AbortError') {
          setQuestionsError('Unable to load follow-up questions.')
        }
      } finally {
        setQuestionsLoading(false)
      }
    }, 650)

    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [chips, symptomText, patientAge, patientGender, selectedLanguage, answers, apiBase])

  return (
    <div className="symptom-page">
      <header className="symptom-header">
        <button className="icon-btn" type="button" aria-label="Go back">
          <ArrowLeft size={18} />
        </button>
        <div>
          <p className="step-label">Step 1 of 3</p>
          <h1>Tell us what you're feeling</h1>
        </div>
      </header>

      <div className="progress-bar">
        <span style={{ width: '33%' }} />
      </div>

      <form className="symptom-form" onSubmit={handleSubmit}>
        <div className="input-card">
          <label>{t('describe_symptoms')}</label>
          <div className="profile-row">
            <div className="profile-field">
              <span className="text-muted">{t('age')}</span>
              <input
                type="number"
                min="0"
                max="120"
                value={patientAge}
                onChange={(event) => setPatientAge(event.target.value)}
              />
            </div>
            <div className="profile-field">
              <span className="text-muted">{t('gender')}</span>
              <select
                value={patientGender}
                onChange={(event) => setPatientGender(event.target.value)}
              >
                <option value="male">{t('male')}</option>
                <option value="female">{t('female')}</option>
                <option value="other">{t('other')}</option>
              </select>
            </div>
          </div>
        </div>

        <div className="input-card">
          <label htmlFor="symptom-text">{t('describe_symptoms')}</label>
          <div className="input-row">
            <input
              id="symptom-text"
              type="text"
              placeholder={t('symptom_input_placeholder')}
              value={symptomText}
              onChange={(event) => setSymptomText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  handleAddChip(symptomText)
                }
              }}
            />
            <button
              className="icon-btn"
              type="button"
              aria-label="Record voice input"
              onClick={handleVoiceInput}
            >
              <Mic size={18} />
            </button>
            <button
              className="icon-btn"
              type="button"
              aria-label="Upload symptom image"
            >
              <Upload size={18} />
            </button>
          </div>

          <div className="chip-row">
            {chips.map((chip) => (
              <span className="chip" key={chip}>
                {chip}
                <button
                  type="button"
                  aria-label={`Remove ${chip}`}
                  onClick={() => handleRemoveChip(chip)}
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>

          <div className="suggested-row">
            {suggestedSymptoms.map((symptom) => (
              <button
                type="button"
                key={symptom}
                className="suggested-chip"
                onClick={() => handleAddChip(symptom)}
              >
                {symptom}
              </button>
            ))}
          </div>
        </div>

        <div className="grid-two">
          <div className="input-card">
            <label htmlFor="severity">Severity (1-10)</label>
            <div className="severity-row">
              <input
                id="severity"
                type="range"
                min="1"
                max="10"
                value={severity}
                onChange={(event) => setSeverity(Number(event.target.value))}
              />
              <span className="severity-pill">{severity}</span>
            </div>
          </div>
          <div className="input-card">
            <label>Duration</label>
            <div className="duration-row">
              {durations.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`duration-pill ${
                    duration === option ? 'active' : ''
                  }`}
                  onClick={() => setDuration(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="input-card">
          <label>Are you currently taking any medications?</label>
          <div className="choice-row">
            {['Yes', 'No'].map((choice) => (
              <button
                key={choice}
                type="button"
                className={`choice-pill ${
                  (takingMeds && choice === 'Yes') || (!takingMeds && choice === 'No')
                    ? 'active'
                    : ''
                }`}
                onClick={() => setTakingMeds(choice === 'Yes')}
              >
                {choice}
              </button>
            ))}
          </div>

          {takingMeds && (
            <>
              <div className="med-input">
                <input
                  type="text"
                  placeholder="Type a medication name (e.g., Paracetamol)"
                  value={medQuery}
                  onChange={(event) => setMedQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault()
                      addMedication(medQuery)
                    }
                  }}
                />
                <button
                  className="icon-btn"
                  type="button"
                  aria-label="Record medication by voice"
                  onClick={handleMedicationVoice}
                >
                  <Mic size={18} />
                </button>
                <button
                  className="icon-btn"
                  type="button"
                  aria-label="Add medication"
                  onClick={() => addMedication(medQuery)}
                >
                  <Plus size={18} />
                </button>
              </div>

              {medLoading && <p className="text-muted">Searching medications...</p>}
              {medError && (
                <div className="input-card error-banner" role="alert">
                  <AlertCircle size={16} />
                  <span>{medError}</span>
                </div>
              )}

              {medSuggestions.length > 0 && (
                <div className="med-suggestions">
                  {medSuggestions.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className="suggested-chip"
                      onClick={() => addMedication(item.name)}
                    >
                      {item.name}
                      <span className="muted"> · {item.generic_name}</span>
                    </button>
                  ))}
                </div>
              )}

              {currentMeds.length > 0 && (
                <div className="chip-row">
                  {currentMeds.map((med) => (
                    <span className="chip" key={med}>
                      {med}
                      <button type="button" aria-label={`Remove ${med}`} onClick={() => removeMedication(med)}>
                        <X size={14} />
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {recentMeds.length > 0 && (
                <div className="suggested-row">
                  {recentMeds.map((med) => (
                    <button
                      type="button"
                      key={med}
                      className="suggested-chip"
                      onClick={() => addMedication(med)}
                    >
                      {med}
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <div className="input-card body-card">
          <div className="body-card-header">
            <div>
              <h3>Where does it hurt?</h3>
              <p className="text-muted">
                Tap a body area to highlight the pain location. (Optional)
              </p>
            </div>
            <Activity size={20} />
          </div>
          <div className="body-diagram">
            <div className="body-placeholder">Body diagram</div>
          </div>
        </div>

        <div className="followup-section">
          <div className="section-heading">
            <h2>{t('quick_followups')}</h2>
            <p>{t('followup_hint')}</p>
          </div>
          {(patientAge < 12 || patientAge >= 65) && (
            <div className="age-badge">
              {patientAge < 12 ? 'Child' : 'Elderly'} screening active
            </div>
          )}
          {questionsLoading && (
            <div className="input-card">
              <p className="text-muted">Generating personalized questions...</p>
            </div>
          )}
          {questionsError && (
            <div className="input-card error-banner" role="alert">
              <AlertCircle size={16} />
              <span>{questionsError}</span>
            </div>
          )}
          <AnimatePresence>
            {followUpQuestions.map((question) => (
              <motion.div
                key={question.id}
                className="input-card"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <p className="question-text">{question.question}</p>
                {question.type === 'yes_no' && (
                  <div className="choice-row">
                    {['Yes', 'No', 'Not sure'].map((choice) => (
                      <button
                        key={choice}
                        type="button"
                        className={`choice-pill ${
                          answers[question.id] === choice ? 'active' : ''
                        }`}
                        onClick={() =>
                          setAnswers((prev) => ({
                            ...prev,
                            [question.id]: choice,
                          }))
                        }
                      >
                        {choice}
                      </button>
                    ))}
                  </div>
                )}
                {question.type === 'choice' && (
                  <div className="choice-row">
                    {(question.options || []).map((option) => (
                      <button
                        key={option}
                        type="button"
                        className={`choice-pill ${
                          answers[question.id] === option ? 'active' : ''
                        }`}
                        onClick={() =>
                          setAnswers((prev) => ({
                            ...prev,
                            [question.id]: option,
                          }))
                        }
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                )}
                <button
                  type="button"
                  className="btn btn-outline skip-btn"
                  onClick={() =>
                    setAnswers((prev) => ({ ...prev, [question.id]: 'Skipped' }))
                  }
                >
                  Skip this
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {error && (
          <div className="error-banner" role="alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <div className="submit-row">
          <div className="text-muted">
            {t('language')}: <strong>{selectedLanguage.toUpperCase()}</strong>
          </div>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Analyzing...' : t('continue')}
          </button>
        </div>
      </form>
    </div>
  )
}

export default SymptomInput
