import { useEffect, useState } from 'react'
import '../styles/medication-checker.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

const severityMeta = {
  SEVERE: { icon: '🚨', className: 'severe' },
  MODERATE: { icon: '⚠️', className: 'moderate' },
  MINOR: { icon: 'ℹ️', className: 'minor' },
}

const MedicationChecker = ({ recommendedMed, currentMeds }) => {
  const [interactions, setInteractions] = useState([])
  const [unknown, setUnknown] = useState([])

  useEffect(() => {
    if (!recommendedMed) return
    const run = async () => {
      const res = await fetch(`${API_BASE}/medications/check-interactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current: currentMeds,
          recommended: recommendedMed,
          language: 'en',
        }),
      })
      const data = await res.json()
      setInteractions(data.interactions || [])
      setUnknown(data.unknown_medications || [])
    }
    run()
  }, [recommendedMed, currentMeds])

  if (!recommendedMed) return null

  if (interactions.length === 0) {
    return (
      <div className="safe-badge">
        ✅ No interactions found
        {unknown.length > 0 && (
          <span className="muted"> (unknown: {unknown.join(', ')})</span>
        )}
      </div>
    )
  }

  return (
    <div className="interactions-warning">
      {interactions.map((interaction, index) => {
        const meta = severityMeta[interaction.severity] || severityMeta.MINOR
        return (
          <div key={`${interaction.drug1}-${interaction.drug2}-${index}`} className={`interaction-alert ${meta.className}`}>
            <div className="alert-header">
              <span className="icon">{meta.icon}</span>
              <strong>{interaction.severity} INTERACTION</strong>
            </div>
            <p className="drugs">
              {interaction.drug1} + {interaction.drug2}
            </p>
            <p className="description">{interaction.description}</p>
            <div className="recommendation">
              <strong>Recommendation:</strong> {interaction.recommendation}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default MedicationChecker
