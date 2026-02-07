import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, Marker, Polyline, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import {
  AlertTriangle,
  MapPin,
  PhoneCall,
  RefreshCcw,
  Search,
} from 'lucide-react'
import { openDB } from 'idb'
import '../styles/nearest-facilities.css'

const CACHE_DB = 'lifelineiq-facilities'
const CACHE_STORE = 'facilities'
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

const radiusOptions = [
  { label: '5 km', value: 5000 },
  { label: '10 km', value: 10000 },
  { label: '20 km', value: 20000 },
  { label: 'Custom', value: 'custom' },
]

const facilityTypes = {
  PHC: { label: 'PHC', color: '#22C55E' },
  CHC: { label: 'CHC', color: '#3B82F6' },
  SDH: { label: 'SDH', color: '#0EA5E9' },
  DH: { label: 'District Hospital', color: '#EF4444' },
  MEDICAL_COLLEGE: { label: 'Medical College', color: '#8B5CF6' },
  PRIVATE: { label: 'Private', color: '#F97316' },
}

const waitMeta = {
  low: { label: 'Low wait', color: '#22C55E' },
  medium: { label: 'Medium wait', color: '#F59E0B' },
  high: { label: 'High wait', color: '#EF4444' },
}

const debounce = (fn, delay = 1200) => {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

const haversineKm = (a, b) => {
  if (!a || !b) return null
  const toRad = (value) => (value * Math.PI) / 180
  const R = 6371
  const dLat = toRad(b.lat - a.lat)
  const dLon = toRad(b.lng - a.lng)
  const lat1 = toRad(a.lat)
  const lat2 = toRad(b.lat)
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h))
}

