import { useEffect, useRef, useState } from "react"
import { marked } from "marked"
import { Sparkles, RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function AutoInsight({ streamUrl, className }) {
  const [output, setOutput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const outputRef = useRef(null)
  const abortRef = useRef(null)
  const requestIdRef = useRef(0)

  function formatLastUpdated(date) {
    return new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(date)
  }

  function parseSseLine(line) {
    if (!line.startsWith("data: ")) return null
    const data = line.slice(6).trim()
    if (!data || data === "[DONE]") return null
    try {
      return JSON.parse(data)
    } catch {
      return null
    }
  }

  async function fetchInsight() {
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId

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
        if (done) {
          const parsed = parseSseLine(rawBuffer)
          if (parsed && requestId === requestIdRef.current) {
            if (parsed.error) setError(parsed.error)
            if (parsed.text) {
              buffer += parsed.text
              setOutput(buffer)
              setLastUpdated(new Date())
            }
          }
          break
        }
        rawBuffer += decoder.decode(value, { stream: true })
        const lines = rawBuffer.split("\n"); rawBuffer = lines.pop()
        for (const line of lines) {
          const parsed = parseSseLine(line)
          if (!parsed) continue
          if (requestId !== requestIdRef.current) continue
          if (parsed.error) {
            setError(parsed.error)
          } else if (parsed.text) {
            buffer += parsed.text
            setOutput(buffer)
            setLastUpdated(new Date())
            if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") return
      if (requestId !== requestIdRef.current) return
      setError(err.message)
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    fetchInsight()
    return () => { if (abortRef.current) abortRef.current.abort() }
  }, [streamUrl])

  return (
    <Card className={`${className ?? ""} ${loading ? "ring-1 ring-primary/40" : ""}`}>
      <CardHeader className="pb-3 flex-row items-center justify-between">
        <div>
          <CardTitle className="text-xs font-semibold uppercase tracking-widest text-white/90 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-primary" /> Mentor IA
          </CardTitle>
          {lastUpdated && !loading && (
            <p className="mt-1 text-[10px] text-white/65">
              Atualizado às {formatLastUpdated(lastUpdated)}
            </p>
          )}
          {loading && (
            <p className="mt-1 text-[10px] text-white/65">
              Atualizando agora... clique no botao de recarregar para reiniciar se travar.
            </p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={fetchInsight}
          title={loading ? "Reiniciar geração" : "Gerar novamente"}
          aria-label={loading ? "Reiniciar geração" : "Gerar novamente"}
        >
          <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </CardHeader>
      {loading && (
        <div className="px-6 pb-2">
          <div className="insight-loading-rail" aria-hidden="true" />
          <div className="mt-2 flex items-center gap-2 text-[11px] text-white/80">
            <span className="insight-loading-dot" />
            <span>Gerando insight com base nos seus dados...</span>
          </div>
        </div>
      )}
      <CardContent ref={outputRef} className="pt-0 max-h-72 overflow-y-auto relative">
        {loading && (
          <div className="pointer-events-none absolute inset-0 insight-loading-overlay" aria-hidden="true" />
        )}
        {loading && !output && (
          <div className="flex items-center gap-2 text-xs text-white/80 py-4">
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
          <p className="text-xs text-white/70 italic">Nenhum insight gerado.</p>
        )}
      </CardContent>
    </Card>
  )
}
