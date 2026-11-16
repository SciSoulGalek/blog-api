from datetime import date, timedelta
from typing import Any

from django.db.models import F, Q, Avg, Case, CharField, Count, Exists, Max, Min, OuterRef, Prefetch, QuerySet, Subquery, Value, When
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag


NEWEST_POSTS_LIMIT = 5
PAGE_SIZE = 10
UNCATEGORIZED_LABEL = "Uncategorized"
COMMENT_HOT_COUNT = 10
COMMENT_NORMAL_COUNT = 3
PUBLISHED_FEED_LIMIT = 50
NEWEST_POSTS_WITH_TAGS_LIMIT = 20 

def categories_by_name() -> QuerySet[Category]:
    "Return all categories alphabetically"
    return Category.objects.order_by("name")

def published_posts() -> QuerySet[Post]:
    "Return published posts from newest to oldest"
    return Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).order_by("-created_at")

def newest_published_posts() -> QuerySet[Post]:
    "Return 5 newest published posts"
    return published_posts()[:NEWEST_POSTS_LIMIT]

def post_by_slug(slug: str) -> Post | None:
    "Find a post by slug or return None"
    return Post.objects.filter(slug=slug).first()

def active_users_count() -> int:
    "Count active users excluding stuff"
    return User.objects.filter(
        is_active=True,
        is_staff=False
    ).count()

def has_drafts() -> bool:
    "Check whether any draft posts exist"
    return Post.objects.filter(
        status=Post.Status.DRAFT
    ).exists()

def published_posts_page(page: int) -> QuerySet[Post]:
    "Return one page of published posts"
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    return published_posts()[start:end]

def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    "Find posts whose titles contain the given word"
    return Post.objects.filter(title__icontains=word)

def users_with_email_domain(domain: str) -> QuerySet[User]:
    "Find users with the specified email domain"
    return User.objects.filter(email__iendswith=f"@{domain}")

def posts_without_category() -> QuerySet[Post]:
    "Find posts without category"
    return Post.objects.filter(category__isnull=True)

def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    "Find categories matching the given slugs"
    return Category.objects.filter(slug__in=slugs)

def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    "Find posts created in specific year and month"
    return Post.objects.filter(
        created_at__year=year,
        created_at__month=month
    )

def posts_last_days(days: int) -> QuerySet[Post]:
    "Find posts created within last specified number of days"
    start_date = timezone.now() - timedelta(days=days)
    return Post.objects.filter(created_at__gte=start_date)

def posts_between(start: date, end: date) -> QuerySet[Post]:
    "Find posts created between two dates"
    return Post.objects.filter(created_at__range=(start, end))

def author_published_posts(email: str) -> QuerySet[Post]:
    "Published posts of the author with this email. Letter case of the email does not matter."
    return Post.objects.filter(
        author__email__iexact=email,
        status=Post.Status.PUBLISHED
    )

def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    "Posts that have the tag with this slug."
    return Post.objects.filter(tags__slug=tag_slug).distinct()

def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    "Comments on posts of the category with this slug."
    return Comment.objects.filter(post__category__slug=category_slug)

def users_with_published_posts() -> QuerySet[User]:
    "Users who have at least one published post. Every user appears once."
    return User.objects.filter(posts__status=Post.Status.PUBLISHED).distinct()

def posts_without_tags() -> QuerySet[Post]:
    "Posts that have no tags."
    return Post.objects.filter(tags__isnull=True)

def users_without_comments() -> QuerySet[User]:
    "Users who have never written a comment."
    return User.objects.filter(comments__isnull=True)

def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    "Posts that have both tags. A post with only one of them is not included."
    return Post.objects.filter(
        tags__slug=first_slug
    ).filter(
        tags__slug=second_slug
    ).distinct()

def search_posts(text: str) -> QuerySet[Post]:
    "Posts that have text in the title or in the body. Letter case does not matter."
    return Post.objects.filter(
        Q(title__icontains=text) | Q(body__icontains=text)
    )

def published_posts_missing_info() -> QuerySet[Post]:
    "Published posts that have no category or no tags. Every post appears once."
    return Post.objects.filter(status=Post.Status.PUBLISHED).filter(
        Q(category__isnull=True) | Q(tags__isnull=True)
    ).distinct()

def edited_posts() -> QuerySet[Post]:
    "Posts that were edited more than 1 hour after they were created."
    return Post.objects.filter(
        updated_at__gt=F("created_at") + timedelta(hours=1)
    )

def comments_by_post_author() -> QuerySet[Comment]:	
    "Comments that the author of the post wrote under their own post."
    return Comment.objects.filter(
        author=F("post__author")
    )

