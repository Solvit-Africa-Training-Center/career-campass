from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Role, Student,Profile,Agent


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "is_staff", "is_active", "get_roles")
    list_filter = ("is_staff", "is_active", "roles")
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ("roles",)  # for ManyToMany fields

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("roles",)}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "roles", "is_active", "is_staff"),
            },
        ),
    )

    def get_roles(self, obj):
        return ", ".join([role.name for role in obj.roles.all()])
    get_roles.short_description = "Roles"


admin.site.register(User, UserAdmin,)
admin.site.register(Student)
admin.site.register(Profile)
admin.site.register(Agent)
