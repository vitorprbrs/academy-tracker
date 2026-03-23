import { useState } from "react"
import { toast } from "sonner"
import { ArrowLeft, Pencil, Trash2, PlusCircle } from "lucide-react"
import { Bar, BarChart, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine, Cell } from "recharts"
import { api } from "@/lib/api"
import { gradeColor, STATUS_LABELS } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import SubjectModal from "@/components/SubjectModal"
import AutoInsight from "@/components/AutoInsight"

export default function SubjectDetail({ subject: s, navigate, onRefresh }) {
  const [editOpen, setEditOpen] = useState(false)
  const [adding, setAdding] = useState(false)
  const [newA, setNewA] = useState({ name: "", weight: "1", max_score: "10" })
  const isSimple = s.calc_type === "simple"

  async function handleScore(id, value) {
    const score = value === "" ? null : parseFloat(value)
    if (value !== "" && isNaN(score)) return
    try { await api.updateAssessment(id, { score }); await onRefresh() }
    catch (err) { toast.error(err.message) }
  }

  async function handleDeleteAssessment(id) {
    if (!confirm("Remover esta avaliação?")) return
    try { await api.deleteAssessment(id); toast.success("Removida."); onRefresh() }
    catch (err) { toast.error(err.message) }
  }

  async function handleDeleteSubject() {
    if (!confirm(`Excluir "${s.name}"?`)) return
    try { await api.deleteSubject(s.id); toast.success("Excluída."); navigate("dashboard"); onRefresh() }
    catch (err) { toast.error(err.message) }
  }

  async function handleAddAssessment(e) {
    e.preventDefault()
    if (!newA.name.trim()) return
    try {
      await api.createAssessment(s.id, {
        name: newA.name,
        weight: isSimple ? 1 : (parseFloat(newA.weight) || 1),
        max_score: parseFloat(newA.max_score) || 10,
      })
      toast.success("Adicionada!"); setNewA({ name:"",weight:"1",max_score:"10" }); setAdding(false); onRefresh()
    } catch (err) { toast.error(err.message) }
  }

  const statColor = gradeColor(s.current_average, s.passing_grade)
  const chartData = s.assessments.map(a => ({ name: a.name.length>10?a.name.slice(0,9)+"…":a.name, nota: a.score??null, max: a.max_score }))

  return (
    <div className="animate-fade-in">
      <Button variant="ghost" size="sm" className="mb-5 -ml-1" onClick={() => navigate("dashboard")}><ArrowLeft className="w-4 h-4" /> Voltar</Button>

      <div className="flex items-start gap-4 mb-6">
        <div className="w-1 h-14 rounded-full shrink-0 mt-0.5" style={{ background: s.color }} />
        <div className="flex-1">
          <h1 className="font-display text-[26px] font-extrabold leading-tight">{s.name}</h1>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            {s.semester && <span className="text-xs text-muted-foreground">{s.semester} ·</span>}
            <span className="text-xs text-muted-foreground">Aprovação: {s.passing_grade.toFixed(1)}</span>
            <span className="text-[10px] text-muted-foreground/50 font-mono bg-muted/40 px-1.5 py-0.5 rounded">
              {isSimple ? "Média Simples" : "Média Ponderada"}
            </span>
            <Badge variant={s.status}>{STATUS_LABELS[s.status]}</Badge>
          </div>
        </div>
        <div className="flex gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}><Pencil className="w-3.5 h-3.5" /> Editar</Button>
          <Button variant="destructive" size="sm" onClick={handleDeleteSubject}><Trash2 className="w-3.5 h-3.5" /></Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-5">
        {[
          { label: "Média Atual",      value: s.current_average, note: `${s.assessments.filter(a=>a.score!==null).length}/${s.assessments.length} realizadas`, color: statColor },
          { label: "Melhor Projeção",  value: s.best_projection, note: "se tirar máximo nas restantes",         color: "hsl(var(--sky))" },
          { label: "Mínimo p/ Passar", value: s.min_needed,      note: "média necessária nas pendentes",        color: "hsl(var(--gold))" },
        ].map(({ label, value, note, color }) => (
          <Card key={label}><CardContent className="p-5">
            <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">{label}</div>
            <div className="font-mono text-[30px] font-semibold leading-none" style={{ color }}>{value!=null?value.toFixed(2):"—"}</div>
            <div className="text-[11px] text-muted-foreground/60 mt-1.5">{note}</div>
          </CardContent></Card>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Notas por Avaliação</CardTitle></CardHeader>
          <CardContent>
            {s.assessments.length === 0 ? <p className="text-sm text-muted-foreground/50 py-10 text-center">Nenhuma avaliação.</p>
              : <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={chartData} barCategoryGap="30%">
                    <XAxis dataKey="name" tick={{ fill:"hsl(var(--muted-foreground))",fontSize:11 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0,10]} tick={{ fill:"hsl(var(--muted-foreground))",fontSize:10,fontFamily:"JetBrains Mono" }} axisLine={false} tickLine={false} width={24} />
                    <Tooltip contentStyle={{ background:"hsl(var(--card))",border:"1px solid hsl(var(--border))",borderRadius:8,fontSize:12 }} formatter={v=>v!==null?v.toFixed(1):"Pendente"} />
                    <ReferenceLine y={s.passing_grade} stroke="hsl(var(--destructive)/0.5)" strokeDasharray="4 3" />
                    <Bar dataKey="nota" radius={[5,5,0,0]} maxBarSize={48}>
                      {chartData.map((entry,i) => <Cell key={i} fill={entry.nota===null?"hsl(var(--muted)/0.5)":entry.nota>=s.passing_grade?"hsl(var(--emerald)/0.7)":"hsl(var(--destructive)/0.7)"} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2 flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Avaliações</CardTitle>
            <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => setAdding(true)}><PlusCircle className="w-3 h-3" /> Adicionar</Button>
          </CardHeader>
          <CardContent className="pt-0">
            <table className="w-full">
              <thead>
                <tr>
                  {["Nome", ...(isSimple ? [] : ["Peso"]), "Nota","Máx",""].map(h=>(
                    <th key={h} className="text-left text-[10px] font-semibold uppercase tracking-wide text-muted-foreground/60 pb-2 px-1">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {s.assessments.map(a => (
                  <tr key={a.id} className="border-t border-border/50 group">
                    <td className="px-1 py-2 text-[13px] font-semibold">{a.name}</td>
                    {!isSimple && <td className="px-1 py-2 text-[12px] font-mono text-muted-foreground">{a.weight}</td>}
                    <td className="px-1 py-2">
                      <Input type="number" min={0} max={a.max_score} step={0.1} defaultValue={a.score??""} placeholder="—"
                        className="h-7 w-16 text-xs font-mono px-2"
                        onBlur={e => handleScore(a.id, e.target.value)}
                        onKeyDown={e => e.key==="Enter" && e.currentTarget.blur()} />
                    </td>
                    <td className="px-1 py-2 text-[12px] font-mono text-muted-foreground">{a.max_score}</td>
                    <td className="px-1 py-2">
                      <button onClick={() => handleDeleteAssessment(a.id)} className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {adding && (
                  <tr className="border-t border-primary/30">
                    <td colSpan={isSimple ? 4 : 5} className="pt-2 pb-1">
                      <form onSubmit={handleAddAssessment} className="flex items-center gap-2">
                        <Input autoFocus className="h-7 text-xs flex-1" placeholder="Nome" value={newA.name} onChange={e=>setNewA(p=>({...p,name:e.target.value}))} />
                        {!isSimple && (
                          <Input className="h-7 text-xs w-14 font-mono" type="number" placeholder="Peso" value={newA.weight} onChange={e=>setNewA(p=>({...p,weight:e.target.value}))} />
                        )}
                        <Input className="h-7 text-xs w-14 font-mono" type="number" placeholder="Máx" value={newA.max_score} onChange={e=>setNewA(p=>({...p,max_score:e.target.value}))} />
                        <Button size="sm" type="submit" className="h-7 text-xs px-2">Ok</Button>
                        <Button size="sm" type="button" variant="ghost" className="h-7 text-xs px-2" onClick={() => setAdding(false)}>✕</Button>
                      </form>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>

      <AutoInsight streamUrl={`/api/insights/subject/${s.id}/stream`} />

      <SubjectModal open={editOpen} subject={s} onClose={() => setEditOpen(false)} onSaved={() => { setEditOpen(false); onRefresh() }} />
    </div>
  )
}
