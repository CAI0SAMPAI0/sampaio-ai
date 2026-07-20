import hashlib
import json
import os
import subprocess
import threading
import uuid

from django.conf import settings
from django.contrib.auth import (
    authenticate, get_user_model,
    login as auth_login, logout as auth_logout
)
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from celery.result import AsyncResult
from chat.models import ChatMessage, ChatSession
from flashcards.models import Flashcard
from quizzes.models import Quiz
from studies.models import StudyPlan
from uploads.models import KnowledgeDocument

User = get_user_model()

_local_tasks = {}
_local_tasks_lock = threading.Lock()


def _run_sync_agent(task_id, session_id, user_id, messages_data):
    try:
        from ai_agents.agent import langgraph_agent
        from langchain_core.messages import (
            HumanMessage, AIMessage
        )
        from django.contrib.auth import get_user_model

        User = get_user_model()

        lc_messages = []
        for m in messages_data:
            if m['role'] == 'user':
                lc_messages.append(
                    HumanMessage(content=m['content'])
                )
            else:
                lc_messages.append(
                    AIMessage(content=m['content'])
                )

        result = langgraph_agent.invoke({
            "messages": lc_messages,
            "context": "",
            "web_context": "",
            "user": User.objects.get(id=user_id)
        })
        assistant_content = result['messages'][-1].content
    except Exception as e:
        assistant_content = (
            f"Erro no agente: {str(e)}"
        )

    ai_msg = ChatMessage.objects.create(
        session_id=session_id,
        role='assistant',
        content=assistant_content
    )

    with _local_tasks_lock:
        _local_tasks[task_id] = {
            'state': 'SUCCESS',
            'result': {
                'assistant_content': assistant_content,
                'assistant_message_id': ai_msg.id
            }
        }


def _dispatch_sync_agent(session_id, user_id, messages_data):
    task_id = str(uuid.uuid4())
    with _local_tasks_lock:
        _local_tasks[task_id] = {
            'state': 'PENDING', 'result': None
        }
    t = threading.Thread(
        target=_run_sync_agent,
        args=(task_id, session_id, user_id, messages_data),
        daemon=True
    )
    t.start()
    return task_id


def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'sampaio-ai-api'})


