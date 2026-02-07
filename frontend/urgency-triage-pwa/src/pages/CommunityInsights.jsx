import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, MapPin, ShieldCheck } from 'lucide-react'
import '../styles/community-insights.css'

const mockStats = [
  { label: 'Total cases (7 days)', value: '132' },
  { label: 'Most common symptom', value: 'Fever + cough' },
  { label: 'Trend vs last week', value: '+12%' },
]

const CommunityInsights = ({ outbreakDetected = true }) => {
  const lastUpdated = useMemo(() => 'Updated 2 hours ago', [])

  return (
    <div className="community-page">
      <header className="community-header">
        <div>
          <h1>Community Health Insights</h1>
          <p className="muted">
            See anonymized trends around you to stay informed and prepared.
          </p>
        </div>
        <span className="updated-pill">{lastUpdated}</span>
      </header>

      {outbreakDetected && (
        <motion.section
          className="outbreak-banner"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <AlertTriangle size={22} />
          <div>
            <h2>Outbreak Alert</h2>
            <p>15 similar cases in your area in the past 48 hours.</p>
            <p className="muted">
              Public health recommendation: avoid crowded indoor spaces and
              monitor symptoms closely.
            </p>
          </div>
          <button className="btn btn-primary" type="button">
            Report to Health Officer
          </button>
        </motion.section>
      )}

      <section className="map-section">
        <div className="section-heading">
          <h2>Health Trends Map</h2>
          <p>
            Heatmap shows symptom clusters within 5 km of your location. Filter
            by symptom type.
          </p>
        </div>
        <div className="map-card card">
          <div className="map-placeholder">
            <MapPin size={20} />
            <p>Interactive heatmap</p>
          </div>
          <div className="map-filters">
            {['All', 'Fever', 'Cough', 'GI', 'Skin'].map((filter) => (
              <button key={filter} className="filter-pill" type="button">
                {filter}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="stats-section">
        {mockStats.map((stat) => (
          <div className="stat-card" key={stat.label}>
            <p className="stat-label">{stat.label}</p>
            <h3>{stat.value}</h3>
          </div>
        ))}
      </section>

      <section className="privacy-section card">
        <ShieldCheck size={20} />
        <div>
          <h3>Your privacy matters</h3>
          <p className="muted">
            All data is anonymized and aggregated. Your data helps keep the
            community safe.
          </p>
          <button className="btn btn-outline" type="button">
            Opt out of sharing
          </button>
        </div>
      </section>
    </div>
  )
}

export default CommunityInsights
