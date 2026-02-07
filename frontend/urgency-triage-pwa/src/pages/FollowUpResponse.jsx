import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import '../styles/followup.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

const FollowUpResponse = () => {
  const { token } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('')
  const [newSymptoms, setNewSymptoms] = useState('')
  const [needHelp, setNeedHelp] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/followups/${token}`)
        if (!res.ok) throw new Error('load')
        const payload = await res.json()
        setData(payload)
      } catch {
        setError('Unable to load follow-up details.')
      } finally {
        setLoading(false)
      }
    }
    load
  }, [token])

  const handleSubmit = async () => {
    if (!status) return
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/followups/${token}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          response_status: status,
          new_symptoms: status === 'worse' ? newSymptoms : null,
          need_help: status === 'worse' ? needHelp : null,
        }),
      })
      if (!res.ok) throw new Error('submit')
      setSubmitted(true)
      setError('')
    } catch {
      setError('Unable to submit response. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="followup-page">
        <div className="followup-card">Loading…</div>
      </div>
    )
  }

  return (
    <div className="followup-page">
      <div className="followup-card">
        <h1>Quick Check-in</h1>
        {error && <p className="error">{error}</p>}
        {data && (
          <>
            <p className="muted">{data.triage_reasoning}</p>
            <p className="muted">Care pathway: {data.care_pathway}</p>
          </>
        )}

        {!submitted ? (
          <>
            <div className="response-buttons">
              <button
                type="button"
                className={status === 'better' ? 'active' : ''}
                onClick={() => setStatus('better')}
              >
                Better
              </button>
              <button
                type="button"
                className={status === 'same' ? 'active' : ''}
                onClick={() => setStatus('same')}
              >
                Same
              </button>
              <button
                type="button"
                className={status === 'worse' ? 'active' : ''}
                onClick={() => setStatus('worse')}
              >
                Worse
              </button>
            </div>

            {status === 'worse' && (
              <div className="followup-extra">
                <label>
                  Any new symptoms?
                  <textarea
                    value={newSymptoms}
                    onChange={(event) => setNewSymptoms(event.target.value)}
                    placeholder="Describe new symptoms"
                  />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={needHelp}
                    onChange={(event) => setNeedHelp(event.target.checked)}
                  />
                  Need immediate help?
                </label>
              </div>
            )}

            <button className="submit-btn" type="button" onClick={handleSubmit}>
              Submit
            </button>
            <button
              className="link-btn"
              type="button"
              onClick={() => navigate('/symptom')}
            >
              Start new triage
            </button>
          </>
        ) : (
          <div className="success">
            Thanks for checking in. If symptoms worsen, seek immediate care.
          </div>
        )}
      </div>
    </div>
  )
}

export default FollowUpResponse
