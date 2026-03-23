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
- Sugira estratégias de estudo concretas, não genéricas.
- Celebre pontos positivos, mas não ignore problemas reais.
- Use emojis com moderação para tornar a leitura mais agradável.
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
1. **📊 Panorama Geral** — resumo rápido do desempenho global
2. **⚠️ Atenção Urgente** — matérias ou situações que precisam de ação imediata
3. **📅 Planejamento** — sugestões de prioridade considerando as datas
4. **💡 Dicas Práticas** — estratégias específicas para as matérias mais críticas
5. **✅ Pontos Positivos** — o que está indo bem e merece reconhecimento
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
        return ChatOpenAI(model=model, api_key=key, temperature=0.6, streaming=True)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, base_url=settings.ollama_base_url, temperature=0.6, streaming=True)


async def stream_insights(
    subjects: list[dict],
    events: list[dict],
    provider: str = "ollama",
    model: str = "llama3",
    openai_api_key: str | None = None,
    focus: str | None = None,
) -> AsyncIterator[str]:
    llm = _get_llm(provider, model, openai_api_key)
    messages = _build_messages(subjects, events, focus)
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content


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
1. **📊 Situação Atual** — diagnóstico direto do desempenho nesta matéria
2. **🎯 Chances de Aprovação** — estimativa realista com base nos números
3. **💡 O Que Fazer Agora** — 2-3 ações concretas e específicas
4. **⚡ Alertas** — pontos críticos que exigem atenção imediata (omita se não houver)
"""


async def stream_subject_insight(
    subject: dict,
    provider: str = "ollama",
    model: str = "llama3",
    openai_api_key: str | None = None,
) -> AsyncIterator[str]:
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

    llm = _get_llm(provider, model, openai_api_key)
    messages = [SystemMessage(content=SUBJECT_SYSTEM_PROMPT), HumanMessage(content=content)]
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content
