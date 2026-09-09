const OFFLINE = 'Der Server ist nicht erreichbar. Läuft die Anwendung noch?'
const FALLBACK = 'Die Anfrage konnte nicht verarbeitet werden.'

async function send(url, options) {
  let response
  try {
    response = await fetch(url, options)
  } catch {
    throw new Error(OFFLINE)
  }
  if (response.ok) return response

  let message = FALLBACK
  try {
    const data = await response.json()
    if (data && data.message) message = data.message
  } catch {
    /* Antwort ohne JSON-Inhalt */
  }
  throw new Error(message)
}

function json(url, payload) {
  return send(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function parseCsv(file) {
  const body = new FormData()
  body.append('file', file)
  const response = await send('/api/csv/parse', { method: 'POST', body })
  return response.json()
}

export async function generateUsers(payload) {
  const response = await json('/api/generate', payload)
  return response.json()
}

export async function fetchVouchers(users) {
  const response = await json('/api/vouchers.pdf', { users })
  return response.blob()
}
