from django.core.mail import send_mail
from .models import Notification


def send_user_notification(user, title, message):
    """
    Cria uma notificação interna no banco de dados e a envia por E-mail.
    """
    Notification.objects.create(user=user, title=title, message=message)

    try:
        send_mail(
            subject=title,
            message=message,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass
