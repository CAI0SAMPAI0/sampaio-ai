import json
import re
import subprocess
import tempfile
import os
from celery import shared_task
from django.conf import settings


@shared_task(bind=True)
def invoke_chat_agent_task(self, session_id, user_id, messages_data):
    """
    Task assíncrona para invocar o agente LangGraph.
    Retorna o conteúdo da resposta do assistente.
    """
    from chat.models import ChatSession, ChatMessage
    from ai_agents.agent import langgraph_agent
    from langchain_core.messages import HumanMessage, AIMessage
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        ChatSession.objects.get(id=session_id, user_id=user_id)

        lc_messages = []
        for msg_data in messages_data:
            if msg_data['role'] == 'user':
                lc_messages.append(
                    HumanMessage(content=msg_data['content'])
                )
            else:
                lc_messages.append(
                    AIMessage(content=msg_data['content'])
                )

        initial_state = {
            "messages": lc_messages,
            "context": "",
            "web_context": "",
            "user": User.objects.get(id=user_id)
        }

        result = langgraph_agent.invoke(initial_state)
        assistant_content = result['messages'][-1].content
    except Exception as e:
        assistant_content = (
            "Desculpe, ocorreu um erro no processamento "
            f"do agente: {str(e)}"
        )

    ai_msg = ChatMessage.objects.create(
        session_id=session_id,
        role='assistant',
        content=assistant_content
    )

    return {
        'assistant_content': assistant_content,
        'assistant_message_id': ai_msg.id
    }


@shared_task(bind=True)
def submit_challenge_task(self, challenge_id, user_id, code):
    """
    Task assíncrona para executar código + gerar feedback via LLM.
    """
    from studies.models import DailyChallenge, ChallengeSubmission
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    try:
        challenge = DailyChallenge.objects.get(id=challenge_id)
    except DailyChallenge.DoesNotExist:
        return {'error': 'Desafio não encontrado.'}

    full_code = (
        f"{code}\n\n# --- TEST CASES ---\n{challenge.test_code}"
    )
    with tempfile.NamedTemporaryFile(
        suffix='.py', delete=False, mode='w', encoding='utf-8'
    ) as temp:
        temp.write(full_code)
        temp_path = temp.name

    passed = False
    exec_output = ""

    try:
        python_exec = os.sys.executable or "python"
        result = subprocess.run(
            [python_exec, temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        passed = (result.returncode == 0)
        if result.stdout or result.stderr:
            exec_output = (
                f"Stdout:\n{result.stdout}\n\n"
                f"Stderr:\n{result.stderr}"
            )
        else:
            exec_output = "Sem saída no terminal."
    except subprocess.TimeoutExpired:
        exec_output = "Erro: Tempo limite excedido (Timeout)."
    except Exception as e:
        exec_output = f"Erro ao executar código: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    feedback_text = ""

    if (
        groq_key
        and groq_key != 'gsk_placeholder_for_development'
        and groq_key != ""
    ):
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            prompt = (
                "Você é um analista especialista em revisão "
                "de código Python e PEP8.\n"
                f"Desafio: {challenge.title}\n"
                f"Instruções: {challenge.description}\n\n"
                f"Código:\n```python\n{code}\n```\n\n"
                f"Status: {'Aprovado' if passed else 'Falhou'}\n"
                f"Logs: {exec_output}\n\n"
                "Responda EXATAMENTE neste formato:\n"
                "NOTA: <de 0 a 10>\n\n"
                "### Correção\n<análise>\n\n"
                "### PEP8\n<dicas>\n\n"
                "### Simplificação\n<sugestões>\n\n"
                "### O que Estudar\n<tópicos>"
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            feedback_text = response.content
        except Exception as e:
            feedback_text = (
                f"Erro ao contatar IA: {e}\n\n"
                f"Status: {'Aprovado' if passed else 'Falhou'}\n"
                f"Logs: {exec_output}"
            )
    else:
        status_str = "Aprovado!" if passed else "Falhou."
        grade = "8" if passed else "3"
        feedback_text = (
            f"NOTA: {grade}\n\n"
            f"### Avaliação Simulada\n\n"
            f"**Status**: {status_str}\n"
            f"**Logs**: \n{exec_output}\n\n"
            "**Dicas PEP8**: 4 espaços, snake_case.\n"
            "**Estudar**: Funções, condicionais, exceções."
        )

    submission = ChallengeSubmission.objects.create(
        user_id=user_id,
        challenge=challenge,
        code=code,
        status='passed' if passed else 'failed',
        execution_output=exec_output,
        feedback=feedback_text
    )

    return {
        'status': submission.status,
        'execution_output': submission.execution_output,
        'feedback': submission.feedback
    }


@shared_task(bind=True)
def analyze_user_level_task(self, user_id, log_data):
    """
    Task assíncrona para analisar o nível do usuário via LLM.
    """
    from django.contrib.auth import get_user_model
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage

    User = get_user_model()

    log_str = ""
    for i, entry in enumerate(log_data):
        log_str += (
            f"Questão {i+1}: {entry.get('question')} | "
            f"Resposta: {entry.get('user_answer')} | "
            f"Correto: {entry.get('is_correct')} | "
            f"Nível: {entry.get('level')}\n"
        )

    system_prompt = (
        "Você é o mentor técnico da Sampaio AI.\n"
        "Níveis: iniciante, junior, pleno, senior.\n"
        "Analise acertos/erros e defina o nível.\n"
        "JSON: {\"level\": \"...\", \"feedback\": \"...\"}"
    )

    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    ai_level = "junior"
    ai_feedback = "Continue estudando para melhorar."

    if (
        groq_key
        and groq_key != 'gsk_placeholder_for_development'
        and groq_key != ""
    ):
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.2
            )
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Log:\n{log_str}")
            ])
            try:
                res_json = json.loads(response.content.strip())
                ai_level = res_json.get(
                    'level', ai_level
                ).lower().strip()
                ai_feedback = res_json.get(
                    'feedback', ai_feedback
                )
            except Exception:
                match = re.search(
                    r'\{.*\}', response.content, re.DOTALL
                )
                if match:
                    res_json = json.loads(match.group(0))
                    ai_level = res_json.get(
                        'level', ai_level
                    ).lower().strip()
                    ai_feedback = res_json.get(
                        'feedback', ai_feedback
                    )
        except Exception:
            pass

    correct_count = sum(
        1 for entry in log_data if entry.get('is_correct')
    )
    if (
        not groq_key
        or groq_key == 'gsk_placeholder_for_development'
        or groq_key == ""
    ):
        if correct_count >= 8:
            ai_level = "senior"
            ai_feedback = "Excelente domínio!"
        elif correct_count >= 5:
            ai_level = "pleno"
            ai_feedback = "Bom domínio."
        elif correct_count >= 3:
            ai_level = "junior"
            ai_feedback = "Boa base."
        else:
            ai_level = "iniciante"
            ai_feedback = "Continue!"

    valid_levels = ['iniciante', 'junior', 'pleno', 'senior']
    if ai_level not in valid_levels:
        ai_level = "junior"

    user = User.objects.get(id=user_id)
    user.level = ai_level
    user.save()

    return {
        'level': ai_level,
        'level_display': user.get_level_display(),
        'feedback': ai_feedback
    }


