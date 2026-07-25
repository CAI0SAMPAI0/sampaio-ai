from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    health_check,
    task_status,
    trigger_daily_challenges,
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
    run_terminal_command,
    run_editor_code,
    export_chat_md,
    share_chat,
    rename_chat,
    public_chat_share_view,
    analyze_user_level,
    edit_chat_message,
    resend_chat_message_view,
    chat_messages_fragment,
    chat_sessions_fragment,
    document_status_fragment,
    dashboard_stats_fragment,
)

urlpatterns = [
    path("", dashboard_page, name="dashboard_page"),
    path("health", health_check, name="health_check"),
    path("api/task/<str:task_id>/", task_status, name="task_status"),
    path(
        "api/cron/daily-challenges",
        trigger_daily_challenges,
        name="trigger_daily_challenges",
    ),
    path("login/", login_page, name="login_page"),
    path("logout/", logout_page, name="logout"),
    path("profile/", profile_page, name="profile_page"),
    path("profile/analyze-level", analyze_user_level, name="analyze_user_level"),
    path("chat/", chat_page, name="chat_page"),
    path("chat/new", new_chat, name="new_chat"),
    path("chat/<int:session_id>/delete", delete_chat, name="delete_chat"),
    path("chat/<int:session_id>/send", send_chat_message, name="send_chat_message"),
    path(
        "chat/message/<int:message_id>/edit",
        edit_chat_message,
        name="edit_chat_message",
    ),
    path(
        "chat/message/<int:message_id>/resend",
        resend_chat_message_view,
        name="resend_chat_message_view",
    ),
    path("chat/<int:session_id>/rename", rename_chat, name="rename_chat"),
    path("chat/<int:session_id>/export", export_chat_md, name="export_chat_md"),
    path("chat/<int:session_id>/share", share_chat, name="share_chat"),
    path(
        "chat/share/<int:session_id>/<str:token>",
        public_chat_share_view,
        name="public_chat_share",
    ),
    path("chat/terminal/run", run_terminal_command, name="run_terminal_command"),
    path("chat/editor/run", run_editor_code, name="run_editor_code"),
    path("library/", library_page, name="library_page"),
    path("flashcards/", flashcards_page, name="flashcards_page"),
    path("quizzes/", quizzes_page, name="quizzes_page"),
    path("challenges/", challenges_page, name="challenges_page"),
    path("challenges/run/", run_challenge_code, name="run_challenge_code"),
    path("challenges/submit/", submit_challenge, name="submit_challenge"),
    path("studies/", study_plans_page, name="study_plans_page"),
    # HTMX Fragment endpoints
    path(
        "api/fragments/chat/messages/<int:session_id>/",
        chat_messages_fragment,
        name="chat_messages_fragment",
    ),
    path(
        "api/fragments/chat/sessions/",
        chat_sessions_fragment,
        name="chat_sessions_fragment",
    ),
    path(
        "api/fragments/document/<int:document_id>/status/",
        document_status_fragment,
        name="document_status_fragment",
    ),
    path(
        "api/fragments/dashboard/stats/",
        dashboard_stats_fragment,
        name="dashboard_stats_fragment",
    ),
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/auth/", include("accounts.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/uploads/", include("uploads.urls")),
    path("api/knowledge-base/", include("knowledge_base.urls")),
    path("api/flashcards/", include("flashcards.urls")),
    path("api/quizzes/", include("quizzes.urls")),
    path("api/studies/", include("studies.urls")),
    path("api/notifications/", include("notifications.urls")),
]

from django.urls import re_path

urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve_db_media, name="serve_db_media"),
]
