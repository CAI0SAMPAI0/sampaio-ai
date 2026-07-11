from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    health_check,
    login_page,
    logout_page,
    dashboard_page,
    chat_page,
    new_chat,
    delete_chat,
    send_chat_message,
    library_page,
    flashcards_page,
    quizzes_page,
    study_plans_page,
    profile_page,
    serve_db_media,
    challenges_page,
    run_challenge_code,
    submit_challenge,
    waha_dashboard,
    waha_qr_proxy,
    waha_screenshot_proxy,
    test_notification_caio
)


urlpatterns = [
    path('', dashboard_page, name='dashboard_page'),
    path('health', health_check, name='health_check'),
    path('login/', login_page, name='login_page'),
    path('logout/', logout_page, name='logout'),
    path('profile/', profile_page, name='profile_page'),
    path('chat/', chat_page, name='chat_page'),
    path('chat/new', new_chat, name='new_chat'),
    path('chat/<int:session_id>/delete', delete_chat, name='delete_chat'),
    path('chat/<int:session_id>/send', send_chat_message, name='send_chat_message'),
    path('library/', library_page, name='library_page'),
    path('flashcards/', flashcards_page, name='flashcards_page'),
    path('quizzes/', quizzes_page, name='quizzes_page'),
    path('challenges/', challenges_page, name='challenges_page'),
    path('challenges/run/', run_challenge_code, name='run_challenge_code'),
    path('challenges/submit/', submit_challenge, name='submit_challenge'),
    path('studies/', study_plans_page, name='study_plans_page'),
    path('waha-dashboard/', waha_dashboard, name='waha_dashboard'),
    path('waha-dashboard/qr/', waha_qr_proxy, name='waha_qr_proxy'),
    path('waha-dashboard/screenshot/', waha_screenshot_proxy, name='waha_screenshot_proxy'),
    path('api/notifications/test-caio/', test_notification_caio, name='test_notification_caio'),
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/uploads/', include('uploads.urls')),
    path('api/knowledge-base/', include('knowledge_base.urls')),
    path('api/flashcards/', include('flashcards.urls')),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/studies/', include('studies.urls')),
    path('api/notifications/', include('notifications.urls')),
]

from django.urls import re_path
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_db_media, name='serve_db_media'),
]

