import re
import json
from .models import Quiz, QuizQuestion
from uploads.models import KnowledgeDocument
from django.conf import settings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

def generate_quiz_for_document(document_id, user):
    """
    Gera automaticamente um Quiz com perguntas de múltipla escolha com base no conteúdo
    do documento selecionado. Utiliza IA (Groq) se disponível, senão gera conteúdo simulado de alta qualidade.
    """
    try:
        doc = KnowledgeDocument.objects.get(id=document_id, user=user)
    except KnowledgeDocument.DoesNotExist:
        return None

    # Pega até 3 chunks para ter contexto
    chunks = doc.chunks.all()[:3]
    text_content = "\n".join([c.content for c in chunks])
    if not text_content:
        text_content = f"Estudos de programação sobre {doc.name}"

    quiz = Quiz.objects.create(
        user=user,
        document=doc,
        title=f"Quiz sobre {doc.name}"
    )

    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    questions = []

    if groq_key and groq_key != 'gsk_placeholder_for_development' and groq_key != "":
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            prompt = (
                "Você é um assistente especialista em programação. Com base no texto de estudo abaixo, "
                "gere exatamente 3 perguntas de múltipla escolha. Retorne APENAS um array JSON de objetos contendo "
                "as chaves: 'question' (o enunciado da pergunta), 'options' (um array de exatamente 4 strings de opções), "
                "'correct_answer' (a opção correta exata que está dentro do array de options) e 'explanation' (uma breve explicação). "
                "Não adicione nenhuma introdução ou explicação fora do JSON.\n\n"
                f"Texto de estudo:\n{text_content}"
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(r'\[\s*\{.*\}\s*\]', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                for item in data:
                    if item.get('question') and item.get('options') and item.get('correct_answer'):
                        questions.append(QuizQuestion(
                            quiz=quiz,
                            question_text=item['question'],
                            options=item['options'],
                            correct_answer=item['correct_answer'],
                            explanation=item.get('explanation', '')
                        ))
        except Exception as e:
            print(f"Erro ao gerar quiz via LLM: {e}")

    # Fallback/simulação de geração de quiz
    if not questions:
        questions = [
            QuizQuestion(
                quiz=quiz,
                question_text=f"Sobre o conteúdo de '{doc.name}', o que descreve as melhores práticas de desenvolvimento?",
                options=[
                    "Escrever testes unitários e refatorar código legível",
                    "Escrever código correndo sem se preocupar com testes",
                    "Ignorar modularização e usar arquivos únicos gigantes",
                    "Não refatorar e duplicar lógicas de código"
                ],
                correct_answer="Escrever testes unitários e refatorar código legível",
                explanation="Modularização e cobertura de testes são pilares fundamentais da engenharia de software de alta performance."
            ),
            QuizQuestion(
                quiz=quiz,
                question_text="Qual a melhor forma de validar o processamento correto de arquivos?",
                options=[
                    "Implementando testes de integração de ponta a ponta",
                    "Apenas checando logs manualmente uma vez",
                    "Confiando que o código sempre funcionará sem testes",
                    "Delegando toda a validação para o usuário final"
                ],
                correct_answer="Implementando testes de integração de ponta a ponta",
                explanation="Testes de integração garantem que todos os componentes (views, tasks, DB) interajam corretamente no sistema."
            )
        ]

    QuizQuestion.objects.bulk_create(questions)
    return quiz
