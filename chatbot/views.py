import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from langchain_groq import ChatGroq
from markdown import markdown
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from chatbot.models import Chat


os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY
os.environ['GOOGLE_API_KEY'] = settings.GOOGLE_API_KEY

# Carregando o RAG ao iniciar

embeddings = HuggingFaceEmbeddings(model_name='paraphrase-multilingual-MiniLM-L12-v2')
persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db')
vector_store = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings,
    collection_name='pdf_collection'
)
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

def get_chat_history(chats):
    chat_history = []
    for chat in chats:
        chat_history.append(('human', chat.message))
        chat_history.append(('ai', chat.response))
    return chat_history


def ask_ai(message):
    model = ChatGroq(model='llama-3.3-70b-versatile')
    docs = retriever.invoke(message)
    context = ""
    for doc in docs:
        fonte = os.path.basename(doc.metadata.get('source', 'Desconhecido'))
        context += f"\n\n[Livro de Origem: {fonte}]\n{doc.page_content}"
    messages = [
        (
            'system',
            'Você é um assistente de IA sênior reponsável por tirar dúvidas spbre programação, especialmente sobre Python, Django, Django Rest Framework, FastAPI, etc. Outras linguagens a tirar dúvidas são: JavaScript, TypeScript, HTML, CSS, Tailwind CSS. Responda de forma clara e objetiva, fornecendo exemplos de código quando necessário. Ajude-o a resolver seus problemas de programação e a entender melhor os conceitos relacionados. Se a pergunta for sobre um erro específico, tente fornecer uma solução ou uma explicação do que pode estar causando o erro. E sempre que possível, forneça links para documentação oficial ou recursos adicionais que possam ser úteis para o usuário. Se precisar de mais informações para responder à pergunta, peça por elas de forma educada e clara. Sempre ajude o usuário a entender a lógica e a pensar como um programador, em vez de apenas fornecer a resposta. Você também pode fornecer dicas e sugestões para melhorar o código do usuário, se ele pedir. Você entende outros frameworks e bibliotecas além dos mencionados como NextJS, React, mas seu foco principal é ajudar com dúvidas relacionadas a eles.'
            'Responda em formato markdown, para que a formatação seja mantida na interface do usuário.'
            'Responda no idioma português.'
            f'\n\nCONTEÚDO DOS LIVROS RECUPERADOS:\n{context}',
        ),
        (
            'human',
            message,
        ),
    ]
    response = model.invoke(messages)
    return markdown(response.content, output_format='html')


@login_required
def chatbot(request):
    chats = Chat.objects.all().order_by('-created_at')

    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_ai(message)

        chat = Chat(
            message=message,
            response=response
        )
        chat.save()

        return JsonResponse({
            'message': message,
            'response': response
        })

    return render(request, 'chatbot.html', {'chats': chats})