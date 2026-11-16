import random
import time
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag

DEFAULT_USERS_COUNT = 20
DEFAULT_POSTS_COUNT = 100
DEFAULT_COMMENTS_COUNT = 500

SEED_PASSWORD = "seed-password-123"

PUBLISHED_POST_PERCENTAGE = 70
DRAFT_POST_PERCENTAGE = 30
NO_CATEGORY_PERCENTAGE = 10
UPDATED_POSTS_PERCENTAGE = 30

MIN_TAGS_PER_POST = 0
MAX_TAGS_PER_POST = 5

MIN_BODY_PARAGRAPHS = 3
MAX_BODY_PARAGRAPHS = 5

MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3

INACTIVE_USER_PERCENTAGE = 10
STAFF_USER_PERCENTAGE = 5
SEED_EMAIL_DOMAIN = "example.com"

DAYS_IN_YEAR = 365
MAX_UPDATE_DAYS = 30

CATEGORIES = [
    "Programming",
    "Technology",
    "Gaming",
    "Education",
    "Science",
    "Lifestyle",
    "Entertainment",
    "News",
]

TAGS = [
    "Python", "Django", "JavaScript", "React", "Web Development",
    "Backend", "Frontend", "Database", "API", "Security",
    "Artificial Intelligence", "Machine Learning", "Gaming",
    "Unity", "Mobile Development", "Tutorial", "Beginner",
    "Advanced", "Open Source", "Software Engineering",
]

def generate_unique_slug(model, value, used_slugs=None):
    base_slug = slugify(value)
    slug = base_slug
    counter = 2

    while (
        model.objects.filter(slug=slug).exists()
        or (used_slugs is not None and slug in used_slugs)
    ):
        slug = f"{base_slug}-{counter}"
        counter += 1

    if used_slugs is not None:
        used_slugs.add(slug)

    return slug

def generate_users(count, fake):
    existing_emails = set(User.objects.values_list("email", flat=True))
    generated_emails = set()
    password_hash = make_password(SEED_PASSWORD)
    users = []

    for _ in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()

        base_email = (
            f"{slugify(first_name)}.{slugify(last_name)}"
            f"@{SEED_EMAIL_DOMAIN}"
        )
        email = base_email
        counter = 2

        while email in existing_emails or email in generated_emails:
            email = (
                f"{slugify(first_name)}.{slugify(last_name)}"
                f"{counter}@{SEED_EMAIL_DOMAIN}"
            )
            counter += 1

        generated_emails.add(email)

        users.append(
            User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password_hash,
                is_active=(
                    random.randint(1, 100) > INACTIVE_USER_PERCENTAGE
                ),
                is_staff=(
                    random.randint(1, 100) <= STAFF_USER_PERCENTAGE
                ),
            )
        )

    return User.objects.bulk_create(users)

def generate_categories_and_tags():
    existing_categories = set(
        Category.objects.values_list("name", flat=True)
    )
    existing_tags = set(
        Tag.objects.values_list("name", flat=True)
    )

    categories = [
        Category(
            name=name,
            slug=generate_unique_slug(Category, name),
        )
        for name in CATEGORIES
        if name not in existing_categories
    ]

    tags = [
        Tag(
            name=name,
            slug=generate_unique_slug(Tag, name),
        )
        for name in TAGS
        if name not in existing_tags
    ]

    Category.objects.bulk_create(categories)
    Tag.objects.bulk_create(tags)

    return (
        list(Category.objects.all()),
        list(Tag.objects.all()),
    )