def comments_before_post() -> QuerySet[Comment]:
    "Comments created before their post. Must be empty if Part 1 is correct."
    return Comment.objects.filter(
        created_at__lt=F("post__created_at")
    )

def published_authors_emails() -> list[str]:
    "Emails of authors who have published posts. Unique, sorted A → Z. A plain list of strings."
    return list(
        User.objects.filter(
            posts__status=Post.Status.PUBLISHED
        ).values_list(
            "email", flat=True
        ).distinct().order_by("email")
    )

def published_posts_overview() -> list[dict[str, Any]]:
    """One dict for each published post with exactly three keys: title, author_email, category_name.
    If a post has no category, category_name is "Uncategorized"."""
    return list(
        Post.objects.filter(
            status=Post.Status.PUBLISHED
        ).annotate(
            category_name=Coalesce(
                "category__name",
                Value(UNCATEGORIZED_LABEL)
            )
        ).values(
            "title", 
            "category_name",
            author_email=F("author__email"), 
        )
    )

def posts_stats() -> dict[str, Any]:
    """In one SQL query: the number of all posts, of published posts and of drafts,
    and the date of the first and of the last post. Keys: total, published, drafts, first_post_at, last_post_at."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at")
    )

def	average_comments_per_post() -> float:
    """The average number of comments on a published post, rounded to 2 digits after the point.
    Posts with 0 comments count too. If there are no posts, return 0.0."""
    result = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).annotate(
        comment_count=Count("comments")
    ).aggregate(
        average=Avg("comment_count")
    )["average"]

    return round(result or 0.0, 2)

def	categories_with_post_count() -> QuerySet[Category]:	
    "Every category with post_count. Most posts first. Same count → sort by name."
    return Category.objects.annotate(
        post_count=Count("posts")
    ).order_by("-post_count", "name")

def	categories_with_published_count() -> QuerySet[Category]:
    "Every category with published_count, the number of its published posts. "
    "Categories with 0 published posts must be in the result too."
    return Category.objects.annotate(
        published_count=Count(
            "posts",
            filter=Q(posts__status=Post.Status.PUBLISHED)
        )
    ).order_by("-published_count", "name")

def	top_authors() -> QuerySet[User]:	
    "The top 5 users by number of published posts, with published_count."
    return User.objects.annotate(
        published_count=Count(
            "posts",
            filter=Q(posts__status=Post.Status.PUBLISHED)
        )
    ).filter(
        published_count__gt=0
    ).order_by("-published_count", "email")[:5]

def	popular_tags(min_posts: int) -> QuerySet[Tag]:
    "Tags used in at least min_posts posts, with post_count."
    return Tag.objects.annotate(
        post_count=Count("posts", distinct=True)
    ).filter(
        post_count__gte=min_posts
    ).order_by("-post_count", "name")[:5]

def	posts_per_status() -> list[dict[str, Any]]:	
    "The number of posts for each status"
    return list(
        Post.objects.values("status").annotate(
            post_count=Count("id")
        ).order_by("status")
    )

def	users_activity() -> QuerySet[User]:
    "Every user with post_count and comment_count. Both numbers must be correct."
    return User.objects.annotate(
        post_count=Count("posts", distinct=True),
        comment_count=Count("comments", distinct=True)
    ).order_by("email")

def	search_users_by_full_name(text: str) -> QuerySet[User]:
    """Users whose full name ("First Last") contains text. Letter case does not matter.
    A search for "john smi" finds John Smith. Every user has full_name."""
    return User.objects.annotate(
        full_name=Concat(
            F("first_name"),
            Value(" "),
            F("last_name")
        )
    ).filter(
        full_name__icontains=text
    )

def	published_posts_per_month() -> list[dict[str, Any]]:
    """The number of published posts in each month: [{"month": ..., "count": 7}, ...], oldest month first."""
    return list(
        Post.objects.filter(
            status=Post.Status.PUBLISHED
        ).annotate(
            month = TruncMonth("created_at")
        ).values(
            "month"
        ).annotate(
            post_count=Count("id")
        ).order_by("month")
    )

def	posts_with_popularity() -> QuerySet[Post]:
    """Every post with comment_count and popularity:
    "hot" for 10 comments or more, "normal" for 3 or more, "quiet" for less."""
    return Post.objects.annotate(
        comment_count=Count("comments")
    ).annotate(
        popularity=Case(
            When(comment_count__gte=COMMENT_HOT_COUNT, then=Value("hot")),
            When(comment_count__gte=COMMENT_NORMAL_COUNT, then=Value("normal")),
            default=Value("quiet"),
            output_field=CharField()
        )
    )

def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Return the tag with this name. Create it (slug from the name) if it does not exist.
    The bool is True if the tag was created. Calling it twice must not create a second tag."""
    slug = slugify(name)
    return Tag.objects.get_or_create(
        slug=slug,
        defaults={"name": name}
    )

