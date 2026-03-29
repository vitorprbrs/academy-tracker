from datetime import date
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings


# ─── Dashboard / Global Insights ─────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um assistente acadêmico inteligente e motivador chamado **Mentor**.
Seu papel é analisar o desempenho do estudante e fornecer insights úteis, práticos e encorajadores em português.

Regras:
- Seja direto, conciso e útil — sem floreios desnecessários.
- Use dados reais fornecidos para embasar suas análises.
- Quando houver provas próximas, destaque a urgência de forma clara.
- Celebre pontos positivos, mas não ignore problemas reais.
- Formate a resposta em seções claras com Markdown.
"""

HUMAN_TEMPLATE = """
Hoje é {today}.

## Matérias e Desempenho

{subjects_context}

## Próximos Eventos no Calendário

{events_context}

---

{focus_instruction}

Por favor, forneça:
1. **📊 Ranking de Matérias** — classifique as matérias da melhor para a pior performance, indicando o status de aprovação de cada uma
2. **🎯 Projeção de Aprovação** — para cada matéria, analise se o aluno conseguirá atingir a nota mínima; use a média atual e a melhor projeção (com máximo nas pendentes) para estimar as chances reais
3. **🔥 Foco Imediato** — indique quais 1-3 matérias precisam de atenção urgente agora e o motivo específico (nota baixa, projeção ruim, prova próxima)
4. **📅 Próximos Passos** — sugestões práticas e objetivas considerando os eventos no calendário
5. **✅ Destaques Positivos** — reconheça brevemente o que está indo bem
"""


def _format_subjects(subjects: list[dict]) -> str:
    if not subjects:
        return "Nenhuma matéria cadastrada ainda."
    lines = []
    for s in subjects:
        avg     = s.get("current_average")
        proj    = s.get("best_projection")
        needed  = s.get("min_needed")
        status  = s.get("status", "pending")
        passing = s.get("passing_grade", 5.0)
        calc    = s.get("calc_type", "weighted")
        avg_str    = f"{avg:.1f}"    if avg    is not None else "sem notas"
        proj_str   = f"{proj:.1f}"   if proj   is not None else "—"
        needed_str = f"{needed:.1f}" if needed is not None else "—"
        calc_label = "Média Simples" if calc == "simple" else "Média Ponderada"
        status_emoji = {
            "approved": "✅", "passing": "🟢",
            "pending":  "⏳", "failing": "🔴", "failed": "❌",
        }.get(status, "⏳")
        lines.append(
            f"- **{s['name']}** {status_emoji} [{calc_label}] | "
            f"Média atual: {avg_str} | "
            f"Melhor projeção: {proj_str} | "
            f"Mínimo p/ passar: {needed_str} | "
            f"Nota de aprovação: {passing}"
        )
        for a in s.get("assessments", []):
            score_str = (
                f"{a['score']:.1f}/{a['max_score']:.0f}"
                if a.get("score") is not None else "pendente"
            )
            weight_str = f" (peso {a['weight']})" if calc == "weighted" else ""
            lines.append(f"  - {a['name']}{weight_str}: {score_str}")
    return "\n".join(lines)


def _format_events(events: list[dict]) -> str:
    if not events:
        return "Nenhum evento cadastrado."
    lines = []
    today = date.today()
    for e in events:
        try:
            event_date = date.fromisoformat(e["date"])
            days_until = (event_date - today).days
            if days_until < 0:
                urgency = f"(passou há {abs(days_until)} dias)"
            elif days_until == 0:
                urgency = "🚨 HOJE"
            elif days_until == 1:
                urgency = "⚡ amanhã"
            elif days_until <= 7:
                urgency = f"⚡ em {days_until} dias"
            else:
                urgency = f"em {days_until} dias"
        except ValueError:
            urgency = ""
        subject_str = f" [{e['subject_name']}]" if e.get("subject_name") else ""
        lines.append(
            f"- {e['date']} {urgency} | **{e['title']}**{subject_str} ({e['event_type']})"
        )
    return "\n".join(lines)


def _build_messages(subjects, events, focus):
    focus_instruction = (
        f"**Foco especial solicitado:** {focus}\n" if focus
        else "Faça uma análise completa e equilibrada."
    )
    human_content = HUMAN_TEMPLATE.format(
        today=date.today().strftime("%d/%m/%Y"),
        subjects_context=_format_subjects(subjects),
        events_context=_format_events(events),
        focus_instruction=focus_instruction,
    )
    return [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_content)]


def _get_llm(provider: str, model: str, openai_api_key: str | None):
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        key = openai_api_key or settings.openai_api_key
        if not key:
            raise ValueError("Chave da API OpenAI não fornecida.")
        return ChatOpenAI(model=model, api_key=key, temperature=0.6)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, base_url=settings.ollama_base_url, temperature=0.6)


async def stream_insights(
    subjects: list[dict],
    events: list[dict],
    provider: str = "ollama",
    model: str | None = None,
    openai_api_key: str | None = None,
    focus: str | None = None,
) -> AsyncIterator[str]:
    resolved_model = model or (settings.ollama_default_model if provider == "ollama" else settings.openai_default_model)
    llm = _get_llm(provider, resolved_model, openai_api_key)
    messages = _build_messages(subjects, events, focus)
    async for chunk in llm.astream(messages):
        content = chunk.content
        if content and isinstance(content, str):
            yield content


async def stream_insights_auto(
    subjects: list[dict],
    events: list[dict],
    focus: str | None = None,
    openai_api_key: str | None = None,
):
    """Dashboard auto-insight: OpenAI (gpt-5-mini) first → Ollama (local) fallback."""
    messages = _build_messages(subjects, events, focus)

    # Try OpenAI (paid) first
    key = openai_api_key or settings.openai_api_key
    if key:
        openai_yielded = False
        try:
            llm = _get_llm("openai", settings.openai_default_model, key)
            async for chunk in llm.astream(messages):
                content = chunk.content
                if content and isinstance(content, str):
                    openai_yielded = True
                    yield content
            return  # OpenAI succeeded
        except Exception:
            if openai_yielded:
                return  # Partial content already sent

    # Fallback to Ollama (local/free)
    ollama_yielded = False
    try:
        llm = _get_llm("ollama", settings.ollama_default_model, None)
        async for chunk in llm.astream(messages):
            content = chunk.content
            if content and isinstance(content, str):
                ollama_yielded = True
                yield content
        return
    except Exception:
        if ollama_yielded:
            return

    raise ValueError(
        "Nenhum modelo disponível. Configure OPENAI_API_KEY no .env "
        "ou inicie o Ollama com 'ollama serve'."
    )


# ─── Subject-Specific Insight ─────────────────────────────────────────────────

SUBJECT_SYSTEM_PROMPT = """Você é um assistente acadêmico inteligente chamado **Mentor**.
Analise o desempenho do estudante na matéria indicada e forneça insights práticos em português.
Seja direto, objetivo e motivador. Use Markdown com seções claras. Emojis com moderação."""

SUBJECT_HUMAN_TEMPLATE = """
Hoje é {today}.