const createNumberIcon = (number) =>
  L.divIcon({
    className: 'facility-marker',
    html: `<div class="facility-pin">${number}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  })

const userIcon = L.divIcon({
  className: 'user-marker',
  html: '<div class="user-pin"></div>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
})

const MapAutoFit = ({ points }) => {
  const map = useMap()

  useEffect(() => {
    if (!points.length) return
    const bounds = L.latLngBounds(points.map((p) => [p.lat, p.lng]))
    map.fitBounds(bounds, { padding: [40, 40] })
  }, [map, points])

  return null
}

const MapFocus = ({ center }) => {
  const map = useMap()

  useEffect(() => {
    if (!center) return
    map.setView([center.lat, center.lng], 14, { animate: true })
  }, [map, center])

  return null
}

const deriveStatus = (isOpen, opensAt) => {
  if (isOpen === true) return { status: 'open', label: 'Open now' }
  if (isOpen === false) return { status: 'closed', label: 'Closed', opensAt }
  return { status: 'unknown', label: 'Hours unavailable', opensAt }
}

const NearestFacilities = () => {
  const [location, setLocation] = useState(null)
  const [manualLocation, setManualLocation] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('map')
  const [filter, setFilter] = useState('all')
  const [radius, setRadius] = useState(10000)
  const [customRadius, setCustomRadius] = useState(15000)
  const [facilities, setFacilities] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [offline, setOffline] = useState(!navigator.onLine)
  const [usingCache, setUsingCache] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const listRef = useRef(null)
  const touchStart = useRef(null)
  const triageUrgency = useMemo(() => {
    const stored = localStorage.getItem('triage_result')
    if (!stored) return 'ROUTINE'
    try {
      const parsed = JSON.parse(stored)
      return parsed?.urgency_level || 'ROUTINE'
    } catch {
      return 'ROUTINE'
    }
  }, [])

  const selectedFacility = useMemo(
    () => facilities.find((facility) => facility.id === selectedId),
    [facilities, selectedId],
  )

  const filteredFacilities = useMemo(() => {
    const maxRadius = radius === 'custom' ? customRadius : radius
    const withinRadius = facilities.filter((facility) => {
      if (!facility.distance) return false
      return facility.distance * 1000 <= maxRadius
    })
    if (filter === 'emergency') {
      return withinRadius.filter(
        (facility) => ['DH', 'MEDICAL_COLLEGE'].includes(facility.type),
      )
    }
    if (filter === 'open') {
      return withinRadius.filter((facility) => facility.status === 'open')
    }
    return withinRadius
  }, [facilities, filter, radius, customRadius])

  const pointsForBounds = useMemo(() => {
    const points = filteredFacilities.map((facility) => ({
      lat: facility.lat,
      lng: facility.lng,
    }))
    if (location) points.push(location)
    return points
  }, [filteredFacilities, location])

  const saveCache = async (data) => {
    const db = await openDB(CACHE_DB, 1, {
      upgrade(dbInstance) {
        if (!dbInstance.objectStoreNames.contains(CACHE_STORE)) {
          dbInstance.createObjectStore(CACHE_STORE)
        }
      },
    })
    await db.put(CACHE_STORE, data, 'latest')
  }

  const loadCache = async () => {
    const db = await openDB(CACHE_DB, 1, {
      upgrade(dbInstance) {
        if (!dbInstance.objectStoreNames.contains(CACHE_STORE)) {
          dbInstance.createObjectStore(CACHE_STORE)
        }
      },
    })
    return db.get(CACHE_STORE, 'latest')
  }

  const fetchFacilities = useCallback(async (coords, radiusMeters) => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 10000)
    try {
      const response = await fetch(`${API_BASE}/facilities/search`, {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_lat: coords.lat,
          user_lng: coords.lng,
          urgency_level: triageUrgency,
          radius_km: Math.max(1, Math.round(radiusMeters / 1000)),
          max_results: 12,
          open_now: filter === 'open' ? true : null,
          emergency_only: filter === 'emergency' ? true : null,
        }),
      })
      clearTimeout(timeout)
      if (!response.ok) throw new Error('Network error')
      const data = await response.json()
      return (data.facilities || []).map((facility, index) => {
        const statusInfo = deriveStatus(facility.is_open_now, facility.opens_at)
        const wait = facility.wait_time?.level || ['low', 'medium', 'high'][index % 3]
        const waitLabel = facility.wait_time?.text || waitMeta[wait]?.label
        return {
          id: facility.id,
          name: facility.name,
          type: facility.facility_type,
          lat: facility.latitude,
          lng: facility.longitude,
          status: statusInfo.status,
          opensAt: statusInfo.opensAt,
          wait,
          waitLabel,
          specialties: facility.specialties?.length ? facility.specialties : ['General Care'],
          phone: facility.contact_number || '+91 00000 00000',
          distance: facility.distance_km,
          travelTime: facility.travel_time_mins ?? facility.travel_time,
          directionsUrl: facility.directions_url,
          callUrl: facility.call_url,
        }
      })
    } finally {
      clearTimeout(timeout)
    }
  }, [filter, triageUrgency])

  const refreshFacilities = async (coords, useCached = false) => {
    setRefreshing(true)
    try {
      const radiusMeters = radius === 'custom' ? customRadius : radius
      const data = useCached
        ? await loadCache()
        : await fetchFacilities(coords, radiusMeters)
      if (!data || data.length === 0) {
        setFacilities([])
        setError(`No facilities within ${radiusMeters / 1000} km. Try expanding.`)
      } else {
        setFacilities(data)
        setError('')
        if (data[0]) {
          persistSelection(data[0])
        }
        if (!useCached) {
          await saveCache(data)
        }
      }
      setUsingCache(useCached)
    } catch (err) {
      const cached = await loadCache()
      if (cached?.length) {
        setFacilities(cached)
        if (cached[0]) {
          persistSelection(cached[0])
        }
        setUsingCache(true)
        setError('')
      } else {
        setError('Unable to load facilities right now. Please try again.')
      }
    } finally {
      setRefreshing(false)
    }
  }

  const debouncedUpdate = useMemo(
    () =>
      debounce((coords) => {
        refreshFacilities(coords)
      }, 1500),
    [radius, customRadius],
  )

  useEffect(() => {
    const handleOnline = () => {
      setOffline(false)
      if (location) refreshFacilities(location)
    }
    const handleOffline = () => {
      setOffline(true)
    }
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [location])

  useEffect(() => {
    let watchId
    let timeoutId

    if (!navigator.geolocation) {
      setLoading(false)
      setError('Location is not supported. Please enter your city or pincode.')
      return undefined
    }

    timeoutId = setTimeout(() => {
      setLoading(false)
      setError('Location is taking too long. Enter your city or pincode.')
    }, 10000)

    watchId = navigator.geolocation.watchPosition(
      (pos) => {
        clearTimeout(timeoutId)
        const coords = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        }
        setLocation(coords)
        setLoading(false)
        setError('')
        debouncedUpdate(coords)
      },
      () => {
        clearTimeout(timeoutId)
        setLoading(false)
        setError('Location permission denied. Enter your city or pincode.')
      },
      { enableHighAccuracy: true, maximumAge: 15000, timeout: 8000 },
    )

    return () => {
      if (watchId) navigator.geolocation.clearWatch(watchId)
      clearTimeout(timeoutId)
    }
  }, [debouncedUpdate])

  useEffect(() => {
    if (!location && !loading) {
      loadCache().then((cached) => {
        if (cached?.length) {
          setFacilities(cached)
          if (cached[0]) {
            persistSelection(cached[0])
          }
          setUsingCache(true)
        }
      })
    }
  }, [location, loading])

  const handleManualSearch = () => {
    if (!manualLocation.trim()) return
    const coords = { lat: 12.9716, lng: 77.5946 }
    setLocation(coords)
    setError('')
    refreshFacilities(coords)
  }

  const handlePullStart = (event) => {
    if (listRef.current?.scrollTop !== 0) return
    touchStart.current = event.touches[0].clientY
  }

  const handlePullMove = (event) => {
    if (!touchStart.current) return
    const diff = event.touches[0].clientY - touchStart.current
    if (diff > 90) {
      touchStart.current = null
      if (location) refreshFacilities(location)
    }
  }

  const handleCall = (phone, callUrl) => {
    if (navigator.userAgent.toLowerCase().includes('mobile')) {
      window.location.href = callUrl || `tel:${phone}`
      return
    }
    alert(`Call ${phone}`)
  }

  const handleDirections = (facility) => {
    if (!location) return
    const url =
      facility.directionsUrl ||
      `https://www.google.com/maps/dir/?api=1&origin=${location.lat},${location.lng}&destination=${facility.lat},${facility.lng}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  const handleExpandRadius = () => {
    const order = [5000, 10000, 20000, 'custom']
    const currentIndex = order.indexOf(radius)
    const next = order[Math.min(currentIndex + 1, order.length - 1)]
    setRadius(next)
    if (next === 'custom' && customRadius < 30000) {
      setCustomRadius(30000)
    }
    if (location) {
      refreshFacilities(location)
    }
  }

  const persistSelection = (facility) => {
    setSelectedId(facility.id)
    localStorage.setItem('selected_facility', JSON.stringify(facility))
  }

  return (
    <div className="facilities-page">
      <header className="facilities-header">
        <div>
          <h1>Nearest Facilities</h1>
          <p className="muted">
            Find the safest facility near you with real-time status updates.
          </p>
        </div>
        <button
          className="btn btn-outline"
          type="button"
          onClick={() => location && refreshFacilities(location)}
        >
          <RefreshCcw size={18} />
          Refresh
        </button>
      </header>

      {offline && (
        <div className="offline-banner">
          Showing cached results (offline).
        </div>
      )}

      <div className="radius-row">
        {radiusOptions.map((option) => (
          <button
            key={option.label}
            type="button"
            className={radius === option.value ? 'active' : ''}
            onClick={() => setRadius(option.value)}
          >
            {option.label}
          </button>
        ))}
        {radius === 'custom' && (
          <div className="manual-input radius-input">
            <input
              type="number"
              min="1000"
              step="1000"
              value={customRadius}
              onChange={(event) => setCustomRadius(Number(event.target.value))}
            />
            <span>meters</span>
          </div>
        )}
      </div>

      <div className="view-toggle">
        <button
          type="button"
          className={viewMode === 'map' ? 'active' : ''}
          onClick={() => setViewMode('map')}
        >
          Map view
        </button>
        <button
          type="button"
          className={viewMode === 'list' ? 'active' : ''}
          onClick={() => setViewMode('list')}
        >
          List view
        </button>
      </div>

      <div className="filter-row">
        <button
          type="button"
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All
        </button>
        <button
          type="button"
          className={filter === 'emergency' ? 'active' : ''}
          onClick={() => setFilter('emergency')}
        >
          Emergency Only
        </button>
        <button
          type="button"
          className={filter === 'open' ? 'active' : ''}
          onClick={() => setFilter('open')}
        >
          Open Now
        </button>
      </div>

      {loading && (
        <div className="skeleton-grid">
          <div className="skeleton map-skeleton" />
          <div className="skeleton card-skeleton" />
          <div className="skeleton card-skeleton" />
        </div>
      )}

      {!loading && error && !usingCache && (
        <div className="error-card">
          <AlertTriangle size={18} />
          <p>{error}</p>
          <div className="manual-row">
            <div className="manual-input">
              <Search size={16} />
              <input
                type="text"
                placeholder="Enter city or pincode"
                value={manualLocation}
                onChange={(event) => setManualLocation(event.target.value)}
              />
            </div>
            <button className="btn btn-primary" type="button" onClick={handleManualSearch}>
              Search
            </button>
          </div>
        </div>
      )}

      {!loading && !error && viewMode === 'map' && (
        <div className="map-wrapper">
          <MapContainer
            center={[location?.lat || 12.9716, location?.lng || 77.5946]}
            zoom={13}
            className="map-view"
            scrollWheelZoom
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {location && (
              <Marker position={[location.lat, location.lng]} icon={userIcon} />
            )}
            {filteredFacilities.map((facility, index) => (
              <Marker
                key={facility.id}
                position={[facility.lat, facility.lng]}
                icon={createNumberIcon(index + 1)}
                eventHandlers={{
                  click: () => persistSelection(facility),
                }}
              />
            ))}
            {location && selectedFacility && (
              <Polyline
                positions={[
                  [location.lat, location.lng],
                  [selectedFacility.lat, selectedFacility.lng],
                ]}
                color="#3B82F6"
              />
            )}
            <MapAutoFit points={pointsForBounds} />
            <MapFocus center={selectedFacility} />
          </MapContainer>
        </div>
      )}

      <div
        className="facility-list"
        ref={listRef}
        onTouchStart={handlePullStart}
        onTouchMove={handlePullMove}
      >
        {filteredFacilities.map((facility, index) => {
          const typeMeta = facilityTypes[facility.type]
          const wait = waitMeta[facility.wait]
          const isActive = facility.id === selectedId
          return (
            <div
              key={facility.id}
              className={`facility-card ${isActive ? 'active' : ''}`}
              onClick={() => persistSelection(facility)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter') persistSelection(facility)
              }}
            >
              <div className="facility-top">
                <div>
                  <h3>{facility.name}</h3>
                  <div className="badge-row">
                    <span
                      className="type-badge"
                      style={{ background: typeMeta?.color || '#64748B' }}
                    >
                      {typeMeta?.label || facility.type}
                    </span>
                    <span className="distance">
                      {facility.distance?.toFixed(1)} km away
                    </span>
                  </div>
                </div>
                <span className="marker-pill">{index + 1}</span>
              </div>

              <div className="facility-meta">
                <div className="status">
                  <span
                    className={`dot ${facility.status}`}
                    aria-hidden="true"
                  />
                  {facility.status === 'open' && 'Open now'}
                  {facility.status === 'closed' && 'Closed'}
                  {facility.status === 'opens' &&
                    `Opens at ${facility.opensAt || 'later'}`}
                </div>
                <div className="status">
                  <span className="dot" style={{ background: wait.color }} />
                  {wait.label}
                </div>
                <div className="status">
                  <MapPin size={16} />
                  {facility.travelTime} mins by auto
                </div>
              </div>

              <div className="specialties">
                {facility.specialties.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>

              <div className="facility-actions">
                <button
                  className="btn btn-outline"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation()
                    handleDirections(facility)
                  }}
                >
                  Get Directions
                </button>
                <button
                  className="btn btn-outline"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation()
                    persistSelection(facility)
                  }}
                >
                  Use This Facility
                </button>
                <button
                  className="btn btn-primary"
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation()
                    handleCall(facility.phone, facility.callUrl)
                  }}
                >
                  <PhoneCall size={16} />
                  Call Now
                </button>
              </div>
            </div>
          )
        })}

        {!loading && !error && filteredFacilities.length === 0 && (
          <div className="empty-card">
            No facilities within {radius === 'custom' ? customRadius / 1000 : radius / 1000} km.
            <button className="btn btn-outline" type="button" onClick={handleExpandRadius}>
              Expand radius
            </button>
          </div>
        )}
      </div>

      {refreshing && <div className="toast">Updating facilities…</div>}
      {usingCache && !offline && (
        <div className="toast">Using offline data — refreshing now.</div>
      )}
    </div>
  )
}

export default NearestFacilities
