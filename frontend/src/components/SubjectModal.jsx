import { useState, useEffect } from "react"
import { toast } from "sonner"
import { Trash2, Plus } from "lucide-react"
import { api } from "@/lib/api"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

const EMPTY = { name: "", semester: "", passing_grade: "6.0", color: "#7c8ef0", calc_type: "weighted" }

export default function SubjectModal({ open, onClose, onSaved, subject = null }) {
  const [form, setForm] = useState(EMPTY)
  const [rows, setRows] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    if (subject) {
      setForm({
        name: subject.name,
        semester: subject.semester ?? "",
        passing_grade: String(subject.passing_grade),
        color: subject.color,
        calc_type: subject.calc_type ?? "weighted",
      })
      setRows(subject.assessments.map(a => ({ name: a.name, weight: String(a.weight), max_score: String(a.max_score) })))
    } else {
      setForm(EMPTY); setRows([])
    }
  }, [open, subject])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const setRow = (i, k, v) => setRows(r => r.map((row, idx) => idx === i ? { ...row, [k]: v } : row))
  const isSimple = form.calc_type === "simple"

  async function handleSubmit(e) {
    e.preventDefault(); setSaving(true)
    try {
      const payload = {
        name: form.name,
        semester: form.semester || null,
        passing_grade: parseFloat(form.passing_grade) || 6.0,
        color: form.color,
        calc_type: form.calc_type,
        assessments: rows.filter(r => r.name.trim()).map(r => ({
          name: r.name,
          weight: isSimple ? 1 : (parseFloat(r.weight) || 1),
          max_score: parseFloat(r.max_score) || 10,
        })),
      }
      if (subject) { await api.updateSubject(subject.id, payload); toast.success("Matéria atualizada!") }
      else          { await api.createSubject(payload);             toast.success("Matéria criada!") }
      onSaved()
    } catch (err) { toast.error(err.message) }
    finally { setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader><DialogTitle>{subject ? "Editar Matéria" : "Nova Matéria"}</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="px-6 space-y-4 pb-2">
            <div className="space-y-1.5">
              <Label>Nome</Label>
              <Input placeholder="ex: Cálculo II" value={form.name} onChange={e => set("name", e.target.value)} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Semestre</Label>
                <Input placeholder="2024.2" value={form.semester} onChange={e => set("semester", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label>Nota p/ aprovação</Label>
                <Input type="number" min="0" max="10" step="0.1" value={form.passing_grade} onChange={e => set("passing_grade", e.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Tipo de cálculo</Label>
              <div className="flex gap-2">
                <CalcBtn active={!isSimple} onClick={() => set("calc_type", "weighted")} label="Média Ponderada" desc="cada nota tem peso" />
                <CalcBtn active={isSimple}  onClick={() => set("calc_type", "simple")}   label="Média Simples"   desc="todas as notas iguais" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Cor</Label>
              <div className="flex items-center gap-3">
                <input type="color" value={form.color} onChange={e => set("color", e.target.value)}
                  className="w-10 h-10 rounded-md border border-border bg-input cursor-pointer p-1" />
                <span className="text-xs text-muted-foreground font-mono">{form.color}</span>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Avaliações</Label>
                <Button type="button" variant="ghost" size="sm" className="h-6 text-xs"
                  onClick={() => setRows(r => [...r, { name: "", weight: "1", max_score: "10" }])}>
                  <Plus className="w-3 h-3" /> Adicionar
                </Button>
              </div>
              {rows.length > 0 && (
                <div className="space-y-2">
                  <div className={cn("grid gap-2 px-1", isSimple ? "grid-cols-[1fr_56px_28px]" : "grid-cols-[1fr_56px_56px_28px]")}>
                    {(isSimple ? ["Nome","Máx",""] : ["Nome","Peso","Máx",""]).map(h => (
                      <span key={h} className="text-[10px] text-muted-foreground/60">{h}</span>
                    ))}
                  </div>
                  {rows.map((row, i) => (
                    <div key={i} className={cn("grid gap-2 items-center", isSimple ? "grid-cols-[1fr_56px_28px]" : "grid-cols-[1fr_56px_56px_28px]")}>
                      <Input className="h-8 text-xs" placeholder="Prova 1" value={row.name} onChange={e => setRow(i,"name",e.target.value)} />
                      {!isSimple && (
                        <Input className="h-8 text-xs font-mono" type="number" min="0.1" step="0.1" value={row.weight} onChange={e => setRow(i,"weight",e.target.value)} />
                      )}
                      <Input className="h-8 text-xs font-mono" type="number" min="1" step="0.5" value={row.max_score} onChange={e => setRow(i,"max_score",e.target.value)} />
                      <button type="button" onClick={() => setRows(r => r.filter((_,idx)=>idx!==i))} className="text-muted-foreground hover:text-destructive transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={saving}>{saving ? "Salvando..." : "Salvar"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function CalcBtn({ active, onClick, label, desc }) {
  return (
    <button type="button" onClick={onClick} className={cn(
      "flex-1 flex flex-col items-start px-3 py-2 rounded-lg border text-left transition-all duration-150",
      active ? "border-primary bg-primary/10" : "border-border text-muted-foreground hover:text-foreground"
    )}>
      <span className={cn("text-xs font-semibold", active && "text-primary")}>{label}</span>
      <span className="text-[10px] text-muted-foreground/60 mt-0.5">{desc}</span>
    </button>
  )
}
