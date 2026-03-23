import { useEffect, useRef, useState } from "react"
import { marked } from "marked"
import { Sparkles, RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function AutoInsight({ streamUrl, className }) {
  const [output, setOutput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const outputRef = useRef(null)
  const abortRef = useRef(null)

  async function fetchInsight() {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setOutput("")
    setError(null)

    try {
      const resp = await fetch(streamUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
        signal: controller.signal,
      })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let rawBuffer = "", buffer = ""
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        rawBuffer += decoder.decode(value, { stream: true })
        const lines = rawBuffer.split("\n"); rawBuffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const data = line.slice(6).trim()
          if (data === "[DONE]") break
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              setError(parsed.error)
            } else if (parsed.text) {
              buffer += parsed.text
              setOutput(buffer)
              if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight
            }
          } catch {} // ignora linhas SSE malformadas
        }
      }
    } catch (err) {
      if (err.name === "AbortError") return
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInsight()
    return () => { if (abortRef.current) abortRef.current.abort() }
  }, [streamUrl])

  return (
    <Card className={className}>
      <CardHeader className="pb-3 flex-row items-center justify-between">
        <CardTitle className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-primary" /> Mentor IA
        </CardTitle>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={fetchInsight} disabled={loading} title="Gerar novamente">
          <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </CardHeader>
      <CardContent ref={outputRef} className="pt-0 max-h-72 overflow-y-auto">
        {loading && !output && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground/60 py-4">
            <span className="animate-pulse">●</span> Mentor analisando seus dados...
          </div>
        )}
        {error && (
          <p className="text-xs text-destructive">Erro: {error}</p>
        )}
        {(output || (loading && output)) && (
          <div
            className="markdown-output"
            dangerouslySetInnerHTML={{
              __html: marked.parse(output) + (loading ? '<span class="cursor-blink"></span>' : ""),
            }}
          />
        )}
        {!loading && !output && !error && (
          <p className="text-xs text-muted-foreground/40 italic">Nenhum insight gerado.</p>
        )}
      </CardContent>
    </Card>
  )
}