def	publish_old_drafts(days: int) -> int:
    "All drafts older than days days become published, with one SQL query. Return how many posts changed."
    cutoff = timezone.now() - timedelta(days=days)
    return Post.objects.filter(
        status=Post.Status.DRAFT,
        created_at__lt=cutoff
    ).update(
        status=Post.Status.PUBLISHED,
        updated_at=timezone.now()
    )


def	tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Add the tag to every post of the category.
    A post that already has this tag must not get it twice.
    Return the number of posts in the category."""
    category = Category.objects.get(slug=category_slug)
    tag = Tag.objects.get(slug=tag_slug)

    post_ids = list(
        Post.objects.filter(category=category).values_list("id", flat=True)
    )

    through_model = Post.tags.through

    through_model.objects.bulk_create(
        [
            through_model(post_id=post_id, tag_id=tag.id)
            for post_id in post_ids
        ],
        ignore_conflicts=True
    )

    return len(post_ids)

def	merge_categories(source_slug: str, target_slug: str) -> int:
    "Move all posts of the source category to the target category, then delete the source category."
    "Return how many posts moved."
    source = Category.objects.get(slug=source_slug)
    target = Category.objects.get(slug=target_slug)

    if source.id == target.id:
        return 0

    moved_count = Post.objects.filter(
        category=source
    ).update(category=target)

    source.delete()

    return moved_count


def	delete_inactive_users_comments() -> int:
    "Delete all comments written by inactive users. Return how many were deleted."
    deleted_count = Comment.objects.filter(
        author__is_active=False
    ).delete()

    return deleted_count


def published_feed() -> list[str]:
    """The 50 newest published posts as lines "title | author email | category name"
    (Uncategorized if there is no category).
    Exactly 1 SQL query."""
    posts = Post.objects.filter(
        status = Post.Status.PUBLISHED
    ).select_related(
        "author",
        "category"
    ).order_by("-created_at")[:PUBLISHED_FEED_LIMIT]
    
    return [
        f"{post.title} | {post.author.email} | "
        f"{post.category.name if post.category else UNCATEGORIZED_LABEL}"
        for post in posts
    ]

def	newest_posts_with_tags() -> list[str]:
    """The 20 newest posts as lines "title: tag1, tag2". At most 2 SQL queries."""
    posts = Post.objects.prefetch_related(
        "tags"
    ).order_by("-created_at")[:NEWEST_POSTS_WITH_TAGS_LIMIT]

    return [
        f"{post.title}: {', '.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]

def	categories_with_published_posts() -> dict[str, list[str]]:
    "{category name: [titles of its published posts, newest first]} for every category."
    "No drafts. At most 2 SQL queries."
    published_posts_queryset = Post.objects.filter(
        status = Post.Status.PUBLISHED
    ).order_by("-created_at")

    categories = Category.objects.prefetch_related(
        Prefetch(
            "posts",
            queryset=published_posts_queryset,
            to_attr="published_posts"
        )
    )

    return {
        category.name: [
            post.title for post in category.published_posts
        ]
        for category in categories
    }

def	posts_with_last_comment() -> QuerySet[Post]:
    "Published posts. Each has last_comment: the body of its newest comment (None if there are no comments)."
    last_comment = Comment.objects.filter(
        post=OuterRef("pk")
    ).order_by("-created_at")

    return Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).annotate(
        last_comment=Subquery(
            last_comment.values("body")[:1]
        )
    )

def	posts_with_staff_comments() -> QuerySet[Post]:
    "Posts with at least one comment from a staff user. Use Exists, not distinct()."
    staff_comment = Comment.objects.filter(
            post=OuterRef("pk"),
            author__is_staff=True
        )
    
    return Post.objects.annotate(
        has_staff_comment=Exists(staff_comment)
    ).filter(
        has_staff_comment=True
    )

def	users_with_draft_as_latest_post() -> QuerySet[User]:
    "Users whose newest post is a draft. Each user has latest_post_status."
    latest_post = Post.objects.filter(
        author=OuterRef("pk")
    ).order_by("-created_at")

    return User.objects.annotate(
        latest_post_status=Subquery(
            latest_post.values("status")[:1]
        )
    ).filter(
        latest_post_status=Post.Status.DRAFT
    )


QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post
}