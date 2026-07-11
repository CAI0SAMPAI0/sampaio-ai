from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

# Models import
from django.contrib.auth import get_user_model
from chat.models import ChatSession, ChatMessage
from uploads.models import KnowledgeDocument
from flashcards.models import Flashcard
from quizzes.models import Quiz
from studies.models import StudyPlan
from knowledge_base.services import search_similar_chunks
from ai_agents.agent import langgraph_agent

# Langchain
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

User = get_user_model()

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'sampaio-ai-api'})


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
            return redirect('dashboard_page')
        else:
            error = "E-mail ou senha incorretos."
            
    return render(request, 'login.html', {'error': error})


def logout_page(request):
    auth_logout(request)
    return redirect('login_page')


@login_required(login_url='login_page')
def dashboard_page(request):
    chats_count = ChatSession.objects.filter(user=request.user).count()
    docs_count = KnowledgeDocument.objects.filter(user=request.user).count()
    processed_count = KnowledgeDocument.objects.filter(user=request.user, processing_status='completed').count()
    cards_count = Flashcard.objects.filter(user=request.user).count()
    quizzes_count = Quiz.objects.filter(user=request.user).count()
    
    # Horas sugeridas totais dos planos de estudo
    study_plans = StudyPlan.objects.filter(user=request.user)
    hours_total = sum(p.available_hours_per_week * p.duration_weeks for p in study_plans)
    
    # Tecnologias estudadas
    techs = list(study_plans.values_list('technology', flat=True).distinct())
    
    dash_data = {
        'arquivos_enviados': docs_count,
        'documentos_processados': processed_count,
        'chats_realizados': chats_count,
        'flashcards_criados': cards_count,
        'quizzes_realizados': quizzes_count,
        'horas_estudadas': hours_total,
        'temas_estudados': techs
    }
    
    return render(request, 'dashboard.html', {'data': dash_data})


@login_required(login_url='login_page')
def chat_page(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    
    active_session_id = request.GET.get('session')
    active_session = None
    messages = []
    
    if active_session_id:
        active_session = get_object_or_404(ChatSession, id=active_session_id, user=request.user)
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
        num_sessions = ChatSession.objects.filter(user=request.user).count() + 1
        session = ChatSession.objects.create(
            user=request.user,
            title=f"Conversa #{num_sessions}"
        )
        return redirect(f"/chat/?session={session.id}")
    return redirect('chat_page')


@login_required(login_url='login_page')
def delete_chat(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return redirect('chat_page')


@login_required(login_url='login_page')
def send_chat_message(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    if request.method == 'POST':
        content = request.POST.get('message')
        if not content:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)
            
        # 1. Salvar mensagem do usuário
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=content
        )
                # 2. Obter histórico de mensagens (últimas 15 em ordem cronológica) para o estado do LangGraph
        history = list(session.messages.all().order_by('-created_at')[:15])
        history.reverse()
        lc_messages = []
        for msg in history:
            if msg.role == 'user':
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                lc_messages.append(AIMessage(content=msg.content))
                
        # 3. Invocar Agente LangGraph
        initial_state = {
            "messages": lc_messages,
            "context": "",
            "web_context": "",
            "user": request.user
        }
        
        try:
            result = langgraph_agent.invoke(initial_state)
            assistant_content = result['messages'][-1].content
        except Exception as e:
            assistant_content = f"Desculpe, ocorreu um erro no processamento do agente: {str(e)}"
            
        # 4. Salvar mensagem do assistente
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=assistant_content
        )
        
        # Se for requisição AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'content': assistant_content})
            
        return redirect(f"/chat/?session={session.id}")
        
    return redirect('chat_page')


@login_required(login_url='login_page')
def library_page(request):
    documents = KnowledgeDocument.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'library.html', {'documents': documents})


@login_required(login_url='login_page')
def flashcards_page(request):
    flashcards = Flashcard.objects.filter(user=request.user).order_by('-created_at')
    documents = KnowledgeDocument.objects.filter(user=request.user, processing_status='completed')
    return render(request, 'flashcards.html', {
        'flashcards': flashcards,
        'documents': documents
    })


