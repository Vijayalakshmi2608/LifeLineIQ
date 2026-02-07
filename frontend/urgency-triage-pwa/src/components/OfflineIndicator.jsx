import { WifiOff } from 'lucide-react'
import '../styles/offline.css'

const OfflineIndicator = ({ offline = false }) => {
  if (!offline) return null

  return (
    <div className="offline-banner">
      <WifiOff size={16} />
      <span>You're offline — results will sync when connected.</span>
    </div>
  )
}

export default OfflineIndicator
