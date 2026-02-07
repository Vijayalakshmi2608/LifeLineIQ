import { Cloud, CheckCircle2 } from 'lucide-react'
import '../styles/offline.css'

const OfflineReady = () => {
  return (
    <div className="offline-page">
      <div className="offline-card">
        <div className="offline-icon">
          <Cloud size={32} />
        </div>
        <h1>Your app works offline!</h1>
        <p>
          LifeLineIQ caches essential screens so you can keep checking symptoms
          even without an internet connection.
        </p>
        <ul>
          <li>
            <CheckCircle2 size={16} /> Symptom input and results
          </li>
          <li>
            <CheckCircle2 size={16} /> Your recent health history
          </li>
          <li>
            <CheckCircle2 size={16} /> Emergency guidance
          </li>
        </ul>
        <button className="btn btn-primary" type="button">
          Got it
        </button>
      </div>
    </div>
  )
}

export default OfflineReady
