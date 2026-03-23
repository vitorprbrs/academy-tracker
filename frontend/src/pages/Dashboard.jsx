import { useState } from "react"
import { PlusCircle } from "lucide-react"
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts"
import { gradeColor, STATUS_LABELS, daysUntil, formatDate } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import SubjectModal from "@/components/SubjectModal"
import AutoInsight from "@/components/AutoInsight"

export default function Dashboard({ subjects, events, navigate, onRefresh }) {
  const [modalOpen, setModalOpen] = useState(false)
  const today = new Date(); today.setHours(0,0,0,0)
  const upcoming = events.filter(e => new Date(e.date+"T00:00:00") >= today).sort((a,b) => a.date.localeCompare(b.date)).slice(0,5)
  const radarData = subjects.map(s => ({ name: s.name.length > 12 ? s.name.slice(0,11)+"…" : s.name, média: s.current_average ?? 0, mínimo: s.passing_grade }))

  return (
    <div className="animate-fade-in">
      <div className="flex items-start justify-between mb-7">
        <div>
          <h1 className="font-display text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">{subjects.length === 0 ? "Comece adicionando suas matérias" : `${subjects.length} matéria${subjects.length!==1?"s":""} cadastrada${subjects.length!==1?"s":""}`}</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => setModalOpen(true)}><PlusCircle className="w-3.5 h-3.5" /> Nova Matéria</Button>
      </div>

      {subjects.length === 0 ? (
        <Card className="mb-6"><CardContent className="py-16 text-center"><div className="text-4xl mb-3">📚</div><p className="text-sm text-muted-foreground">Nenhuma matéria cadastrada ainda.</p></CardContent></Card>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4 mb-6">
          {subjects.map(s => <SubjectCard key={s.id} subject={s} onClick={() => navigate("subject", s.id)} />)}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-4">
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Próximos Eventos</CardTitle></CardHeader>
          <CardContent className="pt-0">
            {upcoming.length === 0 ? <p className="text-sm text-muted-foreground/50">Nenhum evento próximo.</p>
              : <div className="space-y-2">{upcoming.map(e => <EventRow key={e.id} event={e} />)}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Panorama Geral</CardTitle></CardHeader>
          <CardContent className="pt-0">
            {subjects.length < 2 ? <p className="text-sm text-muted-foreground/50 py-10 text-center">Adicione 2+ matérias para ver o radar.</p>
              : <ResponsiveContainer width="100%" height={210}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
                    <Radar name="Média" dataKey="média" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.2} />
                    <Radar name="Mínimo" dataKey="mínimo" stroke="hsl(var(--destructive)/0.5)" fill="transparent" strokeDasharray="4 3" />
                    <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                  </RadarChart>
                </ResponsiveContainer>}
          </CardContent>
        </Card>
      </div>

      {subjects.length > 0 && (
        <AutoInsight streamUrl="/api/insights/auto/stream" />
      )}

      <SubjectModal open={modalOpen} onClose={() => setModalOpen(false)} onSaved={() => { setModalOpen(false); onRefresh() }} />
    </div>
  )
}

function SubjectCard({ subject: s, onClick }) {
  const avg = s.current_average
  const pct = avg !== null ? Math.min(100,(avg/Math.max(s.passing_grade*1.5,10))*100) : 0
  const markPct = Math.min(100,(s.passing_grade/Math.max(s.passing_grade*1.5,10))*100)
  const color = gradeColor(avg, s.passing_grade)
  const calcLabel = s.calc_type === "simple" ? "Simples" : "Ponderada"
  return (
    <div onClick={onClick} className="bg-card border border-border rounded-lg p-5 cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-[3px]" style={{ background: s.color }} />
      <div className="flex items-start justify-between mb-3 mt-0.5">
        <div className="flex-1 min-w-0">
          <div className="font-display font-bold text-[14px] truncate">{s.name}</div>
          <div className="flex items-center gap-1.5 mt-0.5">
            {s.semester && <span className="text-[11px] text-muted-foreground/60">{s.semester}</span>}
            <span className="text-[10px] text-muted-foreground/40 font-mono bg-muted/40 px-1.5 py-0.5 rounded">{calcLabel}</span>
          </div>
        </div>
        <Badge variant={s.status} className="ml-2 shrink-0">{STATUS_LABELS[s.status]}</Badge>
      </div>
      <div className="font-mono text-[32px] font-semibold leading-none mb-1" style={{ color }}>{avg !== null ? avg.toFixed(1) : "—"}</div>
      <div className="text-[11px] text-muted-foreground mb-3">média atual</div>
      <div className="relative h-1.5 bg-white/5 rounded-full overflow-visible mb-3">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
        <div className="absolute top-[-2px] bottom-[-2px] w-[2px] rounded bg-muted-foreground/30" style={{ left: `${markPct}%` }} />
      </div>
      <div className="flex gap-3 text-[11px] text-muted-foreground">
        <span>Proj: <span className="font-mono font-semibold text-foreground">{s.best_projection?.toFixed(1) ?? "—"}</span></span>
        <span>Mín: <span className="font-mono font-semibold text-foreground">{s.min_needed?.toFixed(1) ?? "—"}</span></span>
      </div>
    </div>
  )
}

function EventRow({ event: e }) {
  const d = formatDate(e.date)
  const days = daysUntil(e.date)
  const urgency = days === 0 ? "🚨 Hoje" : days === 1 ? "⚡ Amanhã" : days <= 7 ? `⚡ ${days}d` : `${days}d`
  const urgColor = days <= 1 ? "hsl(var(--red))" : days <= 7 ? "hsl(var(--orange))" : "hsl(var(--muted-foreground))"
  return (
    <div className="flex items-center gap-3 p-2.5 bg-background/40 rounded-lg border border-border/60">
      <div className="text-center w-9 shrink-0">
        <div className="font-mono text-[15px] font-semibold leading-none">{d.day}</div>
        <div className="text-[9px] uppercase text-muted-foreground tracking-wider mt-0.5">{d.month}</div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[12.5px] font-semibold truncate">{e.title}</div>
        {e.subject_name && <div className="text-[11px] text-muted-foreground truncate">{e.subject_name}</div>}
      </div>
      <span className="text-[11px] font-semibold shrink-0" style={{ color: urgColor }}>{urgency}</span>
    </div>
  )
}
