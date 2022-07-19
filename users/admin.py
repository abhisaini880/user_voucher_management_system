from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminCreationForm, UserAdminChangeForm

User = get_user_model()

# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = [
        "id",
        "name",
        "mobile_number",
        "staff",
        "admin",
        "staff_editor",
        "read_only",
    ]
    list_filter = ["admin", "staff", "staff_editor", "read_only"]
    fieldsets = (
        (None, {"fields": ("mobile_number", "password")}),
        ("Personal info", {"fields": ("name",)}),
        (
            "Permissions",
            {"fields": ("admin", "staff", "staff_editor", "read_only")},
        ),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("mobile_number", "name", "password", "password_2"),
            },
        ),
    )
    search_fields = ["mobile_number", "name"]
    ordering = ["id"]
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
