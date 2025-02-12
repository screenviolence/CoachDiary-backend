from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from auth.users.admin.forms import UserCreationForm

from ..models import User


@admin.register(User)
class CustomUserAdmin(
    UserAdmin,
):
    add_form = UserCreationForm

    list_filter = (
        "is_staff",
        "is_superuser",
    )
    search_fields = (
        "email",
        "id",
    )
    list_display = (
        "id",
        "email",
        "is_staff",
        "is_superuser",
    )
    ordering = (
        "email",
    )
    fieldsets = (
        (None, {"fields": ("name", "email", "password")}),
        (
            "Пермиссии",
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("name", "email", "password1", "password2"),
            },
        ),
    )
