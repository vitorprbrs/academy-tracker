const BASE = "/api"

async function req(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const r = await fetch(BASE + path, opts)
  if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail || `HTTP ${r.status}`) }
  if (r.status === 204) return null
  return r.json()
}

export const api = {
  getSubjects:      ()         => req("GET",    "/subjects"),
  createSubject:    (data)     => req("POST",   "/subjects", data),
  updateSubject:    (id, data) => req("PUT",    `/subjects/${id}`, data),
  deleteSubject:    (id)       => req("DELETE", `/subjects/${id}`),
  createAssessment: (sid,data) => req("POST",   `/subjects/${sid}/assessments`, data),
  updateAssessment: (id, data) => req("PUT",    `/assessments/${id}`, data),
  deleteAssessment: (id)       => req("DELETE", `/assessments/${id}`),
  getEvents:        ()         => req("GET",    "/events"),
  createEvent:      (data)     => req("POST",   "/events", data),
  updateEvent:      (id, data) => req("PUT",    `/events/${id}`, data),
  deleteEvent:      (id)       => req("DELETE", `/events/${id}`),
}