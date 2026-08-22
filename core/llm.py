import os
import re
from typing import List, Sequence, Optional
from django.conf import settings
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

# Modelos padrão suportados no Groq
DEFAULT_GROQ_MODELS = [
    getattr(settings, "GROQ_MODEL", None) or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
    "gpt-oss-120b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


def get_groq_api_key() -> Optional[str]:
    """Retorna e limpa a chave da API Groq configurada."""
    key = getattr(settings, "GROQ_API_KEY", None) or os.environ.get("GROQ_API_KEY")
    if not key or key in ("gsk_placeholder_for_development", ""):
        return None
    return str(key).strip().strip("'").strip('"')


def get_groq_model() -> str:
    """Retorna o modelo primário configurado."""
    model = getattr(settings, "GROQ_MODEL", None) or os.environ.get("GROQ_MODEL")
    return (model or "openai/gpt-oss-120b").strip()


def get_groq_llm(model: Optional[str] = None, temperature: float = 0.3) -> Optional[ChatGroq]:
    """Instancia o cliente ChatGroq com o modelo configurado."""
    key = get_groq_api_key()
    if not key:
        return None
    selected_model = model or get_groq_model()
    return ChatGroq(groq_api_key=key, model=selected_model, temperature=temperature)


def compress_messages(
    messages: Sequence[BaseMessage],
    max_recent: int = 6,
    max_chars_per_msg: int = 2500,
) -> List[BaseMessage]:
    """
    Comprime o histórico de mensagens para economizar tokens sem perder o contexto:
    1. Trunca mensagens individuais gigantescas (preservando início e fim).
    2. Mantém as mensagens mais recentes (últimas max_recent) intactas e detalhadas.
    3. Condensa mensagens mais antigas em um resumo estruturado de tópicos anteriores.
    """
    if not messages:
        return []

    # 1. Trunca mensagens individuais muito longas
    processed_messages: List[BaseMessage] = []
    for msg in messages:
        content = msg.content if hasattr(msg, "content") else str(msg)
        if len(content) > max_chars_per_msg:
            half = max_chars_per_msg // 2
            trimmed_content = (
                content[:half]
                + "\n\n[...conteúdo intermediário omitido para economizar contexto...]\n\n"
                + content[-half:]
            )
            if isinstance(msg, HumanMessage):
                processed_messages.append(HumanMessage(content=trimmed_content))
            elif isinstance(msg, AIMessage):
                processed_messages.append(AIMessage(content=trimmed_content))
            elif isinstance(msg, SystemMessage):
                processed_messages.append(SystemMessage(content=trimmed_content))
            else:
                processed_messages.append(HumanMessage(content=trimmed_content))
        else:
            processed_messages.append(msg)

    # 2. Se o total de mensagens já for pequeno, não precisa resumir
    if len(processed_messages) <= max_recent:
        return processed_messages

    # 3. Divide em histórico antigo e mensagens recentes
    older_messages = processed_messages[:-max_recent]
    recent_messages = processed_messages[-max_recent:]

    # 4. Cria resumo contextual das mensagens antigas
    summary_lines = []
    for m in older_messages:
        role = "Usuário" if isinstance(m, HumanMessage) else "Assistente"
        clean_text = m.content.strip().replace("\n", " ")
        clean_text = re.sub(r"\s+", " ", clean_text)
        if len(clean_text) > 180:
            clean_text = clean_text[:180] + "..."
        summary_lines.append(f"- {role}: {clean_text}")

    condensed_summary = (
        "[RESUMO DO CONTEXTO ANTERIOR DA CONVERSA]\n"
        + "\n".join(summary_lines)
        + "\n[FIM DO RESUMO ANTERIOR - CONTINUE O DIÁLOGO A PARTIR DAS MENSAGENS A SEGUIR]\n"
    )

    return [SystemMessage(content=condensed_summary)] + list(recent_messages)


def invoke_groq_with_fallback(
    messages: Sequence[BaseMessage],
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> str:
    """
    Invoca o modelo Groq com fallback automático de modelos caso o modelo principal
    não exista ou retorne 404 (model_not_found).
    """
    groq_key = get_groq_api_key()
    if not groq_key:
        raise ValueError("Chave Groq não configurada")

    candidates = []
    primary = model or get_groq_model()
    if primary:
        candidates.append(primary)
    for m in DEFAULT_GROQ_MODELS:
        if m and m not in candidates:
            candidates.append(m)

    compressed = compress_messages(messages)

    last_exception = None
    for candidate_model in candidates:
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model=candidate_model,
                temperature=temperature,
            )
            response = llm.invoke(compressed)
            return response.content
        except Exception as e:
            err_str = str(e)
            last_exception = e
            if "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str:
                continue
            raise e

    if last_exception:
        raise last_exception
    raise RuntimeError("Nenhum modelo Groq disponível respondeu com sucesso.")