@login_required(login_url='login_page')
def quizzes_page(request):
    quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')
    documents = KnowledgeDocument.objects.filter(user=request.user, processing_status='completed')
    return render(request, 'quizzes.html', {
        'quizzes': quizzes,
        'documents': documents
    })


@login_required(login_url='login_page')
def study_plans_page(request):
    plans = StudyPlan.objects.filter(user=request.user).order_by('-created_at')
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
            remove_avatar = request.POST.get('remove_avatar') == 'true'
            level = request.POST.get('level', 'iniciante')
            whatsapp_number = request.POST.get('whatsapp_number', '')
            
            import re
            if whatsapp_number:
                # Remove all non-digits except @c.us if it's already there
                if not whatsapp_number.endswith('@c.us'):
                    cleaned = re.sub(r'\D', '', whatsapp_number)
                    if cleaned:
                        whatsapp_number = f"{cleaned}@c.us"
                    else:
                        whatsapp_number = None
                else:
                    cleaned_part = re.sub(r'\D', '', whatsapp_number.split('@')[0])
                    if cleaned_part:
                        whatsapp_number = f"{cleaned_part}@c.us"
                    else:
                        whatsapp_number = None
            else:
                whatsapp_number = None
            
            if not email:
                error_message = "O e-mail é obrigatório."
            elif User.objects.exclude(id=request.user.id).filter(email=email).exists():
                error_message = "Este e-mail já está em uso por outro usuário."
            else:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.level = level
                request.user.whatsapp_number = whatsapp_number
                if remove_avatar:
                    if request.user.avatar:
                        request.user.avatar.delete(save=False)
                    request.user.avatar = None
                elif avatar:
                    request.user.avatar = avatar
                request.user.save()
                success_message = "Perfil atualizado com sucesso!"
                
        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not request.user.check_password(current_password):
                error_message = "Senha atual incorreta."
            elif new_password != confirm_password:
                error_message = "A nova senha e a confirmação não conferem."
            elif len(new_password) < 6:
                error_message = "A nova senha deve ter pelo menos 6 caracteres."
            else:
                request.user.set_password(new_password)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                success_message = "Senha alterada com sucesso!"
                
    return render(request, 'profile.html', {
        'success_message': success_message,
        'error_message': error_message
    })


def serve_db_media(request, path):
    from django.http import HttpResponse, Http404
    from accounts.models import StoredFile
    import mimetypes
    
    try:
        clean_path = path.replace('\\', '/')
        stored = StoredFile.objects.get(name=clean_path)
        content_type, encoding = mimetypes.guess_type(clean_path)
        if not content_type:
            content_type = 'application/octet-stream'
        response = HttpResponse(stored.content, content_type=content_type)
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
    
    # Busca desafio de hoje para o nivel do usuario
    challenge = DailyChallenge.objects.filter(date=today, difficulty=user_level).first()
    
    # Se nao houver, gera mock/fallback automaticamente
    if not challenge:
        from studies.tasks import _generate_mock_daily_challenges
        _generate_mock_daily_challenges()
        challenge = DailyChallenge.objects.filter(date=today, difficulty=user_level).first()
        
    submission = None
    if challenge:
        submission = ChallengeSubmission.objects.filter(user=request.user, challenge=challenge).order_by('-created_at').first()
        
    return render(request, 'challenges.html', {
        'challenge': challenge,
        'submission': submission,
        'user_level': user_level
    })


