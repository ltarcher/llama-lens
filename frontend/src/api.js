async function getJson(url) {
  const resp = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!resp.ok) throw new Error(`${url} → ${resp.status}`)
  return resp.json()
}

export const api = {
  hosts: () => getJson('/api/hosts'),
  overview: (id) => getJson(`/api/hosts/${encodeURIComponent(id)}/overview`),
  history: (id, window) => getJson(`/api/hosts/${encodeURIComponent(id)}/history?window=${window}`),
  events: (id, limit = 50) => getJson(`/api/hosts/${encodeURIComponent(id)}/events?limit=${limit}`)
}
