import re
import requests
from django.conf import settings
from django.core.mail import send_mail
from .models import Notification

def send_waha_message(chat_id, text):
    """
    Envia uma mensagem de texto utilizando a API do WAHA.
    """
    waha_url = getattr(settings, 'WAHA_URL', 'http://localhost:3000')
    waha_key = getattr(settings, 'WAHA_API_KEY', '')
    
    # Limpa a URL e garante que termine de forma consistente
    endpoint = f"{waha_url.rstrip('/')}/api/sendText"
    
    headers = {
        'Content-Type': 'application/json'
    }
    if waha_key:
        headers['Authorization'] = f"Bearer {waha_key}"
        headers['X-Api-Key'] = waha_key
        
    payload = {
        'session': 'default',
        'chatId': chat_id,
        'text': text
    }
    
    try:
        print(f"Enviando mensagem WAHA para {chat_id}...")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        print(f"Resposta WAHA para {chat_id}: status={response.status_code}, content={response.text}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Erro de conexão ao enviar mensagem WAHA para {chat_id}: {e}")
        return False

def send_user_notification(user, title, message):
    """
    Cria uma notificação interna no banco de dados e a envia
    simultaneamente por E-mail e por WhatsApp (WAHA), se disponível.
    """
    # 1. Cria notificação interna no Django
    Notification.objects.create(
        user=user,
        title=title,
        message=message
    )

    # 2. Envia por E-mail
    try:
        send_mail(
            subject=title,
            message=message,
            from_email=None,  # Usa settings.DEFAULT_FROM_EMAIL
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Erro ao enviar e-mail para {user.email}: {e}")

    # 3. Envia por WhatsApp via WAHA
    if user.whatsapp_number:
        # Formata o número (garantindo o formato c@us)
        phone = user.whatsapp_number
        if not phone.endswith('@c.us'):
            cleaned = re.sub(r'\D', '', phone)
            if cleaned:
                phone = f"{cleaned}@c.us"
            else:
                phone = None
                
        if phone:
            whatsapp_text = f"*Sampaio AI - {title}*\n\n{message}"
            send_waha_message(phone, whatsapp_text)
