"""
Django settings for erSathi project.

An engineering license preparation platform with exam management,
progress tracking, gamification, and educational content management.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

# ============================================================================
# BASE CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# ============================================================================
# INSTALLED APPS
# ============================================================================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    # REST Framework & API
    "rest_framework",
    "drf_spectacular",
    # Authentication
    "djoser",
    "guardian",
    # Content Management
    "django_summernote",
    "autoslug",
    "smart_selects",
    # API Tools
    "django_filters",
    "corsheaders",
]

if DEBUG:
    THIRD_PARTY_APPS.append("debug_toolbar")

LOCAL_APPS = [
    "core.apps.CoreConfig",
    "courses.apps.CoursesConfig",
    "disciplines.apps.DisciplinesConfig",
    "subjects.apps.SubjectsConfig",
    "study_materials.apps.StudyMaterialsConfig",
    "questions.apps.QuestionsConfig",
    "assessments.apps.AssessmentsConfig",
    "progress.apps.ProgressConfig",
    "gamification.apps.GamificationConfig",
    "tags.apps.TagsConfig",
    "likes.apps.LikesConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ============================================================================
# AUTHENTICATION & PERMISSIONS
# ============================================================================

AUTH_USER_MODEL = "core.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

# ============================================================================
# MIDDLEWARE
# ============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

if DEBUG:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = ["127.0.0.1"]

ROOT_URLCONF = "erSathi.urls"

# ============================================================================
# TEMPLATES
# ============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "erSathi.wsgi.application"

# ============================================================================
# DATABASE
# ============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ============================================================================
# INTERNATIONALIZATION & LOCALIZATION
# ============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

# ============================================================================
# STATIC & MEDIA FILES
# ============================================================================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Summernote uploads handled via MEDIA_ROOT

# ============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================================
# REST FRAMEWORK & API CONFIGURATION
# ============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.DjangoModelPermissions",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# ============================================================================
# JWT CONFIGURATION
# ============================================================================

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
    "ACCESS_TOKEN_LIFETIME": timedelta(days=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=5),
}

# ============================================================================
# SPECTACULAR (DRF API DOCUMENTATION)
# ============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "ErSathi API",
    "DESCRIPTION": "An engineering license preparation platform with exam management, progress tracking, and gamification.",
    "VERSION": "1.0.2",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Local Development"},
        {"url": "https://api.ersathi.com", "description": "Production"},
    ],
}

# ============================================================================
# CORS CONFIGURATION
# ============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.environ.get("FRONTEND_URL", "http://localhost:3000"),
]

# ============================================================================
# SUMMERNOTE CONFIGURATION
# ============================================================================

SUMMERNOTE_THEME = "bs5"  # Bootstrap 5
SUMMERNOTE_CONFIG = {
    "iframe": True,
    "summernote": {
        "airMode": False,
        "width": "100%",
        "height": "400",
        "toolbar": [
            ["style", ["style"]],
            ["font", ["bold", "italic", "underline", "strikethrough", "clear"]],
            ["fontname", ["fontname"]],
            ["fontsize", ["fontsize"]],
            ["color", ["color"]],
            ["para", ["ul", "ol", "paragraph"]],
            ["height", ["height"]],
            ["table", ["table"]],
            ["insert", ["link", "picture", "video", "hr"]],
            ["view", ["fullscreen", "codeview", "help"]],
        ],
    },
    "attachment_require_authentication": True,
    "attachment_filesize_limit": 10 * 1024 * 1024,  # 10MB
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