## Matéria: {subject_name}
- Tipo de cálculo: {calc_type}
- Nota de aprovação: {passing_grade}
- Status: {status}
- Média atual: {current_average}
- Melhor projeção (máximo nas pendentes): {best_projection}
- Mínimo necessário nas pendentes: {min_needed}

## Avaliações:
{assessments}

Forneça uma análise focada com:
1. **📊 Situação Atual** — diagnóstico direto: média atual vs. nota mínima, e se o aluno está aprovado, em risco ou reprovado
2. **🎯 Projeção de Aprovação** — com base na melhor projeção e no mínimo necessário, diga se é possível passar e quais notas precisam ser atingidas nas avaliações pendentes
3. **💡 O Que Fazer Agora** — 2-3 ações concretas e específicas para melhorar o desempenho nesta matéria
4. **⚡ Alertas** — pontos críticos que exigem atenção imediata (omita a seção se não houver)
"""


async def stream_subject_insight(
    subject: dict,
    provider: str = "ollama",
    model: str | None = None,
    openai_api_key: str | None = None,
) -> AsyncIterator[str]:
    resolved_model = model or (settings.ollama_default_model if provider == "ollama" else settings.openai_default_model)
    messages = _build_subject_messages(subject)
    llm = _get_llm(provider, resolved_model, openai_api_key)
    async for chunk in llm.astream(messages):
        c = chunk.content
        if c and isinstance(c, str):
            yield c


async def stream_subject_insight_auto(
    subject: dict,
    openai_api_key: str | None = None,
):
    """Subject-specific auto-insight: OpenAI (gpt-5-mini) first → Ollama fallback."""
    messages = _build_subject_messages(subject)

    # Try OpenAI (paid) first
    key = openai_api_key or settings.openai_api_key
    if key:
        openai_yielded = False
        try:
            llm = _get_llm("openai", settings.openai_default_model, key)
            async for chunk in llm.astream(messages):
                content = chunk.content
                if content and isinstance(content, str):
                    openai_yielded = True
                    yield content
            return
        except Exception:
            if openai_yielded:
                return

    # Fallback to Ollama (local/free)
    ollama_yielded = False
    try:
        llm = _get_llm("ollama", settings.ollama_default_model, None)
        async for chunk in llm.astream(messages):
            content = chunk.content
            if content and isinstance(content, str):
                ollama_yielded = True
                yield content
        return
    except Exception:
        if ollama_yielded:
            return

    raise ValueError(
        "Nenhum modelo disponível. Configure OPENAI_API_KEY no .env "
        "ou inicie o Ollama com 'ollama serve'."
    )


def _build_subject_messages(subject: dict):
    calc_type = subject.get("calc_type", "weighted")
    calc_label = "Média Simples" if calc_type == "simple" else "Média Ponderada"

    assessments_lines = []
    for a in subject.get("assessments", []):
        score_str = f"{a['score']:.1f}/{a['max_score']:.0f}" if a.get("score") is not None else "pendente"
        weight_str = f" (peso {a['weight']})" if calc_type == "weighted" else ""
        assessments_lines.append(f"- {a['name']}{weight_str}: {score_str}")

    avg    = subject.get("current_average")
    proj   = subject.get("best_projection")
    needed = subject.get("min_needed")

    content = SUBJECT_HUMAN_TEMPLATE.format(
        today=date.today().strftime("%d/%m/%Y"),
        subject_name=subject["name"],
        calc_type=calc_label,
        passing_grade=subject.get("passing_grade", 6.0),
        status=subject.get("status", "pending"),
        current_average=f"{avg:.1f}" if avg is not None else "sem notas ainda",
        best_projection=f"{proj:.1f}" if proj is not None else "—",
        min_needed=f"{needed:.1f}" if needed is not None else "—",
        assessments="\n".join(assessments_lines) if assessments_lines else "Nenhuma avaliação cadastrada.",
    )
    return [SystemMessage(content=SUBJECT_SYSTEM_PROMPT), HumanMessage(content=content)]
