from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.contrib.filters.admin import BooleanRadioFilter
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin

from apps.auths.forms import UserChangeAdminForm, UserCreationAdminForm
from apps.auths.models import User

@admin.action(description="Activate selected users")
def activate_users(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Deactivate selected users")
def deactivate_users(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.register(User)
class UserAdmin(ModelAdmin, DjangoUserAdmin):
    form = UserChangeAdminForm
    add_form = UserCreationAdminForm
    change_password_form = AdminPasswordChangeForm

    actions = (activate_users, deactivate_users)

    list_display = (
        "user_identity",
        "is_active",
        "is_staff",
        "post_count",
    )

    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    @display(
        description="Active",
        boolean=True,
        ordering="is_active",
    )
    def is_active(self, obj):
        return obj.is_active


    @display(
        description="Staff",
        boolean=True,
        ordering="is_staff",
    )
    def is_staff(self, obj):
        return obj.is_staff

    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )

    fieldsets = (
        (
            "Personal info",
            {
                "fields": ("email", "first_name", "last_name", "password"),
                "classes": ("tab",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("tab",),
            },
        ),
        (
            "Important dates",
            {
                "fields": ("last_login",),
                "classes": ("tab",),
            },
        ),
    )

    readonly_fields = ("last_login",)
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return (
                (
                    "Create user",
                    {
                        "fields": (
                            "email",
                            "first_name",
                            "last_name",
                            "password1",
                            "password2",
                        ),
                    },
                ),
            )

        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = self.add_form if obj is None else self.form
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            post_count=Count("posts")
        )

    @admin.display(description="User", ordering="email")
    def user_identity(self, obj):
        initials = (
            f"{obj.first_name[:1]}{obj.last_name[:1]}"
        ).upper()

        full_name = f"{obj.first_name} {obj.last_name}"

        return format_html(
            '<span style="display:inline-flex;align-items:center;'
            'gap:10px;"><span style="background:#64748b;color:white;'
            'border-radius:50%;width:32px;height:32px;display:inline-flex;'
            'align-items:center;justify-content:center;">{}</span>'
            '<span><strong>{}</strong><br>{}</span></span>',
            initials,
            full_name,
            obj.email,
        )

    @admin.display(description="Posts", ordering="post_count")
    def post_count(self, obj):
        return obj.post_count

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)