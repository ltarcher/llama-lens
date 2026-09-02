async function getJson(url) {
  const resp = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!resp.ok) throw new Error(`${url} → ${resp.status}`)
  return resp.json()
}

async function postJson(url, body) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `${url} → ${resp.status}`)
  }
  return resp.json()
}

async function putJson(url, body) {
  const resp = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `${url} → ${resp.status}`)
  }
  return resp.json()
}

async function deleteJson(url) {
  const resp = await fetch(url, { method: 'DELETE' })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `${url} → ${resp.status}`)
  }
  return resp.json()
}

export const api = {
  hosts: () => getJson('/api/hosts'),
  overview: (id) => getJson(`/api/hosts/${encodeURIComponent(id)}/overview`),
  history: (id, window) => getJson(`/api/hosts/${encodeURIComponent(id)}/history?window=${window}`),
  events: (id, limit = 50) => getJson(`/api/hosts/${encodeURIComponent(id)}/events?limit=${limit}`),
  addHost: (data) => postJson('/api/hosts', data),
  updateHost: (id, data) => putJson(`/api/hosts/${encodeURIComponent(id)}`, data),
  deleteHost: (id) => deleteJson(`/api/hosts/${encodeURIComponent(id)}`)
}