@login_required(login_url='login_page')
def run_challenge_code(request):
    import sys
    import subprocess
    import tempfile
    import os
    from django.http import JsonResponse
    from studies.models import DailyChallenge
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
        
    challenge_id = request.POST.get('challenge_id')
    code = request.POST.get('code', '')
    
    try:
        challenge = DailyChallenge.objects.get(id=challenge_id)
    except DailyChallenge.DoesNotExist:
        return JsonResponse({'error': 'Desafio não encontrado.'}, status=404)
        
    # Combina o codigo do usuario com as assertivas de teste
    full_code = f"{code}\n\n# --- TEST CASES ---\n{challenge.test_code}"
    
    # Grava o codigo em um arquivo temporario e o executa com o Python do sistema
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as temp:
        temp.write(full_code)
        temp_path = temp.name
        
    try:
        # Usa sys.executable para usar o mesmo interpretador ou python
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
        return JsonResponse({
            'passed': False,
            'stdout': '',
            'stderr': 'Erro de Execução: Limite de tempo excedido (Timeout de 5 segundos). Verifique se há loops infinitos.',
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
    import sys
    import subprocess
    import tempfile
    import os
    import re
    import json
    from django.http import JsonResponse
    from studies.models import DailyChallenge, ChallengeSubmission
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)
        
    challenge_id = request.POST.get('challenge_id')
    code = request.POST.get('code', '')
    
    try:
        challenge = DailyChallenge.objects.get(id=challenge_id)
    except DailyChallenge.DoesNotExist:
        return JsonResponse({'error': 'Desafio não encontrado.'}, status=404)
        
    # 1. Executa localmente para verificar se passa nos testes basicos
    full_code = f"{code}\n\n# --- TEST CASES ---\n{challenge.test_code}"
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as temp:
        temp.write(full_code)
        temp_path = temp.name
        
    passed = False
    exec_output = ""
    
    try:
        python_exec = sys.executable or "python"
        result = subprocess.run(
            [python_exec, temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        passed = (result.returncode == 0)
        exec_output = f"Stdout:\n{result.stdout}\n\nStderr:\n{result.stderr}" if (result.stdout or result.stderr) else "Sem saída no terminal."
    except subprocess.TimeoutExpired:
        exec_output = "Erro: Tempo limite de execução excedido (Timeout)."
    except Exception as e:
        exec_output = f"Erro de infraestrutura ao rodar código: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    # 2. IA gera feedback detalhado usando o GPT OSS 20b da Groq
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    feedback_text = ""
    
    if groq_key and groq_key != 'gsk_placeholder_for_development' and groq_key != "":
        try:
            llm = ChatGroq(
                groq_api_key=groq_key,
                model="openai/gpt-oss-20b",
                temperature=0.4
            )
            
            prompt = (
                "Você é um analista especialista em revisão de código Python e PEP8.\n"
                f"Desafio proposto: {challenge.title}\n"
                f"Instruções: {challenge.description}\n\n"
                f"Código enviado pelo usuário:\n```python\n{code}\n```\n\n"
                f"Resultado da Execução do Teste:\nStatus Aprovado: {passed}\nLogs: {exec_output}\n\n"
                "Forneça uma avaliação detalhada em formato Markdown:\n"
                "1. **Correção**: Explique se o código está correto ou aponte onde errou.\n"
                "2. **PEP8 & Boas Práticas**: Dê dicas sobre nomenclatura, espaçamento, organização e estilo de acordo com a PEP8.\n"
                "3. **Como Simplificar**: Dê sugestões de simplificação ou otimização do código.\n"
                "4. **O que Estudar**: Recomende tópicos técnicos para melhorar no assunto desse desafio.\n"
                "Seja construtivo e escreva em Português."
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            feedback_text = response.content
        except Exception as e:
            feedback_text = f"Erro ao contatar a inteligência artificial para feedback: {e}\n\nStatus dos Testes Locais: {'Aprovado' if passed else 'Falhou'}.\nLogs: {exec_output}"
    else:
        # Feedback simulado
        status_str = "Aprovado!" if passed else "Falhou nos testes."
        feedback_text = (
            f"### Avaliação Simulada (Sem chave Groq ativa)\n\n"
            f"**Status da Execução**: {status_str}\n"
            f"**Logs**: \n{exec_output}\n\n"
            f"**Dicas PEP8**: Lembre-se de usar 4 espaços para indentação e manter nomes de funções e variáveis em snake_case.\n"
            f"**O que estudar**: Funções, condicionais e tratamento de exceções em Python."
        )
        
    # 3. Salva a submissão no banco de dados
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


from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, Http404
import requests
from notifications.services import send_user_notification, send_waha_message

@user_passes_test(lambda u: u.is_superuser, login_url='login_page')
def waha_dashboard(request):
    """
    Painel para o administrador monitorar o status do WAHA (WhatsApp API),
    visualizar o QR Code de pareamento e o print da tela do WhatsApp Web.
    """
    waha_url = getattr(settings, 'WAHA_URL', 'http://localhost:3000').rstrip('/')
    waha_key = getattr(settings, 'WAHA_API_KEY', '')
    headers = {}
    if waha_key:
        headers['Authorization'] = f"Bearer {waha_key}"
        
    session_status = "DESCONECTADO"
    session_details = {}
    error_msg = None
    
    try:
        # Tenta obter status da sessão 'default'
        resp = requests.get(f"{waha_url}/api/sessions/default", headers=headers, timeout=5)
        if resp.status_code == 200:
            session_details = resp.json()
            session_status = session_details.get("status", "UNKNOWN")
        elif resp.status_code == 404:
            # Tenta criar a sessão se não existir
            requests.post(f"{waha_url}/api/sessions", json={"name": "default"}, headers=headers, timeout=5)
            session_status = "STOPPED"
    except Exception as e:
        error_msg = f"Sem conexão com o WPP (WAHA): {str(e)}"
        session_status = "ERRO_CONEXAO"

    # Se a sessão estiver parada, tenta iniciar
    if session_status == "STOPPED":
        try:
            requests.post(f"{waha_url}/api/sessions/default/start", headers=headers, timeout=5)
            session_status = "INICIANDO"
        except Exception:
            pass

    return render(request, 'waha_dashboard.html', {
        'status': session_status,
        'details': session_details,
        'error_msg': error_msg,
        'waha_url': waha_url,
    })


@user_passes_test(lambda u: u.is_superuser, login_url='login_page')
def waha_qr_proxy(request):
    """
    Proxy que obtém a imagem do QR Code do WAHA e a serve localmente para o admin,
    evitando problemas de rede interna ou CORS.
    """
    waha_url = getattr(settings, 'WAHA_URL', 'http://localhost:3000').rstrip('/')
    waha_key = getattr(settings, 'WAHA_API_KEY', '')
    headers = {}
    if waha_key:
        headers['Authorization'] = f"Bearer {waha_key}"
        
    try:
        resp = requests.get(f"{waha_url}/api/default/device/qr/image", headers=headers, timeout=5)
        if resp.status_code == 200:
            return HttpResponse(resp.content, content_type="image/png")
    except Exception:
        pass
    raise Http404("QR Code não disponível.")


@user_passes_test(lambda u: u.is_superuser, login_url='login_page')
def waha_screenshot_proxy(request):
    """
    Proxy que obtém um print da tela do WhatsApp Web (WAHA) para conferência e depuração.
    """
    waha_url = getattr(settings, 'WAHA_URL', 'http://localhost:3000').rstrip('/')
    waha_key = getattr(settings, 'WAHA_API_KEY', '')
    headers = {}
    if waha_key:
        headers['Authorization'] = f"Bearer {waha_key}"
        
    try:
        # WAHA Screenshot endpoint
        resp = requests.get(f"{waha_url}/api/screenshot?session=default", headers=headers, timeout=5)
        if resp.status_code == 200:
            return HttpResponse(resp.content, content_type="image/png")
    except Exception:
        pass
    raise Http404("Screenshot não disponível.")


@user_passes_test(lambda u: u.is_superuser, login_url='login_page')
def test_notification_caio(request):
    """
    Dispara uma notificação de teste (Email + WhatsApp) para Caio Sampaio.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Procura usuário que se chame Caio, caio, ou o usuário logado se não encontrar
    target_user = User.objects.filter(email__icontains="caio").first() or \
                  User.objects.filter(first_name__icontains="caio").first() or \
                  request.user
                  
    title = "Integração Bem-Sucedida!"
    message = (
        f"Olá {target_user.first_name or 'Caio Sampaio'}!\n\n"
        "Esta é uma notificação de teste enviada pelo sistema Sampaio AI para confirmar que as "
        "integrações de e-mail e WhatsApp (WAHA) estão operando com sucesso.\n\n"
        "Bons estudos!"
    )
    
    send_user_notification(target_user, title, message)
    
    return JsonResponse({
        'success': True,
        'recipient_name': target_user.first_name or target_user.email,
        'recipient_email': target_user.email,
        'recipient_whatsapp': target_user.whatsapp_number or "Não cadastrado"
    })