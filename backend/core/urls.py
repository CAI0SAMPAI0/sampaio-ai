from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import health_check


urlpatterns = [
    path('', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/conversations/', include('chatbot.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
