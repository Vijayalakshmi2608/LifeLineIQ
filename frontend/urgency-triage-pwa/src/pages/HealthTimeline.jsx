import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown, ChevronUp, Download, Share2 } from 'lucide-react'
import '../styles/health-timeline.css'

const sessions = [
  {
    id: 1,
    date: 'Feb 4, 2026 · 9:20 AM',
    symptoms: 'Fever, cough',
    urgency: 'Urgent',
    trend: 'worsening',
    severity: 7,
    notes: 'Fever increasing over 3 days.',
  },
  {
    id: 2,
    date: 'Feb 2, 2026 · 8:15 PM',
    symptoms: 'Headache, fatigue',
    urgency: 'Routine',
    trend: 'stable',
    severity: 4,
    notes: 'Hydration advised.',
  },
]

const trendMeta = {
  worsening: { label: 'Worsening', symbol: '↑', color: '#EF4444' },
  stable: { label: 'Stable', symbol: '→', color: '#F59E0B' },
  improving: { label: 'Improving', symbol: '↓', color: '#22C55E' },
}

const HealthTimeline = () => {
  const [openId, setOpenId] = useState(sessions[0]?.id)

  return (
    <div className="timeline-page">
      <header className="timeline-header">
        <div>
          <h1>Health Timeline</h1>
          <p>Your recent health checks and trends in one place.</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-outline" type="button">
            <Download size={18} />
            Download History
          </button>
          <button className="btn btn-outline" type="button">
            <Share2 size={18} />
            Share with Provider
          </button>
        </div>
      </header>

      <section className="trend-card">
        <div>
          <h2>Your Health Trend</h2>
          <p className="muted">Your fever has been increasing for 3 days.</p>
        </div>
        <div className="trend-indicator">
          <span className="trend-arrow">↑</span>
          <div>
            <p className="trend-label">Worsening</p>
            <p className="muted">+18% change this week</p>
          </div>
        </div>
      </section>

      <section className="chart-card">
        <h3>Symptom Severity</h3>
        <div className="chart">
          {sessions.map((session) => (
            <div className="chart-bar" key={session.id}>
              <span
                style={{ height: `${session.severity * 10}%` }}
                aria-label={`Severity ${session.severity}`}
              />
              <p>{session.date.split('·')[0]}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="timeline-list">
        {sessions.map((session) => {
          const isOpen = openId === session.id
          const trend = trendMeta[session.trend]
          return (
            <motion.div
              className="timeline-item"
              key={session.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <button
                className="timeline-summary"
                type="button"
                onClick={() => setOpenId(isOpen ? null : session.id)}
              >
                <div>
                  <p className="timeline-date">{session.date}</p>
                  <p className="timeline-symptoms">{session.symptoms}</p>
                </div>
                <div className="timeline-meta">
                  <span className="urgency-pill">{session.urgency}</span>
                  <span className="trend-pill" style={{ color: trend.color }}>
                    {trend.symbol} {trend.label}
                  </span>
                  {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>
              </button>
              {isOpen && (
                <div className="timeline-details">
                  <p>{session.notes}</p>
                  <div className="detail-actions">
                    <button className="btn btn-outline" type="button">
                      View Results
                    </button>
                    <button className="btn btn-outline" type="button">
                      Add Notes
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          )
        })}
      </section>
    </div>
  )
}

export default HealthTimeline
