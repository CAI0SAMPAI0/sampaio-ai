import re
import json
from .models import Flashcard
from uploads.models import KnowledgeDocument
from django.conf import settings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

def generate_flashcards_for_document(document_id, user):
    """
    Gera automaticamente uma lista de flashcards para o usuário com base no conteúdo
    do documento selecionado. Utiliza IA (Groq) se disponível, senão gera conteúdo simulado de alta qualidade.
    """
    try:
        doc = KnowledgeDocument.objects.get(id=document_id, user=user)
    except KnowledgeDocument.DoesNotExist:
        return []

    # Pega até 3 chunks para ter contexto
    chunks = doc.chunks.all()[:3]
    text_content = "\n".join([c.content for c in chunks])
    if not text_content:
        text_content = f"Estudos de programação sobre {doc.name}"

    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    flashcard_objs = []
    
    if groq_key and groq_key != 'gsk_placeholder_for_development' and groq_key != "":
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="openai/gpt-oss-20b",
                temperature=0.4
            )
            prompt = (
                "Você é um assistente especialista em programação. Com base no texto de estudo abaixo, "
                "gere exatamente 3 a 5 flashcards para revisão de conteúdo. Retorne APENAS um array JSON de objetos contendo "
                "as chaves 'front' (pergunta da frente) e 'back' (resposta do verso). Não adicione nenhuma introdução ou explicação fora do JSON.\n\n"
                f"Texto de estudo:\n{text_content}"
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(r'\[\s*\{.*\}\s*\]', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                for item in data:
                    if item.get('front') and item.get('back'):
                        flashcard_objs.append(Flashcard(
                            user=user,
                            document=doc,
                            front=item['front'],
                            back=item['back']
                        ))
        except Exception as e:
            print(f"Erro ao gerar flashcards via LLM: {e}")
            
    # Fallback/simulação de geração
    if not flashcard_objs:
        flashcard_objs = [
            Flashcard(
                user=user,
                document=doc,
                front=f"Qual é o conceito principal abordado em {doc.name}?",
                back=f"O documento descreve tópicos de desenvolvimento de software referentes a {doc.name}."
            ),
            Flashcard(
                user=user,
                document=doc,
                front=f"Explique o trecho: '{text_content[:60]}...'",
                back=f"Trata-se de uma definição técnica extraída das páginas de {doc.name}."
            ),
            Flashcard(
                user=user,
                document=doc,
                front="Quais são as melhores práticas para este tipo de tecnologia?",
                back="Código limpo, escrita de testes unitários automatizados e modularização de componentes."
            )
        ]
        
    Flashcard.objects.bulk_create(flashcard_objs)
    return flashcard_objs
