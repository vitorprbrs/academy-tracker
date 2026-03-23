import { useState, useEffect } from "react"
import { toast } from "sonner"
import { api } from "@/lib/api"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const EMPTY = { title: "", date: "", event_type: "exam", subject_id: "", description: "" }

export default function EventModal({ open, onClose, onSaved, event = null, subjects = [], prefillDate = null }) {
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    if (event) setForm({ title: event.title, date: event.date, event_type: event.event_type, subject_id: String(event.subject_id ?? ""), description: event.description ?? "" })
    else setForm({ ...EMPTY, date: prefillDate ?? new Date().toISOString().slice(0,10) })
  }, [open, event, prefillDate])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  async function handleSubmit(e) {
    e.preventDefault(); setSaving(true)
    try {
      const payload = { title: form.title, date: form.date, event_type: form.event_type, subject_id: form.subject_id ? parseInt(form.subject_id) : null, description: form.description || null }
      if (event) { await api.updateEvent(event.id, payload); toast.success("Evento atualizado!") }
      else        { await api.createEvent(payload);          toast.success("Evento criado!") }
      onSaved()
    } catch (err) { toast.error(err.message) }
    finally { setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader><DialogTitle>{event ? "Editar Evento" : "Novo Evento"}</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="px-6 space-y-4 pb-2">
            <div className="space-y-1.5">
              <Label>Título</Label>
              <Input placeholder="ex: Prova 1 — Cálculo" value={form.title} onChange={e => set("title", e.target.value)} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Data</Label>
                <Input type="date" value={form.date} onChange={e => set("date", e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label>Tipo</Label>
                <Select value={form.event_type} onValueChange={v => set("event_type", v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="exam">Prova</SelectItem>
                    <SelectItem value="activity">Atividade</SelectItem>
                    <SelectItem value="deadline">Prazo</SelectItem>
                    <SelectItem value="other">Outro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Matéria (opcional)</Label>
              <Select value={form.subject_id} onValueChange={v => set("subject_id", v)}>
                <SelectTrigger><SelectValue placeholder="— Sem matéria —" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">— Sem matéria —</SelectItem>
                  {subjects.map(s => <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Descrição</Label>
              <Textarea placeholder="Detalhes..." value={form.description} onChange={e => set("description", e.target.value)} className="min-h-[64px]" />
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
