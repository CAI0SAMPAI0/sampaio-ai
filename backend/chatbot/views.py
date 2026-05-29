import os
import PyPDF2
import io

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chatbot.models import Chat, Conversation


os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY

embeddings = HuggingFaceEmbeddings(model_name='paraphrase-multilingual-MiniLM-L12-v2')
persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db')
vector_store = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings,
    collection_name='pdf_collection'
)
retriever = vector_store.as_retriever(search_kwargs={"k": 5})


def extract_file_content(file) -> str:
    """Extrai texto de qualquer tipo de arquivo."""
    filename = file.name.lower()
    content = file.read()

    if filename.endswith('.pdf'):
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        except Exception:
            return ''

    # Para todos os outros (py, js, ts, java, csv, txt, etc.)
    try:
        return content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return content.decode('latin-1')
        except Exception:
            return ''


def save_to_rag(content: str, filename: str):
    """Salva conteúdo no ChromaDB."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents([
        Document(page_content=content, metadata={'source': filename})
    ])
    vector_store.add_documents(docs)


def should_save_to_rag(message: str) -> bool:
    keywords = ['salvar no rag', 'adicionar ao rag', 'salve no rag', 'adicione ao rag', 'salvar para sempre', 'adicionar para sempre']
    return any(kw in message.lower() for kw in keywords)


def generate_title(message: str) -> str:
    """Gera título curto para a conversa baseado na primeira mensagem."""
    model = ChatGroq(model='llama-3.3-70b-versatile')
    response = model.invoke([
        ('system', 'Gere um título curto (máximo 5 palavras) para uma conversa que começa com a mensagem do usuário. Responda APENAS o título, sem aspas, sem pontuação extra.'),
        ('human', message),
    ])
    return response.content.strip()[:100]


def ask_ai(message: str, file_context: str, chat_history: list) -> str:
    model = ChatGroq(model='llama-3.3-70b-versatile')

    docs = retriever.invoke(message)
    rag_context = ""
    for doc in docs:
        fonte = os.path.basename(doc.metadata.get('source', 'Desconhecido'))
        rag_context += f"\n\n[Livro: {fonte}]\n{doc.page_content}"

    system_prompt = (
        'Você é um assistente de IA sênior responsável por tirar dúvidas sobre programação, '
        'especialmente Python, Django, DRF, FastAPI, JavaScript, TypeScript, HTML, CSS, Tailwind CSS. '
        'Responda de forma clara e objetiva, com exemplos de código quando necessário. '
        'Responda em formato markdown. Responda em português.'
        f'\n\nCONTEÚDO DOS LIVROS (RAG):\n{rag_context}'
    )

    if file_context:
        system_prompt += f'\n\nARQUIVO ENVIADO PELO USUÁRIO:\n{file_context}'

    messages = [('system', system_prompt)] + chat_history + [('human', message)]
    response = model.invoke(messages)
    return response.content


# ─── Conversations ────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversations(request):
    if request.method == 'GET':
        convs = Conversation.objects.filter(user=request.user).order_by('-created_at')
        data = [{'id': c.id, 'title': c.title, 'created_at': c.created_at} for c in convs]
        return Response(data)

    if request.method == 'POST':
        conv = Conversation.objects.create(user=request.user)
        return Response({'id': conv.id, 'title': conv.title, 'created_at': conv.created_at})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def conversation_detail(request, pk):
    try:
        conv = Conversation.objects.get(pk=pk, user=request.user)
        conv.delete()
        return Response({'message': 'Conversa deletada.'})
    except Conversation.DoesNotExist:
        return Response({'error': 'Não encontrada.'}, status=status.HTTP_404_NOT_FOUND)


# ─── Chat ─────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def chatbot(request, conversation_id):
    try:
        conv = Conversation.objects.get(pk=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversa não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        chats = Chat.objects.filter(conversation=conv).order_by('created_at')
        data = [{'id': c.id, 'message': c.message, 'response': c.response, 'created_at': c.created_at} for c in chats]
        return Response(data)

    if request.method == 'POST':
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Mensagem vazia.'}, status=status.HTTP_400_BAD_REQUEST)

        # Arquivo opcional
        file_context = ''
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            file_context = extract_file_content(uploaded_file)
            if should_save_to_rag(message):
                save_to_rag(file_context, uploaded_file.name)
                file_context = ''  # já está no RAG, não precisa no contexto

        # Histórico da conversa atual
        previous_chats = Chat.objects.filter(conversation=conv).order_by('created_at')
        chat_history = []
        for c in previous_chats:
            chat_history.append(('human', c.message))
            chat_history.append(('ai', c.response))

        response = ask_ai(message, file_context, chat_history)

        # Gera título na primeira mensagem
        is_first = not previous_chats.exists()
        if is_first:
            conv.title = generate_title(message)
            conv.save()

        Chat.objects.create(
            user=request.user,
            conversation=conv,
            message=message,
            response=response
        )

        return Response({
            'message': message,
            'response': response,
            'conversation_title': conv.title if is_first else None,
        })