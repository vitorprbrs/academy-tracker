import { useState, useRef } from "react"
import { Sparkles, Bot, Key, Eye, EyeOff } from "lucide-react"
import { marked } from "marked"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"

const OLLAMA_MODELS = ["llama3","llama3.2","qwen2.5","mistral","gemma2","phi3"]
const OPENAI_MODELS = [
  { value:"gpt-4o",        label:"GPT-4o (recomendado)" },
  { value:"gpt-4o-mini",   label:"GPT-4o Mini (mais barato)" },
  { value:"gpt-4-turbo",   label:"GPT-4 Turbo" },
  { value:"gpt-3.5-turbo", label:"GPT-3.5 Turbo (mais rápido)" },
]

export default function InsightsPage() {
  const [provider, setProvider] = useState("ollama")
  const [ollamaModel, setOllamaModel] = useState("llama3")
  const [customOllama, setCustomOllama] = useState("")
  const [openaiModel, setOpenaiModel] = useState("gpt-4o")
  const [apiKey, setApiKey] = useState("")
  const [showKey, setShowKey] = useState(false)
  const [focus, setFocus] = useState("")
  const [output, setOutput] = useState("")
  const [loading, setLoading] = useState(false)
  const outputRef = useRef(null)
  const isOllama = provider === "ollama"

  async function generateInsights() {
    setLoading(true); setOutput("")
    const model = isOllama ? (customOllama.trim() || ollamaModel) : openaiModel
    try {
      const resp = await fetch("/api/insights/stream", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, model, openai_api_key: isOllama ? null : apiKey, focus: focus || null }),
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
            if (parsed.error) throw new Error(parsed.error)
            if (parsed.text) { buffer += parsed.text; setOutput(buffer); if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight }
          } catch {}
        }
      }
    } catch (err) {
      setOutput(`**Erro:** ${err.message}\n\n${isOllama ? `Verifique se o Ollama está rodando:\n\`ollama serve\`` : "Verifique se a chave OpenAI é válida."}`)
    } finally { setLoading(false) }
  }

  return (
    <div className="animate-fade-in max-w-3xl">
      <div className="mb-7">
        <h1 className="font-display text-2xl font-bold flex items-center gap-2"><Sparkles className="w-6 h-6 text-primary" /> Insights IA</h1>
        <p className="text-sm text-muted-foreground mt-1">Análise do seu desempenho acadêmico com LLM</p>
      </div>

      <Card className="mb-5"><CardContent className="p-5 space-y-5">
        <div>
          <Label className="mb-2 block">Provedor</Label>
          <div className="flex gap-2">
            <ProviderBtn active={isOllama}  onClick={() => setProvider("ollama")}  icon="🦙" label="Ollama"  desc="Local · gratuito" />
            <ProviderBtn active={!isOllama} onClick={() => setProvider("openai")} icon="✦" label="OpenAI" desc="GPT-4o · pago" />
          </div>
        </div>

        {isOllama && (
          <div className="animate-fade-in space-y-3">
            <div>
              <Label className="mb-1.5 block">Modelo</Label>
              <div className="flex gap-2 flex-wrap">
                {OLLAMA_MODELS.map(m => (
                  <button key={m} onClick={() => { setOllamaModel(m); setCustomOllama("") }}
                    className={cn("px-3 py-1.5 rounded-md text-xs font-mono font-medium border transition-all",
                      ollamaModel===m&&!customOllama ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:text-foreground"
                    )}>{m}</button>
                ))}
              </div>
            </div>
            <div>
              <Label className="mb-1.5 block">Ou digite outro modelo</Label>
              <Input placeholder="ex: deepseek-r1, codellama..." value={customOllama} onChange={e=>setCustomOllama(e.target.value)} className="max-w-xs font-mono text-sm" />
            </div>
            <p className="text-[11px] text-muted-foreground/60">Certifique-se que o Ollama está rodando: <code className="bg-muted/50 px-1 rounded">ollama serve</code></p>
          </div>
        )}

        {!isOllama && (
          <div className="animate-fade-in space-y-3">
            <div>
              <Label className="mb-1.5 block">Modelo</Label>
              <Select value={openaiModel} onValueChange={setOpenaiModel}>
                <SelectTrigger className="max-w-xs"><SelectValue /></SelectTrigger>
                <SelectContent>{OPENAI_MODELS.map(m => <SelectItem key={m.value} value={m.value}><span className="font-mono text-xs">{m.label}</span></SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label className="mb-1.5 block"><Key className="w-3 h-3 inline mr-1" />Chave da API</Label>
              <div className="relative max-w-xs">
                <Input type={showKey?"text":"password"} placeholder="sk-..." value={apiKey} onChange={e=>setApiKey(e.target.value)} className="pr-10 font-mono text-sm" />
                <button type="button" onClick={() => setShowKey(v=>!v)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-[11px] text-muted-foreground/60 mt-1.5">A chave não é salva — é enviada apenas na requisição.</p>
            </div>
          </div>
        )}

        <div>
          <Label className="mb-1.5 block">Foco da análise <span className="text-muted-foreground/50 normal-case tracking-normal font-normal">(opcional)</span></Label>
          <Input placeholder="ex: priorizar matérias com prova essa semana..." value={focus} onChange={e=>setFocus(e.target.value)} />
        </div>

        <Button onClick={generateInsights} disabled={loading||(!isOllama&&!apiKey)} className="w-full">
          {loading ? <><span className="animate-pulse">●</span> Gerando insights...</> : <><Sparkles className="w-4 h-4" /> Gerar Insights</>}
        </Button>
      </CardContent></Card>

      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex items-center gap-2"><Bot className="w-3.5 h-3.5" /> Mentor</CardTitle></CardHeader>
        <CardContent ref={outputRef} className="pt-0 max-h-[60vh] overflow-y-auto">
          {!output && !loading && <p className="text-sm text-muted-foreground/40 italic">Clique em "Gerar Insights" para que o Mentor analise seu desempenho.</p>}
          {(output||loading) && <div className="markdown-output" dangerouslySetInnerHTML={{ __html: marked.parse(output)+(loading?'<span class="cursor-blink"></span>':"") }} />}
        </CardContent>
      </Card>
    </div>
  )
}

function ProviderBtn({ active, onClick, icon, label, desc }) {
  return (
    <button onClick={onClick} className={cn("flex-1 flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-all duration-150",
      active ? "border-primary bg-primary/10 text-foreground" : "border-border text-muted-foreground hover:text-foreground"
    )}>
      <span className="text-xl">{icon}</span>
      <div>
        <div className={cn("text-sm font-semibold", active && "text-primary")}>{label}</div>
        <div className="text-[11px] text-muted-foreground/70 mt-0.5">{desc}</div>
      </div>
    </button>
  )
}
