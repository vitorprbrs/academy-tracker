import { useState } from "react"
import { LayoutDashboard, CalendarDays, PlusCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import SubjectModal from "@/components/SubjectModal"

export default function Sidebar({ subjects, view, activeSubjectId, navigate }) {
  const [modalOpen, setModalOpen] = useState(false)

  return (
    <>
      <aside className="w-[230px] flex-shrink-0 border-r border-border bg-surface flex flex-col overflow-hidden">
        <div className="px-5 py-5 border-b border-border">
          <div className="font-display font-extrabold text-[17px] tracking-tight">⬡ Academic</div>
          <div className="text-[11px] text-foreground/75 mt-0.5 font-light">seu desempenho em foco</div>
        </div>

        <nav className="p-3 space-y-1">
          {[
            { id: "dashboard", label: "Dashboard",  icon: LayoutDashboard },
            { id: "calendar",  label: "Calendário", icon: CalendarDays },
          ].map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => navigate(id)}
              className={cn("w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-[13px] font-medium transition-all text-left",
                view === id && id !== "subject" ? "bg-primary/10 text-primary" : "text-foreground/85 hover:bg-secondary hover:text-foreground"
              )}>
              <Icon className="w-4 h-4 shrink-0" />{label}
            </button>
          ))}
        </nav>

        <Separator />

        <div className="flex-1 overflow-y-auto p-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-foreground/70 px-2 mb-2">Matérias</p>
          {subjects.length === 0
            ? <p className="text-[11px] text-foreground/60 px-2">Nenhuma matéria</p>
            : subjects.map(s => (
                <button key={s.id} onClick={() => navigate("subject", s.id)}
                  className={cn("w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[12.5px] transition-all text-left truncate",
                    view === "subject" && activeSubjectId === s.id ? "bg-secondary text-foreground" : "text-foreground/80 hover:bg-secondary hover:text-foreground"
                  )}>
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: s.color }} />
                  <span className="truncate">{s.name}</span>
                </button>
              ))
          }
        </div>

        <div className="p-3 border-t border-border">
          <Button className="w-full" size="sm" onClick={() => setModalOpen(true)}>
            <PlusCircle className="w-3.5 h-3.5" /> Nova Matéria
          </Button>
        </div>
      </aside>

      <SubjectModal open={modalOpen} onClose={() => setModalOpen(false)}
        onSaved={() => { setModalOpen(false); window.location.reload() }} />
    </>
  )
}
