import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) { return twMerge(clsx(inputs)) }

export const STATUS_LABELS = { approved: "Aprovado", passing: "Passando", pending: "Pendente", failing: "Reprovando", failed: "Reprovado" }

export function gradeColor(avg, passing) {
  if (avg == null) return "hsl(var(--muted-foreground))"
  if (avg >= passing) return "hsl(var(--emerald))"
  if (avg >= passing * 0.85) return "hsl(var(--gold))"
  return "hsl(var(--red))"
}

export const EVENT_TYPE_COLORS = { exam: "hsl(var(--red))", activity: "hsl(var(--sky))", deadline: "hsl(var(--orange))", other: "hsl(var(--primary))" }

export function daysUntil(dateStr) {
  const today = new Date(); today.setHours(0,0,0,0)
  return Math.round((new Date(dateStr + "T00:00:00") - today) / 86400000)
}

export function formatDate(dateStr) {
  const d = new Date(dateStr + "T00:00:00")
  return { day: String(d.getDate()).padStart(2,"0"), month: d.toLocaleString("pt-BR",{month:"short"}) }
}