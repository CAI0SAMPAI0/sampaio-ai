from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StoredFile


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "level", "is_staff", "is_active", "date_joined"]
    list_filter = ["level", "is_staff", "is_superuser", "is_active"]
    search_fields = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informações Pessoais", {"fields": ("avatar", "level", "plain_password")}),
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas Importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password", "level", "is_staff", "is_superuser"),
            },
        ),
    )


@admin.register(StoredFile)
class StoredFileAdmin(admin.ModelAdmin):
    list_display = ["name", "size", "updated_at"]
    search_fields = ["name"]

