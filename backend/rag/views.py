import os

from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


def testar_rag():
    os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY
    os.environ['GOOGLE_API_KEY'] = settings.GOOGLE_API_KEY
    os.environ['HUGGING_FACE_KEY'] = settings.HUGGING_FACE_KEY

    model = ChatGroq(model='llama-3.3-70b-versatile')
    embeddings = HuggingFaceEmbeddings(
        model_name='paraphrase-multilingual-MiniLM-L12-v2',
    )
    persist_directory = os.path.join(settings.BASE_DIR, 'chroma_db')

    if not os.path.exists(persist_directory):
        files_path = os.path.join(settings.BASE_DIR, 'core/files')
        all_documents = []

        for file in os.listdir(files_path):
            if file.endswith('.pdf'):
                print(f'Carregando arquivo: {file}')
                loader = PyPDFLoader(os.path.join(files_path, file))
                all_documents.extend(loader.load())
        
        if not all_documents:
            print('Nenhum arquivo PDF encontrado na pasta "files".')
            return

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(all_documents)

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name='pdf_collection'
        )

    else:
        print('Carregando vetor store existente...')
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=persist_directory,
            collection_name='pdf_collection'
        )
    # O retriever sem filtros vai buscar os 5 trechos mais parecidos na biblioteca inteira
    retriever = vector_store.as_retriever(search_kwargs={"k": 10})

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente atencioso para tarefas de resposta a perguntas. "
                   "Use os seguintes trechos de contexto recuperados para responder à pergunta. "
                   "Se você não souber a resposta, diga apenas que não sabe. "
                   "Use no máximo três frases e mantenha a resposta concisa."),
        ("human", "Pergunta: {question}\n\nContexto: {context}\n\nResposta:")
    ])
    
    def format_docs(docs):
        formatted = []
        for doc in docs:
            content = os.path.basename(doc.metadata.get('source', 'Desconhecido'))
            formatted.append(content)
        return "\n".join(formatted)

    rag_chain = (
        {
            'context': retriever | format_docs,
            'question': RunnablePassthrough(),
        }
        | prompt
        | model
        | StrOutputParser()
    )