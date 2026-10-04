from django.conf import settings
from django.db import models

CATEGORY_NAME_MAX_LENGTH = 100
TAG_NAME_MAX_LENGTH = 50
TITLE_MAX_LENGTH = 200
STATUS_MAX_LENGTH = 10

DRAFT_STATUS = "draft"
PUBLISHED_STATUS = "published"

POSTS_RELATED_NAME = "posts"
COMMENTS_RELATED_NAME = "comments"
CATEGORY_POSTS_RELATED_NAME = "posts"
TAG_POSTS_RELATED_NAME = "posts"

COMMENT_AUTHOR_LABEL = "Comment by"


class Category(models.Model):
    name = models.CharField(
        max_length=CATEGORY_NAME_MAX_LENGTH,
        unique=True,
    )
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
    )
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = DRAFT_STATUS, "Draft"
        PUBLISHED = PUBLISHED_STATUS, "Published"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=POSTS_RELATED_NAME,
    )
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name=CATEGORY_POSTS_RELATED_NAME,
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name=TAG_POSTS_RELATED_NAME,
    )
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name=COMMENTS_RELATED_NAME,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=COMMENTS_RELATED_NAME,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{COMMENT_AUTHOR_LABEL} {self.author.email}"