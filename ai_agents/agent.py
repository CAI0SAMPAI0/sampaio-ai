import re
import requests
from typing import TypedDict, Sequence
from django.conf import settings
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from knowledge_base.services import search_similar_chunks


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    context: str
    web_context: str
    user: any


def web_search_ddg(query: str) -> str:
    """
    Realiza uma busca no DuckDuckGo (HTML) e retorna os principais snippets.
    Livre de dependências externas e chaves de API.
    """
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Reduced timeout to 2.0s to prevent hanging when offline or blocked
        res = requests.post(url, data={"q": query}, headers=headers, timeout=2.0)
        if res.status_code == 200:
            snippets = re.findall(
                r'<a class="result__snippet"[^>]*>(.*?)</a>', res.text, re.DOTALL
            )
            results = []
            for s in snippets[:3]:
                clean_text = re.sub(r"<[^>]*>", "", s).strip()
                results.append(clean_text)
            if results:
                return "\n".join([f"- {r}" for r in results])
    except Exception as e:
        print(f"Erro ao buscar no DDG: {e}")
    return ""


def retrieve_rag_node(state: AgentState) -> dict:
    """
    Recupera trechos relevantes dos livros/documentos do usuário.
    """
    # Pega o último texto do usuário
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if not last_user_msg:
        return {"context": ""}

    similar_chunks = search_similar_chunks(state["user"], last_user_msg, top_k=3)
    context_parts = []
    for score, chunk in similar_chunks:
        if score > 0.15:
            context_parts.append(
                f"Livro/Documento: {chunk.document.name} (Pág. {chunk.page_number or 'N/A'})\n"
                f"Trecho: {chunk.content}"
            )

    context_str = "\n\n---\n\n".join(context_parts) if context_parts else ""
    return {"context": context_str}


def web_search_node(state: AgentState) -> dict:
    """
    Decide se precisa buscar na internet (se explicitamente solicitado ou se o RAG foi vazio).
    """
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if not last_user_msg:
        return {"web_context": ""}

    # Verifica intenção de busca online
    trigger_words = [
        "busca",
        "pesquisa",
        "internet",
        "web",
        "online",
        "atual",
        "google",
        "noticia",
        "recente",
    ]
    greetings = [
        "ola",
        "olá",
        "oi",
        "bom dia",
        "boa tarde",
        "boa noite",
        "tudo bem",
        "eae",
        "e ai",
        "hello",
        "hi",
    ]
    is_greeting = (
        any(gree in last_user_msg.lower() for gree in greetings)
        and len(last_user_msg.split()) < 4
    )

    needs_web = (
        any(word in last_user_msg.lower() for word in trigger_words)
        or not state.get("context")
    ) and not is_greeting

    if needs_web:
        web_res = web_search_ddg(last_user_msg)
        return {"web_context": web_res}

    return {"web_context": ""}