@shared_task(bind=True)
def verify_flashcard_answer_task(self, flashcard_id, user_answer):
    """
    Task assíncrona para verificar resposta do flashcard via LLM.
    """
    from flashcards.models import Flashcard
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    try:
        flashcard = Flashcard.objects.get(id=flashcard_id)
    except Flashcard.DoesNotExist:
        return {'error': 'Flashcard não encontrado.'}

    groq_key = getattr(settings, 'GROQ_API_KEY', None)

    if (
        groq_key
        and groq_key != 'gsk_placeholder_for_development'
        and groq_key != ""
    ):
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.2
            )
            prompt = (
                "Compare a resposta do usuário com a esperada.\n"
                f"Pergunta: {flashcard.front}\n"
                f"Correta: {flashcard.back}\n"
                f"Usuário: {user_answer}\n\n"
                "JSON: {\"correct\": bool, \"score\": 0-100, "
                "\"feedback\": \"...\"}"
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(
                r'\{.*\}', response.content, re.DOTALL
            )
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass

    import difflib
    ratio = difflib.SequenceMatcher(
        None, user_answer.lower(), flashcard.back.lower()
    ).ratio()
    score = int(ratio * 100)
    return {
        'correct': score >= 50,
        'score': score,
        'feedback': f"Similaridade: {score}%."
    }


@shared_task(bind=True)
def generate_flashcards_task(self, document_id, user_id):
    """
    Task assíncrona para gerar flashcards via LLM.
    """
    from flashcards.models import Flashcard
    from uploads.models import KnowledgeDocument
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    try:
        doc = KnowledgeDocument.objects.get(
            id=document_id, user_id=user_id
        )
    except KnowledgeDocument.DoesNotExist:
        return {'error': 'Documento não encontrado.'}

    chunks = doc.chunks.all()[:3]
    text_content = "\n".join([c.content for c in chunks])
    if not text_content:
        text_content = f"Estudos sobre {doc.name}"

    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    flashcard_objs = []

    if (
        groq_key
        and groq_key != 'gsk_placeholder_for_development'
        and groq_key != ""
    ):
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            prompt = (
                "Gere 3-5 flashcards. "
                "JSON: [{\"front\": \"...\", \"back\": \"...\"}]\n\n"
                f"Texto:\n{text_content}"
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(
                r'\[\s*\{.*\}\s*\]', response.content, re.DOTALL
            )
            if match:
                data = json.loads(match.group(0))
                for item in data:
                    if item.get('front') and item.get('back'):
                        flashcard_objs.append(Flashcard(
                            user_id=user_id, document=doc,
                            front=item['front'],
                            back=item['back']
                        ))
        except Exception:
            pass

    if not flashcard_objs:
        flashcard_objs = [
            Flashcard(
                user_id=user_id, document=doc,
                front=f"Conceito de {doc.name}?",
                back=f"Tópicos de {doc.name}."
            ),
        ]

    Flashcard.objects.bulk_create(flashcard_objs)
    return {
        'count': len(flashcard_objs),
        'flashcards': [
            {'front': f.front, 'back': f.back}
            for f in flashcard_objs
        ]
    }


@shared_task(bind=True)
def generate_quiz_task(
    self, document_id, user_id,
    theme=None, num_questions=3, difficulty="Médio"
):
    """
    Task assíncrona para gerar quiz via LLM.
    """
    from quizzes.models import Quiz, QuizQuestion
    from uploads.models import KnowledgeDocument
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    try:
        doc = KnowledgeDocument.objects.get(
            id=document_id, user_id=user_id
        )
    except KnowledgeDocument.DoesNotExist:
        return {'error': 'Documento não encontrado.'}

    chunks = doc.chunks.all()[:3]
    text_content = "\n".join([c.content for c in chunks])
    if not text_content:
        text_content = f"Estudos sobre {doc.name}"

    title = f"Quiz sobre {doc.name}"
    if theme:
        title += f" (Tema: {theme})"

    quiz = Quiz.objects.create(
        user_id=user_id, document=doc, title=title
    )

    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    questions = []

    if (
        groq_key
        and groq_key != 'gsk_placeholder_for_development'
        and groq_key != ""
    ):
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            prompt = (
                f"Gere {num_questions} perguntas múltipla escolha.\n"
                f"Tema: {theme or 'Geral'}\n"
                f"Dificuldade: {difficulty}\n\n"
                "JSON: [{\"question\": \"...\", "
                "\"options\": [4 strings], "
                "\"correct_answer\": \"...\", "
                "\"explanation\": \"...\"}]\n\n"
                f"Texto:\n{text_content}"
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(
                r'\[\s*\{.*\}\s*\]', response.content, re.DOTALL
            )
            if match:
                data = json.loads(match.group(0))
                for item in data:
                    if (
                        item.get('question')
                        and item.get('options')
                        and item.get('correct_answer')
                    ):
                        questions.append(QuizQuestion(
                            quiz=quiz,
                            question_text=item['question'],
                            options=item['options'],
                            correct_answer=item['correct_answer'],
                            explanation=item.get(
                                'explanation', ''
                            )
                        ))
        except Exception:
            pass

    if not questions:
        questions = [
            QuizQuestion(
                quiz=quiz,
                question_text=(
                    f"Melhores práticas em {doc.name}?"
                ),
                options=[
                    "Testes e PEP8",
                    "Sem testes",
                    "Arquivos gigantes",
                    "Sem refatoração"
                ],
                correct_answer="Testes e PEP8",
                explanation="Fundamental."
            )
        ]

    QuizQuestion.objects.bulk_create(questions)
    return {
        'quiz_id': quiz.id,
        'question_count': len(questions)
    }


@shared_task(bind=True)
def generate_study_plan_task(
    self, user_id, objective, technology,
    available_hours, duration_weeks
):
    """
    Task assíncrona para gerar plano de estudos via LLM.
    """
    from studies.models import StudyPlan
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage

    title = f"Plano de Estudos: {technology}"
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    plan_content = {}

    if (
        groq_key
        and groq_key != 'gsk_placeholder_for_development'
        and groq_key != ""
    ):
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.5
            )
            prompt = (
                f"Plano de estudos: '{technology}', "
                f"objetivo: '{objective}'. "
                f"{available_hours}h/semana, "
                f"{duration_weeks} semanas.\n"
                "JSON: {\"semanas\": [{\"semana\": 1, "
                "\"topico\": \"...\", "
                "\"tarefas\": [...], "
                "\"horas_sugeridas\": 4}]}"
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            match = re.search(
                r'\{\s*"semanas".*\}',
                response.content, re.DOTALL
            )
            if match:
                plan_content = json.loads(match.group(0))
        except Exception:
            pass

    if not plan_content:
        semanas = []
        for w in range(1, duration_weeks + 1):
            semanas.append({
                "semana": w,
                "topico": f"{technology} - Parte {w}",
                "tarefas": [
                    f"Ler sobre {technology}",
                    "Praticar com projetos"
                ],
                "horas_sugeridas": max(2, available_hours)
            })
        plan_content = {"semanas": semanas}

    plan = StudyPlan.objects.create(
        user_id=user_id, title=title, objective=objective,
        technology=technology,
        available_hours_per_week=available_hours,
        duration_weeks=duration_weeks,
        plan_content=plan_content
    )
    return {'plan_id': plan.id}