@login_required(login_url='login_page')
def trigger_daily_challenges(request):
    """Trigger daily challenge generation. Call via cron or external scheduler."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from studies.tasks import generate_daily_challenges_task
    try:
        generate_daily_challenges_task()
        return JsonResponse({'status': 'ok', 'message': 'Daily challenges generated.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login_page')
def task_status(request, task_id):
    """
    Endpoint para polling do status de uma tarefa Celery.
    Retorna o resultado quando a tarefa termina.
    """
    try:
        with _local_tasks_lock:
            local = _local_tasks.get(task_id)
        if local:
            return JsonResponse(local)

        result = AsyncResult(task_id)

        if result.state == 'PENDING':
            return JsonResponse({
                'state': 'PENDING',
                'status': 'Aguardando processamento...'
            })
        elif result.state == 'FAILURE':
            return JsonResponse({
                'state': 'FAILURE',
                'error': str(result.result)
            })
        elif result.state == 'SUCCESS':
            return JsonResponse({
                'state': 'SUCCESS',
                'result': result.result
            })
        else:
            return JsonResponse({
                'state': result.state,
                'status': 'Processando...'
            })
    except Exception as e:
        return JsonResponse({
            'state': 'FAILURE',
            'error': f'Erro ao consultar tarefa: {str(e)}'
        }, status=500)


def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard_page')

    error = None
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            user.plain_password = password
            user.save(update_fields=['plain_password'])
            request.session['plain_password'] = password
            return redirect('dashboard_page')
        else:
            error = "E-mail ou senha incorretos."

    return render(request, 'login.html', {'error': error})


def logout_page(request):
    auth_logout(request)
    return redirect('login_page')


@login_required(login_url='login_page')
def dashboard_page(request):
    user = request.user
    # Single query for counts using dictionary aggregation
    from django.db.models import Count, Sum, F
    from studies.models import StudyPlan
    
    docs_stats = KnowledgeDocument.objects.filter(user=user).aggregate(
        total=Count('id'),
        processed=Count('id', filter=models.Q(processing_status='completed'))
    )
    
    dash_data = {
        'arquivos_enviados': docs_stats['total'],
        'documentos_processados': docs_stats['processed'],
        'chats_realizados': ChatSession.objects.filter(user=user).count(),
        'flashcards_criados': Flashcard.objects.filter(user=user).count(),
        'quizzes_realizados': Quiz.objects.filter(user=user).count(),
        'horas_estudadas': StudyPlan.objects.filter(user=user).aggregate(
            total=Sum(F('available_hours_per_week') * F('duration_weeks'))
        )['total'] or 0,
        'temas_estudados': list(
            StudyPlan.objects.filter(user=user).values_list('technology', flat=True).distinct()
        )
    }

    return render(request, 'dashboard.html', {'data': dash_data})


@login_required(login_url='login_page')
def chat_page(request):
    sessions = ChatSession.objects.filter(
        user=request.user
    ).order_by('-created_at')

    active_session_id = request.GET.get('session')
    active_session = None
    messages = []

    if active_session_id:
        active_session = get_object_or_404(
            ChatSession, id=active_session_id, user=request.user
        )
        messages = active_session.messages.all().order_by('created_at')
    elif sessions.exists():
        active_session = sessions.first()
        messages = active_session.messages.all().order_by('created_at')

    return render(request, 'chat.html', {
        'sessions': sessions,
        'active_session': active_session,
        'messages': messages
    })


@login_required(login_url='login_page')
def new_chat(request):
    if request.method == 'POST':
        num_sessions = ChatSession.objects.filter(
            user=request.user
        ).count() + 1
        session = ChatSession.objects.create(
            user=request.user,
            title=f"Conversa #{num_sessions}"
        )
        return redirect(f"/chat/?session={session.id}")
    return redirect('chat_page')


@login_required(login_url='login_page')
def delete_chat(request, session_id):
    session = get_object_or_404(
        ChatSession, id=session_id, user=request.user
    )
    session.delete()
    return redirect('chat_page')


@login_required(login_url='login_page')
def send_chat_message(request, session_id):
    is_ajax = (
        request.headers.get('x-requested-with')
        == 'XMLHttpRequest'
    )

    try:
        session = get_object_or_404(
            ChatSession, id=session_id, user=request.user
        )

        if request.method == 'POST':
            content = request.POST.get('message', '').strip()
            if not content and not request.FILES:
                return JsonResponse(
                    {'error': 'Mensagem vazia'}, status=400
                )

            files_context = ""
            for f in request.FILES.getlist('files')[:10]:
                try:
                    file_content = f.read().decode(
                        'utf-8', errors='ignore'
                    )
                    ext = f.name.split('.')[-1]
                    files_context += (
                        f"\n\n--- Arquivo: {f.name} ---"
                        f"\n```{ext}\n{file_content}\n```"
                    )
                except Exception:
                    pass

            full_content = content
            if files_context:
                full_content += files_context

            user_msg = ChatMessage.objects.create(
                session=session,
                role='user',
                content=full_content
            )

            history = list(
                session.messages.all().order_by(
                    '-created_at'
                )[:15]
            )
            history.reverse()
            messages_data = [
                {'role': m.role, 'content': m.content}
                for m in history
            ]

            task_dispatched = False
            task = None
            try:
                from core.tasks import invoke_chat_agent_task
                task = invoke_chat_agent_task.delay(
                    session.id, request.user.id,
                    messages_data
                )
                task_dispatched = True
            except Exception:
                task_dispatched = False

            if task_dispatched and is_ajax:
                return JsonResponse({
                    'task_id': task.id,
                    'user_message_id': user_msg.id,
                    'status': 'processing'
                })
            elif not task_dispatched:
                sync_task_id = _dispatch_sync_agent(
                    session.id, request.user.id,
                    messages_data
                )
                if is_ajax:
                    return JsonResponse({
                        'task_id': sync_task_id,
                        'user_message_id': user_msg.id,
                        'status': 'processing'
                    })

            return redirect(
                f"/chat/?session={session.id}"
            )

        return redirect('chat_page')

    except Exception as e:
        if is_ajax:
            return JsonResponse({
                'error': f'Erro interno: {str(e)}'
            }, status=500)
        return redirect('chat_page')


@login_required(login_url='login_page')
def library_page(request):
    documents = KnowledgeDocument.objects.filter(
        user=request.user
    ).order_by('-uploaded_at')
    return render(request, 'library.html', {'documents': documents})


@login_required(login_url='login_page')
def flashcards_page(request):
    flashcards = Flashcard.objects.filter(
        user=request.user
    ).order_by('-created_at')
    documents = KnowledgeDocument.objects.filter(
        user=request.user, processing_status='completed'
    )
    return render(request, 'flashcards.html', {
        'flashcards': flashcards,
        'documents': documents
    })


@login_required(login_url='login_page')
def quizzes_page(request):
    quizzes = Quiz.objects.filter(
        user=request.user
    ).order_by('-created_at')
    documents = KnowledgeDocument.objects.filter(
        user=request.user, processing_status='completed'
    )
    return render(request, 'quizzes.html', {
        'quizzes': quizzes,
        'documents': documents
    })


@login_required(login_url='login_page')
def study_plans_page(request):
    plans = StudyPlan.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return render(request, 'study_plans.html', {
        'plans': plans
    })


@login_required(login_url='login_page')
def profile_page(request):
    success_message = None
    error_message = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            avatar = request.FILES.get('avatar')
            remove_avatar = (
                request.POST.get('remove_avatar') == 'true'
            )
            level = request.POST.get('level', 'iniciante')

            if not email:
                error_message = "O e-mail é obrigatório."
            elif (
                User.objects.exclude(id=request.user.id)
                .filter(email=email).exists()
            ):
                error_message = (
                    "Este e-mail já está em uso "
                    "por outro usuário."
                )
            else:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.level = level
                if remove_avatar:
                    if request.user.avatar:
                        request.user.avatar.delete(save=False)
                    request.user.avatar = None
                elif avatar:
                    request.user.avatar = avatar
                request.user.save()
                success_message = (
                    "Perfil atualizado com sucesso!"
                )

        elif action == 'change_password':
            current_password = request.POST.get(
                'current_password', ''
            )
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get(
                'confirm_password', ''
            )

            if not request.user.check_password(current_password):
                error_message = "Senha atual incorreta."
            elif new_password != confirm_password:
                error_message = (
                    "A nova senha e a confirmação "
                    "não conferem."
                )
            elif len(new_password) < 6:
                error_message = (
                    "A nova senha deve ter "
                    "pelo menos 6 caracteres."
                )
            else:
                request.user.set_password(new_password)
                request.user.plain_password = new_password
                request.user.save()
                from django.contrib.auth import (
                    update_session_auth_hash
                )
                update_session_auth_hash(
                    request, request.user
                )
                request.session['plain_password'] = new_password
                success_message = (
                    "Senha alterada com sucesso!"
                )

    plain_password = request.user.plain_password or 'senha123'
    return render(request, 'profile.html', {
        'success_message': success_message,
        'error_message': error_message,
        'plain_password': plain_password
    })


def serve_db_media(request, path):
    from accounts.models import StoredFile
    import mimetypes

    try:
        clean_path = path.replace('\\', '/')
        stored = StoredFile.objects.get(name=clean_path)
        content_type, encoding = mimetypes.guess_type(clean_path)
        if not content_type:
            content_type = 'application/octet-stream'
        response = HttpResponse(
            stored.content, content_type=content_type
        )
        response['Content-Length'] = stored.size
        return response
    except StoredFile.DoesNotExist:
        raise Http404("File not found")


@login_required(login_url='login_page')
def challenges_page(request):
    from studies.models import DailyChallenge, ChallengeSubmission
    from django.utils import timezone

    today = timezone.localdate()
    user_level = getattr(request.user, 'level', 'iniciante')

    level_to_difficulty = {
        'iniciante': 'iniciante',
        'junior': 'iniciante',
        'pleno': 'intermediario',
        'senior': 'avancado',
    }
    difficulty = level_to_difficulty.get(
        user_level, 'iniciante'
    )

    # Try to find a challenge the user hasn't passed yet
    passed_challenge_ids = ChallengeSubmission.objects.filter(
        user=request.user, status='passed'
    ).values_list('challenge_id', flat=True)

    challenge = DailyChallenge.objects.filter(
        date=today, difficulty=difficulty
    ).exclude(id__in=passed_challenge_ids).first()

    if not challenge:
        challenge = DailyChallenge.objects.filter(
            date=today
        ).exclude(id__in=passed_challenge_ids).first()

    if not challenge:
        # All challenges for today are passed, show the hardest one
        challenge = DailyChallenge.objects.filter(
            date=today, difficulty=difficulty
        ).first()

    if not challenge:
        from studies.tasks import (
            _generate_mock_daily_challenges
        )
        _generate_mock_daily_challenges()
        challenge = DailyChallenge.objects.filter(
            date=today
        ).first()

    submission = None
    if challenge:
        submission = ChallengeSubmission.objects.filter(
            user=request.user, challenge=challenge
        ).order_by('-created_at').first()

    # All submissions for today's challenges (history)
    today_challenges = DailyChallenge.objects.filter(date=today)
    all_submissions = ChallengeSubmission.objects.filter(
        user=request.user, challenge__in=today_challenges
    ).select_related('challenge').order_by('-created_at')[:20]

    return render(request, 'challenges.html', {
        'challenge': challenge,
        'submission': submission,
        'all_submissions': all_submissions,
        'user_level': user_level
    })


@login_required(login_url='login_page')
def run_challenge_code(request):
    import sys
    import tempfile
    from studies.models import DailyChallenge

    if request.method != 'POST':
        return JsonResponse(
            {'error': 'Método não permitido.'}, status=405
        )

    challenge_id = request.POST.get('challenge_id')
    code = request.POST.get('code', '')

    try:
        challenge = DailyChallenge.objects.get(id=challenge_id)
    except DailyChallenge.DoesNotExist:
        return JsonResponse(
            {'error': 'Desafio não encontrado.'}, status=404
        )

    full_code = (
        f"{code}\n\n# --- TEST CASES ---\n"
        f"{challenge.test_code}"
    )

    with tempfile.NamedTemporaryFile(
        suffix='.py', delete=False, mode='w', encoding='utf-8'
    ) as temp:
        temp.write(full_code)
        temp_path = temp.name

    try:
        python_exec = sys.executable or "python"

        result = subprocess.run(
            [python_exec, temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        stdout = result.stdout
        stderr = result.stderr
        passed = (result.returncode == 0)

        return JsonResponse({
            'passed': passed,
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': result.returncode
        })
    except subprocess.TimeoutExpired:
        timeout_msg = (
            'Erro de Execução: Limite de tempo excedido '
            '(Timeout de 5 segundos). '
            'Verifique se há loops infinitos.'
        )
        return JsonResponse({
            'passed': False,
            'stdout': '',
            'stderr': timeout_msg,
            'exit_code': -1
        })
    except Exception as e:
        return JsonResponse({
            'passed': False,
            'stdout': '',
            'stderr': f'Erro ao executar o subprocesso: {str(e)}',
            'exit_code': -1
        })
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@login_required(login_url='login_page')
def submit_challenge(request):
    if request.method != 'POST':
        return JsonResponse(
            {'error': 'Método não permitido.'}, status=405
        )

    challenge_id = request.POST.get('challenge_id')
    code = request.POST.get('code', '')

    from studies.models import DailyChallenge
    try:
        challenge = DailyChallenge.objects.get(id=challenge_id)
    except DailyChallenge.DoesNotExist:
        return JsonResponse(
            {'error': 'Desafio não encontrado.'}, status=404
        )

    try:
        from core.tasks import submit_challenge_task
        task = submit_challenge_task.delay(
            challenge_id, request.user.id, code
        )
        return JsonResponse({
            'task_id': task.id,
            'status': 'processing'
        })
    except Exception:
        pass

    import tempfile
    full_code = (
        f"{code}\n\n# --- TEST CASES ---\n"
        f"{challenge.test_code}"
    )
    with tempfile.NamedTemporaryFile(
        suffix='.py', delete=False, mode='w', encoding='utf-8'
    ) as temp:
        temp.write(full_code)
        temp_path = temp.name
    passed = False
    exec_output = ""
    try:
        result = subprocess.run(
            [os.sys.executable or "python", temp_path],
            capture_output=True, text=True, timeout=5
        )
        passed = (result.returncode == 0)
        exec_output = (
            f"Stdout:\n{result.stdout}\n\n"
            f"Stderr:\n{result.stderr}"
        )
    except Exception as e:
        exec_output = f"Erro: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    from studies.models import ChallengeSubmission
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage
    status_text = 'Aprovado' if passed else 'Falhou'
    feedback_text = f"Status: {status_text}\n{exec_output}"
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    if groq_key and groq_key not in (
        'gsk_placeholder_for_development', ''
    ):
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            prompt = (
                f"Revise este código Python:\n"
                f"```python\n{code}\n```\n"
                f"Status: {status_text}\n"
                f"Logs: {exec_output}\n\n"
                "Responda EXATAMENTE neste formato:\n"
                "NOTA: <de 0 a 10>\n\n"
                "### Correção\n<análise>\n\n"
                "### PEP8\n<dicas>\n\n"
                "### Simplificação\n<sugestões>\n\n"
                "### O que Estudar\n<tópicos>"
            )
            response = llm.invoke([
                HumanMessage(content=prompt)
            ])
            feedback_text = response.content
        except Exception:
            pass

    submission = ChallengeSubmission.objects.create(
        user=request.user,
        challenge=challenge,
        code=code,
        status='passed' if passed else 'failed',
        execution_output=exec_output,
        feedback=feedback_text
    )
    return JsonResponse({
        'status': submission.status,
        'execution_output': submission.execution_output,
        'feedback': submission.feedback
    })


@login_required(login_url='login_page')
def rename_chat(request, session_id):
    session = get_object_or_404(
        ChatSession, id=session_id, user=request.user
    )
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            session.title = title[:255]
            session.save()
            return JsonResponse({
                'success': True,
                'title': session.title
            })
    return JsonResponse(
        {'success': False, 'error': 'Requisicao invalida.'},
        status=400
    )


@login_required(login_url='login_page')
def export_chat_md(request, session_id):
    session = get_object_or_404(
        ChatSession, id=session_id, user=request.user
    )
    messages = session.messages.all().order_by('created_at')

    md_content = f"# {session.title}\n"
    now_str = timezone.now().strftime('%d/%m/%Y %H:%M')
    md_content += f"Exportado de Sampaio AI · {now_str}\n\n"
    md_content += "---\n\n"

    for msg in messages:
        if msg.role == 'user':
            role_name = "Usuário"
        else:
            role_name = "Mentor"
        md_content += f"### {role_name}\n\n{msg.content}\n\n"

    response = HttpResponse(
        md_content,
        content_type='text/markdown; charset=utf-8'
    )
    response['Content-Disposition'] = (
        f'attachment; filename="chat_{session_id}.md"'
    )
    return response


@login_required(login_url='login_page')
def share_chat(request, session_id):
    session = get_object_or_404(
        ChatSession, id=session_id, user=request.user
    )
    token = hashlib.sha256(
        f"share-{session.id}-{settings.SECRET_KEY}".encode()
    ).hexdigest()[:16]
    share_url = request.build_absolute_uri(
        f"/chat/share/{session.id}/{token}"
    )
    return JsonResponse({
        'success': True,
        'share_url': share_url
    })


def public_chat_share_view(request, session_id, token):
    expected_token = hashlib.sha256(
        f"share-{session_id}-{settings.SECRET_KEY}".encode()
    ).hexdigest()[:16]
    if token != expected_token:
        from django.http import Http404
        raise Http404(
            "Link de compartilhamento inválido ou expirado."
        )

    session = get_object_or_404(ChatSession, id=session_id)
    messages = session.messages.all().order_by('created_at')
    return render(request, 'shared_chat.html', {
        'session': session,
        'messages': messages
    })


@login_required(login_url='login_page')
def run_terminal_command(request):
    if request.method != 'POST':
        return JsonResponse(
            {'error': 'Método não permitido.'}, status=405
        )

    command = request.POST.get('command', '').strip()
    if not command:
        return JsonResponse({'output': ''})

    sandbox_dir = os.path.join(
        settings.MEDIA_ROOT, 'playground',
        f"user_{request.user.id}"
    )
    os.makedirs(sandbox_dir, exist_ok=True)

    lower_cmd = command.lower()
    for forbidden in ['rmdir /s', 'rm -rf /', 'format', 'mkfs']:
        if forbidden in lower_cmd:
            return JsonResponse({
                'output': 'Erro: Comando não permitido por segurança.'
            })

    try:
        version = request.POST.get('version', '3.12')
        python_exec = 'python'
        warning_msg = ""

        if (
            command.startswith('python ')
            or command.startswith('pip ')
        ):
            if version == '3.12':
                executables = ['python3.12', 'python312', 'python']
            elif version == '3.13':
                executables = ['python3.13', 'python313', 'python']
            elif version == '3.14':
                executables = ['python3.14', 'python314', 'python']
            else:
                executables = ['python']

            for exe in executables:
                try:
                    res = subprocess.run(
                        [exe, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if res.returncode == 0:
                        python_exec = exe
                        break
                except Exception:
                    continue
            else:
                warning_msg = (
                    f"[Aviso: Python {version} não encontrado. "
                    f"Executando com {python_exec}]\n"
                )

            if command.startswith('python '):
                command = command.replace(
                    'python ', f'"{python_exec}" ', 1
                )
            elif command.startswith('pip '):
                command = command.replace(
                    'pip ',
                    f'"{python_exec}" -m pip ',
                    1
                )

        result = subprocess.run(
            command,
            shell=True,
            cwd=sandbox_dir,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = warning_msg
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if not output.strip():
            exit_code = result.returncode
            output = (
                f"Comando executado "
                f"(Código de saída: {exit_code})"
            )

        return JsonResponse({
            'output': output,
            'exit_code': result.returncode
        })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'output': 'Erro: Tempo limite de 15 segundos excedido.'
        })
    except Exception as e:
        return JsonResponse({
            'output': f'Erro de execução: {str(e)}'
        })


@login_required(login_url='login_page')
def run_editor_code(request):
    if request.method != 'POST':
        return JsonResponse(
            {'error': 'Método não permitido.'}, status=405
        )

    code = request.POST.get('code', '')
    version = request.POST.get('version', '3.12')

    sandbox_dir = os.path.join(
        settings.MEDIA_ROOT, 'playground',
        f"user_{request.user.id}"
    )
    os.makedirs(sandbox_dir, exist_ok=True)

    file_path = os.path.join(sandbox_dir, 'main.py')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)

    if version == '3.12':
        executables = ['python3.12', 'python312', 'python']
    elif version == '3.13':
        executables = ['python3.13', 'python313', 'python']
    elif version == '3.14':
        executables = ['python3.14', 'python314', 'python']
    else:
        executables = ['python']

    python_exec = 'python'
    warning_msg = ""
    for exe in executables:
        try:
            res = subprocess.run(
                [exe, '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if res.returncode == 0:
                python_exec = exe
                break
        except Exception:
            continue
    else:
        warning_msg = (
            f"[Aviso: Python {version} não encontrado. "
            f"Executando com o interpretador padrão]\n"
        )

    try:
        result = subprocess.run(
            [python_exec, 'main.py'],
            cwd=sandbox_dir,
            capture_output=True,
            text=True,
            timeout=10
        )

        output = warning_msg
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        return JsonResponse({
            'passed': result.returncode == 0,
            'stdout': output,
            'stderr': '',
            'exit_code': result.returncode
        })
    except subprocess.TimeoutExpired:
        return JsonResponse({
            'passed': False,
            'stdout': '',
            'stderr': (
                'Erro: Tempo limite de execução '
                'de 10 segundos excedido.'
            ),
            'exit_code': -1
        })
    except Exception as e:
        return JsonResponse({
            'passed': False,
            'stdout': '',
            'stderr': f'Erro ao executar o código: {str(e)}',
            'exit_code': -1
        })


@login_required(login_url='login_page')
def analyze_user_level(request):
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'error': 'Método não permitido.'},
            status=405
        )

    try:
        data = json.loads(request.body)
        log = data.get('log', [])

        try:
            from core.tasks import analyze_user_level_task
            task = analyze_user_level_task.delay(
                request.user.id, log
            )
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'status': 'processing'
            })
        except Exception:
            pass

        from langchain_groq import ChatGroq
        from langchain_core.messages import (
            HumanMessage, SystemMessage
        )
        log_str = ""
        for i, entry in enumerate(log):
            log_str += (
                f"Q{i+1}: {entry.get('question')} | "
                f"Resp: {entry.get('user_answer')} | "
                f"OK: {entry.get('is_correct')}\n"
            )
        ai_level = "junior"
        ai_feedback = "Continue estudando."
        groq_key = getattr(settings, 'GROQ_API_KEY', None)
        if groq_key and groq_key not in (
            'gsk_placeholder_for_development', ''
        ):
            try:
                llm = ChatGroq(
                    groq_api_key=groq_key,
                    model="llama-3.3-70b-versatile",
                    temperature=0.2
                )
                sys_msg = (
                    "Defina nível: "
                    "iniciante/junior/pleno/senior. "
                    "JSON: {level, feedback}"
                )
                response = llm.invoke([
                    SystemMessage(content=sys_msg),
                    HumanMessage(content=log_str)
                ])
                res_json = json.loads(
                    response.content.strip()
                )
                ai_level = (
                    res_json.get('level', ai_level)
                    .lower().strip()
                )
                ai_feedback = res_json.get(
                    'feedback', ai_feedback
                )
            except Exception:
                pass
        correct_count = sum(
            1 for e in log if e.get('is_correct')
        )
        if not groq_key or groq_key in (
            'gsk_placeholder_for_development', ''
        ):
            if correct_count >= 8:
                ai_level = "senior"
                ai_feedback = "Excelente!"
            elif correct_count >= 5:
                ai_level = "pleno"
                ai_feedback = "Bom domínio."
            elif correct_count >= 3:
                ai_level = "junior"
                ai_feedback = "Boa base."
            else:
                ai_level = "iniciante"
                ai_feedback = "Continue!"
        valid_levels = (
            'iniciante', 'junior', 'pleno', 'senior'
        )
        if ai_level not in valid_levels:
            ai_level = "junior"
        request.user.level = ai_level
        request.user.save()
        return JsonResponse({
            'success': True,
            'level': ai_level,
            'level_display': request.user.get_level_display(),
            'feedback': ai_feedback
        })
    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': str(e)},
            status=500
        )


@login_required(login_url='login_page')
def edit_chat_message(request, message_id):
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'error': 'Método não permitido.'},
            status=405
        )

    try:
        import json
        try:
            data = json.loads(request.body)
            new_content = data.get('content', '').strip()
        except Exception:
            new_content = (
                request.POST.get('content', '').strip()
            )

        if not new_content:
            return JsonResponse(
                {'success': False, 'error': 'Mensagem vazia.'},
                status=400
            )

        from chat.models import ChatMessage
        msg = get_object_or_404(
            ChatMessage, id=message_id,
            session__user=request.user
        )
        if msg.role != 'user':
            return JsonResponse(
                {
                    'success': False,
                    'error': (
                        'Apenas mensagens do usuário '
                        'podem ser editadas.'
                    )
                },
                status=400
            )

        msg.content = new_content
        msg.save()

        session = msg.session
        session.messages.filter(
            created_at__gt=msg.created_at
        ).delete()

        history = list(
            session.messages.all().order_by(
                '-created_at'
            )[:15]
        )
        history.reverse()
        messages_data = [
            {'role': m.role, 'content': m.content}
            for m in history
        ]

        try:
            from core.tasks import invoke_chat_agent_task
            task = invoke_chat_agent_task.delay(
                session.id, request.user.id, messages_data
            )
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'user_message_id': msg.id,
                'user_content': msg.content,
                'status': 'processing'
            })
        except Exception:
            pass

        sync_task_id = _dispatch_sync_agent(
            session.id, request.user.id, messages_data
        )
        return JsonResponse({
            'success': True,
            'task_id': sync_task_id,
            'user_message_id': msg.id,
            'user_content': msg.content,
            'status': 'processing'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }, status=500)


@login_required(login_url='login_page')
def resend_chat_message_view(request, message_id):
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'error': 'Método não permitido.'},
            status=405
        )

    try:
        from chat.models import ChatMessage
        msg = get_object_or_404(
            ChatMessage, id=message_id,
            session__user=request.user
        )
        if msg.role != 'user':
            return JsonResponse(
                {
                    'success': False,
                    'error': (
                        'Apenas mensagens do usuário '
                        'podem ser reenviadas.'
                    )
                },
                status=400
            )

        session = msg.session
        session.messages.filter(
            created_at__gt=msg.created_at
        ).delete()

        history = list(
            session.messages.all().order_by(
                '-created_at'
            )[:15]
        )
        history.reverse()
        messages_data = [
            {'role': m.role, 'content': m.content}
            for m in history
        ]

        try:
            from core.tasks import invoke_chat_agent_task
            task = invoke_chat_agent_task.delay(
                session.id, request.user.id, messages_data
            )
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'user_message_id': msg.id,
                'status': 'processing'
            })
        except Exception:
            pass

        sync_task_id = _dispatch_sync_agent(
            session.id, request.user.id, messages_data
        )
        return JsonResponse({
            'success': True,
            'task_id': sync_task_id,
            'user_message_id': msg.id,
            'status': 'processing'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }, status=500)


# ============================================================
# HTMX Fragment Views - Carregamento Parcial Dinâmico
# ============================================================

@login_required(login_url='login_page')
def chat_messages_fragment(request, session_id):
    """Retorna apenas as mensagens do chat."""
    session = get_object_or_404(
        ChatSession, id=session_id, user=request.user
    )
    messages = session.messages.all().order_by('created_at')
    return render(request, 'fragments/chat_messages.html', {
        'messages': messages,
        'session': session
    })


@login_required(login_url='login_page')
def chat_sessions_fragment(request):
    """Retorna a lista de sessões de chat."""
    sessions = ChatSession.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return render(request, 'fragments/chat_sessions.html', {
        'sessions': sessions
    })


@login_required(login_url='login_page')
def document_status_fragment(request, document_id):
    """Retorna o status de processamento de um documento."""
    doc = get_object_or_404(
        KnowledgeDocument, id=document_id, user=request.user
    )
    return render(request, 'fragments/document_status.html', {
        'doc': doc
    })


@login_required(login_url='login_page')
def dashboard_stats_fragment(request):
    """Retorna as estatísticas do dashboard."""
    from django.db.models import Count, Sum, F
    
    user = request.user
    docs_stats = KnowledgeDocument.objects.filter(user=user).aggregate(
        total=Count('id'),
        processed=Count('id', filter=models.Q(processing_status='completed'))
    )
    
    return render(request, 'fragments/dashboard_stats.html', {
        'arquivos_enviados': docs_stats['total'],
        'documentos_processados': docs_stats['processed'],
        'chats_realizados': ChatSession.objects.filter(user=user).count(),
        'flashcards_criados': Flashcard.objects.filter(user=user).count(),
        'quizzes_realizados': Quiz.objects.filter(user=user).count(),
        'horas_estudadas': StudyPlan.objects.filter(user=user).aggregate(
            total=Sum(F('available_hours_per_week') * F('duration_weeks'))
        )['total'] or 0,
        'temas_estudados': list(
            StudyPlan.objects.filter(user=user).values_list('technology', flat=True).distinct()
        )
    })
