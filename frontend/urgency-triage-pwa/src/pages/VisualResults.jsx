import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  ShieldCheck,
  Clock,
  Home,
  Download,
  Share2,
} from 'lucide-react'
import '../styles/visual-check.css'

const urgencyMeta = {
  EMERGENCY: { label: 'Emergency', color: 'danger', icon: AlertTriangle, action: 'Call Ambulance Now' },
  URGENT: { label: 'Urgent', color: 'warn', icon: Clock, action: 'Find Nearest Hospital' },
  ROUTINE: { label: 'Routine', color: 'info', icon: ShieldCheck, action: 'Book Doctor Appointment' },
  SELF_CARE: { label: 'Self-care', color: 'safe', icon: Home, action: 'View Care Instructions' },
}

const VisualResults = () => {
  const navigate = useNavigate()
  const stored = localStorage.getItem('visual_result')
  const result = stored ? JSON.parse(stored) : null
  const meta = useMemo(() => urgencyMeta[result?.urgency_level] || urgencyMeta.ROUTINE, [result])
  const Icon = meta.icon

  if (!result) {
    return (
      <div className="visual-page">
        <p className="muted">No visual analysis found yet.</p>
        <button className="btn btn-primary" onClick={() => navigate('/visual-check')}>
          Start Visual Check
        </button>
      </div>
    )
  }

  return (
    <div className="visual-page">
      <div className={`urgency-badge ${meta.color}`}>
        <Icon size={20} />
        <span>{meta.label}</span>
      </div>
      <button className="btn btn-primary" onClick={() => navigate('/facilities')}>
        {meta.action}
      </button>

      <section className="result-card">
        <h2>Visual observations</h2>
        <ul>
          {result.observations?.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="result-card">
        <h2>Possible conditions</h2>
        {result.possible_conditions?.map((cond) => (
          <div key={cond.name} className="condition-card">
            <strong>{cond.name}</strong>
            <span className="muted">Likelihood: {cond.likelihood}</span>
            <p>{cond.reason}</p>
          </div>
        ))}
      </section>

      <section className="result-card">
        <h2>Red flags</h2>
        <div className="alert-box">
          {result.red_flags?.map((flag) => (
            <p key={flag}>• {flag}</p>
          ))}
        </div>
      </section>

      <section className="result-card">
        <h2>Immediate actions</h2>
        <ol>
          {result.immediate_actions?.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>

      <section className="result-card">
        <h2>Home care</h2>
        <ol>
          {result.home_care?.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>

      <section className="result-card">
        <h2>When to seek care</h2>
        <ol>
          {result.when_to_seek_care?.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>

      <section className="result-card">
        <h2>Medications to consider</h2>
        <ul>
          {result.medications?.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {result.specialist && <p>Suggested specialist: {result.specialist}</p>}
      </section>

      <section className="result-card">
        <h2>Limitations</h2>
        <p className="muted">{result.limitations}</p>
      </section>

      <div className="result-actions">
        <button className="btn btn-outline">
          <Download size={16} />
          Save
        </button>
        <button className="btn btn-outline">
          <Share2 size={16} />
          Share
        </button>
      </div>
    </div>
  )
}

export default VisualResults
