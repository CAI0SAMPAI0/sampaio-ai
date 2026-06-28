import json
import re
from django.conf import settings
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from .models import StudyPlan

def generate_study_plan(user, objective, technology, available_hours, duration_weeks):
    """
    Gera um plano de estudos estruturado semanalmente para a tecnologia informada,
    adequado à carga horária do usuário. Utiliza IA (Groq) se disponível, senão gera conteúdo simulado de alta qualidade.
    """
    title = f"Plano de Estudos: {technology}"
    
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    plan_content = {}

    if groq_key and groq_key != 'gsk_placeholder_for_development' and groq_key != "":
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.5
            )
            prompt = (
                "Você é um mentor técnico especialista em programação. Crie um plano de estudos "
                f"para a tecnologia '{technology}', com o objetivo de '{objective}'. "
                f"O usuário tem {available_hours} horas disponíveis por semana, e a duração do plano é de {duration_weeks} semanas.\n\n"
                "Retorne APENAS um objeto JSON válido representando as semanas. Cada semana deve conter o número da semana, "
                "um tópico principal, uma lista de tarefas recomendadas e as horas sugeridas. Exemplo de formato de resposta:\n"
                "{\n"
                "  \"semanas\": [\n"
                "    {\n"
                "      \"semana\": 1,\n"
                "      \"topico\": \"Introdução\",\n"
                "      \"tarefas\": [\"Tarefa 1\", \"Tarefa 2\"],\n"
                "      \"horas_sugeridas\": 4\n"
                "    }\n"
                "  ]\n"
                "}\n"
                "Não inclua nenhum texto explicativo antes ou depois do JSON."
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(r'\{\s*\"semanas\".*\}', response.content, re.DOTALL)
            if match:
                plan_content = json.loads(match.group(0))
        except Exception as e:
            print(f"Erro ao gerar plano de estudos via LLM: {e}")

    # Fallback/simulação de plano de estudos
    if not plan_content:
        semanas = []
        for w in range(1, duration_weeks + 1):
            semanas.append({
                "semana": w,
                "topico": f"Fundamentos e Prática de {technology} - Parte {w}",
                "tarefas": [
                    f"Ler capítulos sugeridos de livros sobre {technology}",
                    "Codificar um pequeno projeto prático de validação",
                    "Escrever testes unitários e revisar com flashcards"
                ],
                "horas_sugeridas": max(2, available_hours)
            })
        plan_content = {"semanas": semanas}

    plan = StudyPlan.objects.create(
        user=user,
        title=title,
        objective=objective,
        technology=technology,
        available_hours_per_week=available_hours,
        duration_weeks=duration_weeks,
        plan_content=plan_content
    )
    return plan
