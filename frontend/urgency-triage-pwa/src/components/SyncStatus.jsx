import { useEffect, useState } from 'react'
import { CloudOff, CloudCheck, AlertTriangle } from 'lucide-react'
import '../styles/offline.css'

const SyncStatus = ({ initialPending = 3 }) => {
  const [pending, setPending] = useState(initialPending)
  const [syncing, setSyncing] = useState(false)
  const [conflict, setConflict] = useState(false)

  useEffect(() => {
    if (pending === 0) return
    setSyncing(true)
    const timer = setTimeout(() => {
      setSyncing(false)
      setPending(0)
      setConflict(false)
    }, 2200)
    return () => clearTimeout(timer)
  }, [pending])

  return (
    <div className="sync-card">
      <div className="sync-header">
        <div>
          <h3>Sync Status</h3>
          <p className="muted">
            {pending > 0
              ? `${pending} health checks waiting to sync`
              : 'All data is synced'}
          </p>
        </div>
        {syncing && <CloudOff size={20} />}
        {!syncing && !conflict && <CloudCheck size={20} />}
        {conflict && <AlertTriangle size={20} />}
      </div>

      {syncing && (
        <div className="sync-progress">
          <span />
        </div>
      )}

      {conflict && (
        <div className="sync-conflict">
          <p>Conflicting urgency levels detected.</p>
          <div className="conflict-actions">
            <button className="btn btn-outline" type="button">
              Keep most recent
            </button>
            <button className="btn btn-primary" type="button">
              Review conflict
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default SyncStatus