def generate_posts(count, users, categories, tags, fake):
    posts = []
    post_tags = []
    used_slugs = set()

    for _ in range(count):
        title = fake.sentence(nb_words=6).rstrip(".")

        body_paragraphs = fake.paragraphs(
            nb=random.randint(
                MIN_BODY_PARAGRAPHS,
                MAX_BODY_PARAGRAPHS,
            )
        )

        status = random.choices(
            [Post.Status.PUBLISHED, Post.Status.DRAFT],
            weights=[
                PUBLISHED_POST_PERCENTAGE,
                DRAFT_POST_PERCENTAGE,
            ],
        )[0]

        category = (
            None
            if random.randint(1, 100) <= NO_CATEGORY_PERCENTAGE
            else random.choice(categories)
        )

        selected_tags = random.sample(
            tags,
            k=random.randint(
                MIN_TAGS_PER_POST,
                min(MAX_TAGS_PER_POST, len(tags)),
            ),
        )

        created_at = timezone.now() - timedelta(days = random.randint(0, DAYS_IN_YEAR))

        post = Post(
            author=random.choice(users),
            title=title,
            slug=generate_unique_slug(Post, title, used_slugs),
            body="\n\n".join(body_paragraphs),
            category=category,
            status=status,
            created_at=created_at,
            updated_at=created_at,
        )

        posts.append(post)
        post_tags.append(selected_tags)
    
    post_creation_dates = [post.created_at for post in posts]
    
    created_posts = Post.objects.bulk_create(posts)

    now = timezone.now()

    for post, created_at in zip(posts, post_creation_dates):
        post.created_at = created_at
        post.updated_at = created_at

        max_days = min(MAX_UPDATE_DAYS, (now - created_at).days)

        if max_days >= 1 and random.randint(1, 100) <= UPDATED_POSTS_PERCENTAGE:
            post.updated_at = created_at + timedelta(days=random.randint(1, max_days))

    Post.objects.bulk_update(posts, ["created_at", "updated_at"])

    for post, selected_tags in zip(created_posts, post_tags):
        post.tags.set(selected_tags)

    return created_posts

def generate_comments(count, users, posts, fake):
    published_posts = [
        post for post in posts
        if post.status == Post.Status.PUBLISHED
    ]

    if count > 0 and not published_posts:
        raise CommandError("Cannot create comments without published posts.")

    comments = []

    for _ in range(count):
        post = random.choice(published_posts)
        now = timezone.now()

        comments.append(
            Comment(
                post=post,
                author=random.choice(users),
                body=" ".join(
                    fake.sentences(
                        nb=random.randint(
                            MIN_COMMENT_SENTENCES,
                            MAX_COMMENT_SENTENCES,
                        )
                    )
                ),
                created_at = post.created_at + timedelta(seconds=random.randint(
                    0, int((now - post.created_at).total_seconds())
                )),
            )
        )

    comment_dates = [comment.created_at for comment in comments]

    Comment.objects.bulk_create(comments)

    for comment, created_at in zip(comments, comment_dates):
        comment.created_at = created_at

    Comment.objects.bulk_update(comments, ["created_at"])

    return comments

def clear_seed_data():
    Comment.objects.all().delete()
    Post.objects.all().delete()
    Tag.objects.all().delete()
    Category.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()

class Command(BaseCommand):
    help = "Generate sample blog data"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=DEFAULT_USERS_COUNT)
        parser.add_argument("--posts", type=int, default=DEFAULT_POSTS_COUNT)
        parser.add_argument("--comments", type=int, default=DEFAULT_COMMENTS_COUNT)
        parser.add_argument("--clear", action="store_true")
    
    @transaction.atomic
    def handle(self, *args, **options):
        start_time = time.perf_counter()

        users_count = options["users"]
        posts_count = options["posts"]
        comments_count = options["comments"]

        if min(users_count, posts_count, comments_count) < 0:
            raise CommandError("Counts cannot be negative.")

        if (posts_count > 0 or comments_count > 0) and users_count == 0:
            raise CommandError("Users are required to create posts or comments.")

        self.stdout.write("Arguments validated successfully.")

        if options["clear"]:
            clear_seed_data()
            self.stdout.write(
                self.style.SUCCESS("Existing seed data cleared.")
            )

        fake = Faker()
        users = generate_users(users_count, fake)
        categories, tags = generate_categories_and_tags()
        posts = generate_posts(
            posts_count,
            users,
            categories,
            tags,
            fake,
        )
        comments = generate_comments(
            comments_count,
            users,
            posts,
            fake,
        )

        elapsed_time = time.perf_counter() - start_time

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))
        self.stdout.write(f"Users created: {len(users)}")
        self.stdout.write(f"Posts created: {len(posts)}")
        self.stdout.write(f"Comments created: {len(comments)}")
        self.stdout.write(f"Execution time: {elapsed_time:.2f} seconds")