def generate_response_node(state: AgentState) -> dict:
    """
    Gera a resposta final do agente consolidando RAG e busca web com foco didático e pedagógico.
    """
    lc_messages = []

    # 1. Identifica nível e dados do aluno
    user = state.get("user")
    user_level = "iniciante"
    user_name = "Aluno"
    if user:
        user_level = getattr(user, "level", "iniciante") or "iniciante"
        user_name = (
            getattr(user, "first_name", None)
            or getattr(user, "email", "Aluno").split("@")[0]
        )

    level_instruction = ""
    if user_level in ("iniciante", "junior"):
        level_instruction = (
            f"O aluno está no nível {user_level.upper()}.\n"
            "- Explique de forma muito simples, paciente e didática.\n"
            "- Use analogias práticas do mundo real para ilustrar conceitos abstratos.\n"
            "- Decomponha o problema passo a passo (Entradas -> Processamento -> Saídas).\n"
            "- Priorize lógica pura (estruturas condicionais, repetições, funções e coleções) antes de qualquer framework.\n"
        )
    elif user_level == "pleno":
        level_instruction = (
            "O aluno está no nível PLENO / INTERMEDIÁRIO.\n"
            "- Foque em fundamentos sólidos, boas práticas e conformidade com PEP8.\n"
            "- Mostre a relação clara entre lógica pura e a abstração dos frameworks.\n"
            "- Traga exemplos práticos e desafie o aluno a pensar em estrutura e modularidade.\n"
        )
    else:  # senior
        level_instruction = (
            "O aluno está no nível SÊNIOR / AVANÇADO.\n"
            "- Compare diferentes abordagens e trade-offs arquiteturais.\n"
            "- Aprofunde em documentação oficial, performance, concorrência e padrões de projeto.\n"
            "- Discuta boas práticas avançadas e resiliência de código.\n"
        )

    # 2. Prompt pedagógico completo de tutoria e mentoria
    system_prompt = f"""Você é uma IA professora especializada em ensinar programação de forma didática, progressiva e lógica, com foco em ajudar o aluno a aprender de verdade na plataforma Sampaio AI.

Sua missão não é apenas responder perguntas ou ser um gerador automático de código pronto, mas sim conduzir o aluno no raciocínio, na compreensão dos fundamentos e na transformação de problemas em soluções reais.

## NÍVEL DO ALUNO ATUAL
Nome do Aluno: {user_name}
Nível de Programação Cadastrado: {user_level.upper()}
{level_instruction}

## PRINCÍPIOS PEDAGÓGICOS FUNDAMENTAIS
- Ensine primeiro a lógica, depois a sintaxe e só então frameworks e ferramentas.
- Priorize o ensino de lógica de programação, algoritmos, entradas e saídas, condições, repetição, funções e estrutura de pensamento antes de frameworks, APIs e bibliotecas avançadas.
- Sempre que possível, incentive o aluno a pensar antes de entregar a resposta final.
- Faça perguntas orientadoras quando o aluno estiver aprendendo ou travado.
- Explique o "porquê" de cada decisão técnica, não apenas o "como".
- Adapte a profundidade da explicação ao nível do aluno.
- Use exemplos simples, práticos e progressivos.
- Nunca humilhe, ironize ou desanime o aluno.
- Priorize entendimento real, não resposta pronta.
- Quando o aluno pedir solução direta, tente primeiro guiá-lo com pistas e raciocínio.
- Se o aluno já tentou, reconheça o esforço e avance com mais clareza a partir de onde ele parou.
- Se o aluno estiver muito perdido, simplifique a explicação e conduza passo a passo.

## ESTRUTURA DE ENSINO E RESOLUÇÃO DE PROBLEMAS
Sempre que o aluno pedir ajuda para resolver um problema, siga esta ordem pedagógica:
1. Entender o problema: Decompor em Entrada, Processamento e Saída.
2. Identificar as regras de negócio e restrições.
3. Criar o algoritmo e o raciocínio em linguagem simples (português/pseudocódigo).
4. Transformar o algoritmo em código estruturado.
5. Testar e prever casos de borda.
6. Sugerir melhorias ou próximo passo de prática.

## SOBRE LÓGICA DE PROGRAMAÇÃO
- Explique raciocínio lógico com clareza.
- Mostre estruturas como condições, repetições, funções, listas e dicionários com foco no pensamento algorítmico.
- Sempre conecte o conteúdo com resolução de problemas reais.
- Não pule fundamentos essenciais.

## SOBRE FRAMEWORKS E BIBLIOTECAS
- Só introduza frameworks quando a base lógica estiver clara.
- Explique qual problema real o framework resolve.
- Mostre a relação entre framework, estrutura de projeto e necessidade real.
- Não trate framework como mágica: compare com a lógica por trás do que ele automatiza (solução manual vs framework).
- Deixe claro o que é convenção do framework e o que é lógica pura do programa.

## SOBRE DOCUMENTAÇÃO E CONSULTAS
- Sempre incentive o uso da documentação oficial.
- Quando o assunto envolver bibliotecas, frameworks ou APIs, consulte a documentação / referências antes de responder.
- Resuma a documentação em linguagem simples e didática.
- Destaque o que é essencial para o aluno naquele momento.
- Nunca invente comportamento de biblioteca ou framework (sem alucinações).

## QUANDO O ALUNO PERGUNTAR "COMO FAÇO ISSO?" OU PEDIR CÓDIGO
Sempre responda estruturando:
1. O que é o conceito.
2. Por que isso existe e quando usar.
3. Como pensar para implementar (raciocínio/lógica).
4. Código com comentários explicativos nas partes importantes.
5. Um pequeno desafio ou próximo passo de prática.

## QUANDO A DÚVIDA FOR DE ERRO OU BUG
- Ajude a investigar a causa raiz antes de apenas corrigir.
- Leia e explique o que a mensagem de erro significa.
- Sugira testes simples para isolar o problema.
- Só então proponha a correção explicando o motivo do conserto.

## TOM DE VOZ
- Humana, didática, professoral, paciente, encorajadora, clara e direta.
- Use analogias do mundo real para ilustrar conceitos abstratos.

## OBJETIVO FINAL
Fazer o aluno aprender a pensar como programador: entender problemas, criar algoritmos, implementar soluções com autonomia e usar ferramentas com consciência.
"""

    # Adiciona contexto do RAG (livros do usuário)
    if state.get("context"):
        system_prompt += (
            "\n## CONTEXTO EXTRAÍDO DOS LIVROS/DOCUMENTOS DE PROGRAMAÇÃO DO ALUNO:\n"
            f"{state['context']}\n"
            "Cite o nome do livro/documento e a página quando responder com base neste material.\n"
        )

    # Adiciona contexto da Web
    if state.get("web_context"):
        system_prompt += (
            "\n## INFORMAÇÕES RECENTES DA INTERNET (DOCUMENTAÇÃO OFICIAL / WEB):\n"
            f"{state['web_context']}\n"
            "Use estas informações para complementar a resposta com dados técnicos atualizados da documentação oficial.\n"
        )

    lc_messages.append(SystemMessage(content=system_prompt))

    # 2. Histórico de conversas
    lc_messages.extend(state["messages"])

    # 3. Executa inferência com fallback e compressão de contexto
    assistant_content = ""
    from core.llm import get_groq_api_key, invoke_groq_with_fallback

    groq_key = get_groq_api_key()

    if groq_key:
        try:
            assistant_content = invoke_groq_with_fallback(lc_messages, temperature=0.3)
        except Exception as e:
            assistant_content = (
                f"Desculpe, ocorreu um erro ao processar a resposta: {str(e)}"
            )
    else:
        # Resposta simulada para desenvolvimento
        key_status = "Chave nula ou ausente"
        if getattr(settings, "GROQ_API_KEY", None) == "gsk_placeholder_for_development":
            key_status = "Placeholder de desenvolvimento ativo no seu arquivo .env"

        assistant_content = (
            f"### Resposta do Mentor (Modo Simulação LangGraph)\n\n"
            f"Olá! O Sampaio AI está em modo simulado ({key_status}).\n\n"
        )
        if state.get("context"):
            assistant_content += (
                f"**Livros Consumidos (RAG):**\n```\n{state['context']}\n```\n\n"
            )
        if state.get("web_context"):
            assistant_content += (
                f"**Resultados da Internet (Web Search):**\n"
                f"```\n{state['web_context']}\n```\n\n"
            )
        if not state.get("context") and not state.get("web_context"):
            assistant_content += (
                "*(Nenhum contexto RAG ou Web foi recuperado para esta mensagem).* \n"
            )

    # Retorna o resultado para atualizar a lista de mensagens (ou estado)
    return {
        "messages": list(state["messages"]) + [AIMessage(content=assistant_content)]
    }


# Compilação do grafo LangGraph
workflow = StateGraph(AgentState)

workflow.add_node("retrieve_rag", retrieve_rag_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("generate_response", generate_response_node)

workflow.set_entry_point("retrieve_rag")
workflow.add_edge("retrieve_rag", "web_search")
workflow.add_edge("web_search", "generate_response")
workflow.add_edge("generate_response", END)

langgraph_agent = workflow.compile()
