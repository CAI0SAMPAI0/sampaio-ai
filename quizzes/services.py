import re
import json
from .models import Quiz, QuizQuestion
from uploads.models import KnowledgeDocument
from django.conf import settings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage


def generate_quiz_for_document(
    document_id, user, theme=None, num_questions=3, difficulty="Médio"
):
    """
    Gera automaticamente um Quiz com perguntas de múltipla escolha com base no conteúdo
    do documento selecionado. Utiliza IA (Groq) se disponível, senão gera conteúdo simulado de alta qualidade.
    """
    try:
        doc = KnowledgeDocument.objects.get(id=document_id, user=user)
    except KnowledgeDocument.DoesNotExist:
        return None

    # Se tema for especificado, busca semanticamente os trechos mais relevantes do arquivo
    if theme:
        try:
            from knowledge_base.services import (
                DeterministicEmbeddings,
                cosine_similarity,
            )

            embedder = DeterministicEmbeddings()
            query_vector = embedder.embed_query(theme)
            all_chunks = doc.chunks.all()
            scored_chunks = []
            for chunk in all_chunks:
                score = cosine_similarity(query_vector, chunk.embedding)
                scored_chunks.append((score, chunk))
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            chunks = [item[1] for item in scored_chunks[:3]]
        except Exception as e:
            print(f"Erro na busca semântica de tema: {e}")
            chunks = doc.chunks.all()[:3]
    else:
        chunks = doc.chunks.all()[:3]

    text_content = "\n".join([c.content for c in chunks])
    if not text_content:
        text_content = f"Estudos de programação sobre {doc.name}"

    title = f"Quiz sobre {doc.name}"
    if theme:
        title += f" (Tema: {theme})"

    quiz = Quiz.objects.create(user=user, document=doc, title=title)

    groq_key = getattr(settings, "GROQ_API_KEY", None)
    questions = []

    if groq_key and groq_key != "gsk_placeholder_for_development" and groq_key != "":
        try:
            from core.llm import invoke_groq_with_fallback
            prompt = (
                "Você é um assistente especialista em programação. Com base no texto de estudo abaixo, "
                f"gere exatamente {num_questions} perguntas de múltipla escolha.\n"
                f"Foco Temático: {theme if theme else 'Todo o conteúdo do texto'}\n"
                f"Nível de Dificuldade: {difficulty}\n\n"
                "Retorne APENAS um array JSON de objetos contendo "
                "as chaves: 'question' (o enunciado da pergunta), 'options' (um array de exatamente 4 strings de opções), "
                "'correct_answer' (a opção correta exata que está dentro do array de options) e 'explanation' (uma breve explicação técnica baseada na PEP8 ou boas práticas).\n"
                "Não adicione nenhuma introdução ou explicação fora do JSON.\n\n"
                f"Texto de estudo:\n{text_content}"
            )
            response_content = invoke_groq_with_fallback([HumanMessage(content=prompt)], temperature=0.4)
            match = re.search(r"\[\s*\{.*\}\s*\]", response_content, re.DOTALL)

            if match:
                data = json.loads(match.group(0))
                for item in data:
                    if (
                        item.get("question")
                        and item.get("options")
                        and item.get("correct_answer")
                    ):
                        questions.append(
                            QuizQuestion(
                                quiz=quiz,
                                question_text=item["question"],
                                options=item["options"],
                                correct_answer=item["correct_answer"],
                                explanation=item.get("explanation", ""),
                            )
                        )
        except Exception as e:
            print(f"Erro ao gerar quiz via LLM: {e}")

    # Fallback/simulação de geração de quiz de acordo com os parâmetros
    if not questions:
        questions = [
            QuizQuestion(
                quiz=quiz,
                question_text=f"Sobre o conteúdo de '{doc.name}' focado em '{theme or 'Geral'}', qual alternativa descreve as melhores práticas?",
                options=[
                    "Escrever testes unitários e refatorar código legível seguindo a PEP8",
                    "Escrever código correndo sem se preocupar com testes ou estilo",
                    "Ignorar modularização e usar arquivos únicos gigantes",
                    "Não refatorar e duplicar lógicas de código",
                ],
                correct_answer="Escrever testes unitários e refatorar código legível seguindo a PEP8",
                explanation="Modularização, legibilidade seguindo a PEP8 e cobertura de testes são pilares fundamentais da engenharia de software.",
            )
        ]
        # Se pediu mais questões no fallback
        for idx in range(1, num_questions):
            questions.append(
                QuizQuestion(
                    quiz=quiz,
                    question_text=f"Questão {idx+1} [Simulada Nível {difficulty}]: Qual a melhor forma de validar o processamento correto?",
                    options=[
                        "Implementando testes automatizados adequados ao fluxo",
                        "Apenas checando logs manualmente uma vez",
                        "Confiando que o código sempre funcionará sem validações",
                        "Delegando toda a validação para o usuário final",
                    ],
                    correct_answer="Implementando testes automatizados adequados ao fluxo",
                    explanation="Garantir validações automáticas reduz a taxa de regressão e aumenta o desempenho geral do sistema.",
                )
            )

    QuizQuestion.objects.bulk_create(questions)
    return quiz
