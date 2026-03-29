import { useState, useEffect, useCallback } from "react"
import { Toaster, toast } from "sonner"
import { api } from "@/lib/api"
import Sidebar from "@/components/Sidebar"
import Dashboard from "@/pages/Dashboard"
import SubjectDetail from "@/pages/SubjectDetail"
import CalendarPage from "@/pages/CalendarPage"

export default function App() {
  const [subjects, setSubjects] = useState([])
  const [events, setEvents] = useState([])
  const [view, setView] = useState("dashboard")
  const [activeSubjectId, setActiveSubjectId] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    try {
      const [s, e] = await Promise.all([api.getSubjects(), api.getEvents()])
      setSubjects(s)
      setEvents(e)
    } catch {
      toast.error("Erro ao carregar dados.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  function navigate(target, subjectId = null) {
    setView(target)
    if (subjectId != null) setActiveSubjectId(subjectId)
  }

  const activeSubject = subjects.find(s => s.id === activeSubjectId) ?? null

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground font-mono text-sm animate-pulse">carregando...</div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Toaster position="bottom-right" theme="dark"
        toastOptions={{ style: { background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", color: "hsl(var(--foreground))", fontFamily: "Plus Jakarta Sans, sans-serif", fontSize: "13px" } }}
      />
      <Sidebar subjects={subjects} view={view} activeSubjectId={activeSubjectId} navigate={navigate} />
      <main className="flex-1 overflow-y-auto p-7">
        {view === "dashboard" && <Dashboard subjects={subjects} events={events} navigate={navigate} onRefresh={loadData} />}
        {view === "subject" && activeSubject && <SubjectDetail subject={activeSubject} navigate={navigate} onRefresh={loadData} />}
        {view === "calendar" && <CalendarPage subjects={subjects} events={events} onRefresh={loadData} />}

      </main>
    </div>
  )
}
