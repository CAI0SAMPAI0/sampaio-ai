import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from langchain_core.messages import HumanMessage
from .agent import langgraph_agent
from uploads.models import KnowledgeDocument
from knowledge_base.services import process_document_into_chunks

User = get_user_model()

class AgentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testagent@sampaio.ai',
            password='password123'
        )
        
        # Cria documento RAG de estudo
        self.doc = KnowledgeDocument.objects.create(
            user=self.user,
            name="react_notes.txt",
            file_type="txt",
            file_size=100,
            processing_status="pending"
        )
        self.doc.file.save("react_notes.txt", ContentFile(b"React utiliza virtual DOM para otimizar a renderizacao da interface."))
        self.doc.save()
        process_document_into_chunks(self.doc)

    def tearDown(self):
        if self.doc.file and os.path.exists(self.doc.file.path):
            try:
                os.remove(self.doc.file.path)
            except Exception:
                pass

    def test_langgraph_agent_rag_execution(self):
        messages = [HumanMessage(content="React utiliza virtual DOM para otimizar a renderizacao da interface.")]
        state = {
            "messages": messages,
            "context": "",
            "web_context": "",
            "user": self.user
        }
        
        result = langgraph_agent.invoke(state)
        self.assertGreater(len(result['messages']), 1)
        response_content = result['messages'][-1].content
        self.assertIn("React", result['context'])
        self.assertIn("virtual DOM", result['context'])
        self.assertIn("Simulação", response_content)

    def test_langgraph_agent_web_search_execution(self):
        messages = [HumanMessage(content="pesquise na internet sobre Python")]
        state = {
            "messages": messages,
            "context": "",
            "web_context": "",
            "user": self.user
        }
        
        result = langgraph_agent.invoke(state)
        self.assertIn("web_context", result)
