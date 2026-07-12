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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Reduced timeout to 2.0s to prevent hanging when offline or blocked
        res = requests.post(url, data={'q': query}, headers=headers, timeout=2.0)
        if res.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', res.text, re.DOTALL)
            results = []
            for s in snippets[:3]:
                clean_text = re.sub(r'<[^>]*>', '', s).strip()
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
    for msg in reversed(state['messages']):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break
            
    if not last_user_msg:
        return {"context": ""}
        
    similar_chunks = search_similar_chunks(state['user'], last_user_msg, top_k=3)
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
    for msg in reversed(state['messages']):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break
            
    if not last_user_msg:
        return {"web_context": ""}
        
    # Verifica intenção de busca online
    trigger_words = ['busca', 'pesquisa', 'internet', 'web', 'online', 'atual', 'google', 'noticia', 'recente']
    greetings = ['ola', 'olá', 'oi', 'bom dia', 'boa tarde', 'boa noite', 'tudo bem', 'eae', 'e ai', 'hello', 'hi']
    is_greeting = any(gree in last_user_msg.lower() for gree in greetings) and len(last_user_msg.split()) < 4
    
    needs_web = (any(word in last_user_msg.lower() for word in trigger_words) or not state.get('context')) and not is_greeting
    
    if needs_web:
        web_res = web_search_ddg(last_user_msg)
        return {"web_context": web_res}
        
    return {"web_context": ""}


def generate_response_node(state: AgentState) -> dict:
    """
    Gera a resposta final do agente consolidando RAG e busca web.
    """
    lc_messages = []
    
    # 1. Prompt de sistema (IA de programação)
    system_prompt = (
        "Você é o mentor técnico e assistente virtual da Sampaio AI, uma plataforma inteligente "
        "de estudos de programação. Seu objetivo é ensinar conceitos, tirar dúvidas técnicas, "
        "criar planos de estudos e propor desafios práticos com clareza e exemplos elegantes.\n\n"
    )
    
    # Adiciona contexto do RAG (livros)
    if state.get('context'):
        system_prompt += (
            "Aqui está o contexto relevante extraído dos LIVROS DE PROGRAMAÇÃO do usuário:\n"
            f"{state['context']}\n"
            "Cite o livro/documento e a página quando responder com base neste contexto.\n\n"
        )
        
    # Adiciona contexto da Web
    if state.get('web_context'):
        system_prompt += (
            "Aqui estão informações recentes encontradas na INTERNET:\n"
            f"{state['web_context']}\n"
            "Use estas informações para complementar a resposta com dados atuais, mencionando que a fonte é de busca web.\n\n"
        )
        
    lc_messages.append(SystemMessage(content=system_prompt))
    
    # 2. Histórico de conversas
    lc_messages.extend(state['messages'])
    
    # 3. Executa inferência
    assistant_content = ""
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    if groq_key:
        groq_key = str(groq_key).strip().strip("'").strip('"')
    
    if groq_key and groq_key != 'gsk_placeholder_for_development' and groq_key != "":
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-specdec",
                temperature=0.3
            )
            response = llm.invoke(lc_messages)
            assistant_content = response.content
        except Exception as e:
            assistant_content = f"Desculpe, ocorreu um erro ao processar a resposta: {str(e)}"
    else:
        # Resposta simulada para desenvolvimento
        key_status = "Chave nula ou ausente"
        if groq_key == 'gsk_placeholder_for_development':
            key_status = "Placeholder de desenvolvimento ativo no seu arquivo .env"
        elif groq_key == "":
            key_status = "Chave vazia"
            
        assistant_content = (
            f"### Resposta do Mentor (Modo Simulação LangGraph)\n\n"
            f"Olá! O Sampaio AI está em modo simulado ({key_status}).\n\n"
        )
        if state.get('context'):
            assistant_content += (
                f"**Livros Consumidos (RAG):**\n"
                f"```\n{state['context']}\n```\n\n"
            )
        if state.get('web_context'):
            assistant_content += (
                f"**Resultados da Internet (Web Search):**\n"
                f"```\n{state['web_context']}\n```\n\n"
            )
        if not state.get('context') and not state.get('web_context'):
            assistant_content += "*(Nenhum contexto RAG ou Web foi recuperado para esta mensagem).* \n"

    # Retorna o resultado para atualizar a lista de mensagens (ou estado)
    return {"messages": list(state['messages']) + [AIMessage(content=assistant_content)]}


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
