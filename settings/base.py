from pathlib import Path

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy

from settings.conf import (
    BLOG_ENV_ID,
    BLOG_DB_HOST,
    BLOG_DB_NAME,
    BLOG_DB_PASSWORD,
    BLOG_DB_PORT,
    BLOG_DB_USER,
    BLOG_SECRET_KEY,
)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = BLOG_SECRET_KEY

DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.auths",
    "apps.blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "settings.wsgi.application"

AUTH_USER_MODEL = "auths.User"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": BLOG_DB_NAME,
        "USER": BLOG_DB_USER,
        "PASSWORD": BLOG_DB_PASSWORD,
        "HOST": BLOG_DB_HOST,
        "PORT": BLOG_DB_PORT,
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Almaty"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

UNFOLD = {
    "SITE_TITLE": "Blog API Admin",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Content Management",
    "SITE_SYMBOL": "article",
    "DASHBOARD_CALLBACK": "apps.blog.admin.dashboard_callback",
    "ENVIRONMENT": "apps.blog.admin.environment_callback",
    "COLORS": {
        "primary": {
            "50": "240 253 250",
            "100": "204 251 241",
            "200": "153 246 228",
            "300": "94 234 212",
            "400": "45 212 191",
            "500": "20 184 166",
            "600": "13 148 136",
            "700": "15 118 110",
            "800": "17 94 89",
            "900": "19 78 74",
            "950": "4 47 46",
        },
    },
    "SITE_DROPDOWN": [
        {
            "icon": "code",
            "title": "GitHub",
            "link": "https://github.com/SciSoulGalek",
        },
        {
            "icon": "menu_book",
            "title": "Unfold Documentation",
            "link": "https://unfoldadmin.com/docs/",
        },
    ],
    "COMMAND": {
        "search_models": True,
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Overview"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Content"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Posts"),
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                        "badge": "apps.blog.admin.draft_posts_badge",
                        "badge_variant": "warning",
                    },
                    {
                        "title": _("Comments"),
                        "icon": "comment",
                        "link": reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": _("Tags"),
                        "icon": "sell",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Access"),
                "separator": True,
                "collapsible": True,
                "permission": lambda request: request.user.is_superuser,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:auths_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": _("All"),
                    "link": reverse_lazy("admin:blog_post_changelist"),
                },
                {
                    "title": _("Published"),
                    "link": format_lazy(
                        "{}?status__exact=published",
                        reverse_lazy("admin:blog_post_changelist"),
                    ),
                },
                {
                    "title": _("Drafts"),
                    "link": format_lazy(
                        "{}?status__exact=draft",
                        reverse_lazy("admin:blog_post_changelist"),
                    ),
                },
            ],
        },
    ],
}