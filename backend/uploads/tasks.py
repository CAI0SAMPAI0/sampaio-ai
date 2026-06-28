from celery import shared_task
from .models import KnowledgeDocument
from knowledge_base.services import process_document_into_chunks

@shared_task
def process_document_task(document_id):
    try:
        doc = KnowledgeDocument.objects.get(id=document_id)
        doc.processing_status = 'processing'
        doc.save()
        
        success = process_document_into_chunks(doc)
        return success
    except KnowledgeDocument.DoesNotExist:
        return False
