import { useState } from "react"
import { toast } from "sonner"
import { PlusCircle } from "lucide-react"
import FullCalendar from "@fullcalendar/react"
import dayGridPlugin from "@fullcalendar/daygrid"
import listPlugin from "@fullcalendar/list"
import { api } from "@/lib/api"
import { EVENT_TYPE_COLORS } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import EventModal from "@/components/EventModal"

export default function CalendarPage({ subjects, events, onRefresh }) {
  const [modalOpen, setModalOpen] = useState(false)
  const [prefillDate, setPrefillDate] = useState(null)

  const fcEvents = events.map(e => ({
    id: String(e.id), title: e.title, start: e.date,
    backgroundColor: e.subject_color ?? EVENT_TYPE_COLORS[e.event_type] ?? "hsl(var(--primary))",
    borderColor: "transparent", textColor: "#fff",
  }))

  async function handleEventClick({ event }) {
    if (confirm(`Excluir "${event.title}"?`)) {
      try { await api.deleteEvent(parseInt(event.id)); toast.success("Evento excluído."); onRefresh() }
      catch (err) { toast.error(err.message) }
    }
  }

  return (
    <div className="animate-fade-in">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold">Calendário</h1>
          <p className="text-sm text-muted-foreground mt-1">Provas, trabalhos e prazos</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => { setPrefillDate(null); setModalOpen(true) }}>
          <PlusCircle className="w-3.5 h-3.5" /> Novo Evento
        </Button>
      </div>

      <div className="flex gap-4 mb-4 flex-wrap">
        {[["exam","Prova"],["activity","Atividade"],["deadline","Prazo"],["other","Outro"]].map(([k,l]) => (
          <div key={k} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: EVENT_TYPE_COLORS[k] }} />
            <span className="text-xs text-muted-foreground">{l}</span>
          </div>
        ))}
      </div>

      <Card><CardContent className="p-5">
        <FullCalendar
          plugins={[dayGridPlugin, listPlugin]}
          initialView="dayGridMonth"
          locale="pt-br"
          headerToolbar={{ left: "prev,next today", center: "title", right: "dayGridMonth,listWeek" }}
          events={fcEvents}
          height={520}
          eventClick={handleEventClick}
          dateClick={({ dateStr }) => { setPrefillDate(dateStr); setModalOpen(true) }}
          eventContent={({ event }) => (
            <div className="px-1.5 py-0.5 text-[11px] truncate font-medium">{event.title}</div>
          )}
        />
      </CardContent></Card>

      <EventModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSaved={() => { setModalOpen(false); onRefresh() }}
        subjects={subjects}
        prefillDate={prefillDate}
      />
    </div>
  )
}
