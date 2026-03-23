# ⬡ Academic Tracker

Sistema de acompanhamento acadêmico com IA local (Ollama + LangChain), construído com FastAPI, SQLite e uma interface web moderna.

## ✨ Funcionalidades

- 📚 **Cadastro de matérias** com pesos e avaliações personalizadas
- 📊 **Gráficos automáticos** de média atual, melhor projeção e mínimo para passar
- 📅 **Calendário dinâmico** com provas, trabalhos e prazos
- 🤖 **Insights com IA local** via Ollama + LangChain (streaming em tempo real)
- 💾 Dados persistidos em SQLite local (sem nuvem)

## 🛠 Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + SQLAlchemy |
| Banco | SQLite |
| IA | LangChain + Ollama (local) |
| Frontend | HTML/CSS/JS + Chart.js + FullCalendar |
| Gerenciador | `uv` |

## 🚀 Setup

### 1. Pré-requisitos

```bash
# Instalar uv (se não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar Ollama
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Windows: baixar em https://ollama.com/download
```

### 2. Baixar um modelo no Ollama

```bash
# Recomendado (bom equilíbrio qualidade/velocidade):
ollama pull llama3

# Alternativas:
ollama pull qwen2.5      # muito bom em português
ollama pull mistral      # rápido
ollama pull llama3.2     # menor, mais leve
```

### 3. Instalar dependências e rodar

```bash
# Clonar/entrar na pasta do projeto
cd academic-tracker

# Instalar dependências com uv
uv sync

# Iniciar o servidor
uv run uvicorn app.main:app --reload --port 8000
```

### 4. Abrir no navegador

```
http://localhost:8000
```

A API docs ficam disponíveis em: `http://localhost:8000/docs`

## 📁 Estrutura do Projeto

```
academic-tracker/
├── pyproject.toml              # Dependências (uv)
├── app/
│   ├── main.py                 # FastAPI app + roteamento
│   ├── database.py             # Configuração SQLite/SQLAlchemy
│   ├── models.py               # Modelos do banco (Subject, Assessment, Event)
│   ├── schemas.py              # Schemas Pydantic (validação)
│   ├── utils.py                # Cálculos de média, projeção, status
│   ├── routers/
│   │   ├── subjects.py         # CRUD de matérias
│   │   ├── assessments.py      # CRUD de avaliações
│   │   ├── events.py           # CRUD de eventos do calendário
│   │   └── insights.py         # Endpoint SSE de insights
│   └── ai/
│       └── agent.py            # LangChain + Ollama (streaming)
└── frontend/
    └── index.html              # SPA completa (Chart.js + FullCalendar)
```

## 🧮 Como Funciona o Cálculo de Médias

Cada avaliação tem um **peso** (relativo). A média é calculada ponderada:

```
Média Atual = Σ(nota × peso) / Σ(pesos das notas lançadas)

Melhor Projeção = (Σ(notas lançadas × peso) + Σ(nota_máx × peso_pendente)) / Σ(todos os pesos)

Mínimo p/ Passar = (nota_aprovação × peso_total - Σ(notas × pesos)) / Σ(pesos_pendentes)
```

**Exemplo:**
- P1 (peso 0.4): nota 7.5
- P2 (peso 0.4): pendente
- Trabalho (peso 0.2): nota 8.0

```
Média Atual    = (7.5×0.4 + 8.0×0.2) / (0.4+0.2) = 7.67
Melhor Projeção = (7.5×0.4 + 10×0.4 + 8.0×0.2) / 1.0 = 8.60
Mínimo p/ Passar = (6.0×1.0 - 7.5×0.4 - 8.0×0.2) / 0.4 = 2.50  ✅
```

## 🤖 Usando Insights IA

1. Certifique-se que o Ollama está rodando: `ollama serve`
2. Na aba **Insights IA**, selecione o modelo (ex: `llama3`)
3. Opcionalmente adicione um foco específico
4. Clique em "Gerar Insights"

A IA recebe automaticamente todas as suas matérias, notas e eventos do calendário para a análise.

## 🎨 Personalização

Você pode modificar o modelo padrão do Ollama alterando o campo "Modelo Ollama" na interface, ou diretamente em `app/ai/agent.py`.

Para alterar o prompt da IA (idioma, tom, formato), edite as constantes `SYSTEM_PROMPT` e `HUMAN_TEMPLATE` em `app/ai/agent.py`.
