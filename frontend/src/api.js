const API_BASE = import.meta.env.VITE_API_BASE
if (!API_BASE) throw new Error('VITE_API_BASE is not set')
const API = `${API_BASE}/api`



/** Convert minutes-from-midnight to "HH:MM" */
export function minsToTime(m) {
  const h = Math.floor(m / 60)
  const mm = m % 60
  return `${String(h).padStart(2, '0')}:${String(mm).padStart(2, '0')}`
}

/** Convert "HH:MM" to minutes from midnight */
export function timeToMins(t) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

/** Current time as minutes from midnight */
export function getNowMins() {
  const d = new Date()
  return d.getHours() * 60 + d.getMinutes()
}

/** Clean program ID into human-readable title */
export function cleanTitle(id) {
  return (id || '').replace(/_/g, ' ')
}

/** Extract YouTube video ID from URL */
export function ytId(url) {
  try {
    const u = new URL(url)
    return u.searchParams.get('v') || url
  } catch {
    return url
  }
}

/** YouTube embed URL with autoplay (mute=1 required by browsers for autoplay to work) */
export function embedUrl(url) {
  return `https://www.youtube.com/embed/${ytId(url)}?autoplay=1&mute=1&rel=0&modestbranding=1&playsinline=1`
}

/** YouTube thumbnail URL */
export function thumbUrl(url) {
  return `https://img.youtube.com/vi/${ytId(url)}/mqdefault.jpg`
}

/** Fetch saved preferences from the backend */
export async function fetchPreferences() {
  const res = await fetch(`${API}/preferences`)
  return await res.json()
}

/** Save preferences to the backend */
export async function savePreferences(payload) {
  const res = await fetch(`${API}/preferences`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return res.ok
}

/** Generate schedule using current preferences payload */
export async function generateSchedule(payload) {
  const res = await fetch(`${API}/schedule/sync?probe=false&discover=true`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    let msg = 'Request failed'
    try {
      const err = await res.json()
      msg = err.detail || JSON.stringify(err)
    } catch {
      msg = await res.text()
    }
    throw new Error(msg)
  }
  return await res.json()
}

// add near other exported functions
export async function fetchStreams(probe = false) {
  const res = await fetch(`${API}/streams?probe=${probe}`);
  if (!res.ok) throw new Error('Failed to fetch streams');
  return await res.json();
}