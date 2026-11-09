import json

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.sections import TableSection
from django.db.models import Count
from unfold.contrib.filters.admin import RangeDateTimeFilter
from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag
from django.conf import settings
from django.utils.html import format_html
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action

def environment_callback(request):
    if settings.BLOG_ENV_ID.lower() == "production":
        return ["Production", "danger"]

    return ["Local", "warning"]

def draft_posts_badge(request):
    return Post.objects.filter(status=Post.Status.DRAFT).count()

class CategoryPostsSection(TableSection):
    verbose_name = "Posts in this category"
    related_name = "posts"
    fields = ["title", "status", "created_at"]

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = [CategoryPostsSection]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(post_count=Count("posts"))
            .prefetch_related("posts")
        )

    @admin.display(description="Posts", ordering="post_count")
    def post_count(self, obj):
        return obj.post_count


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "slug", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            post_count=Count("posts")
        )

    @admin.display(description="Posts", ordering="post_count")
    def post_count(self, obj):
        return obj.post_count

@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post", "author", "short_body", "created_at")
    list_select_related = ("post", "author")
    autocomplete_fields = ("post", "author")
    search_fields = (
        "body",
        "author__email",
        "post__title",
    )

    list_filter = (
            "post",
            "author",
            ("created_at", RangeDateTimeFilter),
        )
    list_filter_submit = True

    @admin.display(description="Comment")
    def short_body(self, obj):
        return obj.body[:50]

@admin.action(description="Publish selected posts")
def publish_posts(modeladmin, request, queryset):
    queryset.update(status=Post.Status.PUBLISHED)


@admin.action(description="Move selected posts to drafts")
def draft_posts(modeladmin, request, queryset):
    queryset.update(status=Post.Status.DRAFT)

class PostCommentsSection(TableSection):
    verbose_name = "Comments"
    related_name = "comments"
    fields = ("author", "body", "created_at")

class CommentInline(TabularInline):
    model = Comment
    extra = 0
    per_page = 100
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    show_change_link = True

@admin.register(Post)
class PostAdmin(ModelAdmin):
    actions = (publish_posts, draft_posts)
    actions_list = ["publish_all_drafts"]
    actions_row = ["toggle_status"]

    list_display = (
            "title",
            "author",
            "category",
            "status_badge",
            "comment_count",
            "created_at",
            "tags_display",
        )
    list_filter = (
        "status",
        "category",
        "tags",
        "author",
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    search_fields = ("title", "body", "author__email")
    list_select_related = ("author", "category")
    autocomplete_fields = ("author", "category")
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    list_sections = [PostCommentsSection]
    inlines = (CommentInline,)

    warn_unsaved_form = True

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        },
    }

    fieldsets = (
        (
            "Content",
            {
                "classes": ["tab"],
                "fields": ("title", "slug", "body"),
            },
        ),
        (
            "Classification",
            {
                "classes": ["tab"],
                "fields": ("category", "tags", "status"),
            },
        ),
        (
            "Meta",
            {
                "classes": ["tab"],
                "fields": ("author", "created_at", "updated_at"),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Comments", ordering="comment_count")
    def comment_count(self, obj):
        return obj.comment_count

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        if obj.status == Post.Status.PUBLISHED:
            return format_html(
                '<span style="color: #16a34a; font-weight: 600;">Published</span>'
            )
        return format_html(
            '<span style="color: #d97706; font-weight: 600;">Draft</span>'
        )

    @admin.display(description="Tags")
    def tags_display(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())

    @action(
        description="Publish all drafts",
        permissions=["publish_all_drafts"],
        url_path="publish-all-drafts",
    )
    def publish_all_drafts(self, request):
        count = Post.objects.filter(
            status=Post.Status.DRAFT
        ).update(status=Post.Status.PUBLISHED)

        self.message_user(request, f"{count} drafts published.")
        return redirect(reverse("admin:blog_post_changelist"))


    def has_publish_all_drafts_permission(self, request):
        return request.user.has_perm("blog.change_post")


    @action(
        description="Toggle publish status",
        permissions=["toggle_status"],
        url_path="toggle-status",
    )
    def toggle_status(self, request, object_id):
        post = self.get_object(request, object_id)

        if post:
            if post.status == Post.Status.PUBLISHED:
                post.status = Post.Status.DRAFT
            else:
                post.status = Post.Status.PUBLISHED

            post.save()
            self.message_user(request, f"Post status changed: {post.title}")

        return redirect(reverse("admin:blog_post_changelist"))


    def has_toggle_status_permission(self, request, object_id=None):
        return request.user.has_perm("blog.change_post")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(comment_count=Count("comments"))
            .prefetch_related("tags", "comments__author")
        )

def dashboard_callback(request, context):
    total_posts = Post.objects.count()
    published_posts = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).count()
    draft_posts = Post.objects.filter(
        status=Post.Status.DRAFT
    ).count()

    categories = Category.objects.annotate(
        post_count=Count("posts")
    ).order_by("name")

    authors = (
        User.objects.annotate(post_count=Count("posts"))
        .filter(post_count__gt=0)
        .order_by("-post_count")[:5]
    )

    context.update({
        "total_users": User.objects.count(),
        "published_posts": published_posts,
        "draft_posts": draft_posts,
        "total_comments": Comment.objects.count(),
        "category_chart": json.dumps({
            "labels": [category.name for category in categories],
            "datasets": [{
                "label": "Posts",
                "data": [category.post_count for category in categories],
            }],
        }),
        "top_authors": authors,
        "published_percentage": (
            published_posts / total_posts * 100 if total_posts else 0
        ),
        "draft_percentage": (
            draft_posts / total_posts * 100 if total_posts else 0
        ),
    })

    return context