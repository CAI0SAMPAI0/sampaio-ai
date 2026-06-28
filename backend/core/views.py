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
            
            if not email:
                error_message = "O e-mail é obrigatório."
            elif User.objects.exclude(id=request.user.id).filter(email=email).exists():
                error_message = "Este e-mail já está em uso por outro usuário."
            else:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
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