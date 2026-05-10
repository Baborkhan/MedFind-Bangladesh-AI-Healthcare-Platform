# medfind/medfind_project/settings_render.py
# ═══════════════════════════════════════════════════
#  Render.com Production Settings — MedFind Bangladesh
# ═══════════════════════════════════════════════════
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "medfind-render-change-me-in-env-vars"
)

DEBUG = False

ALLOWED_HOSTS = [h.strip() for h in os.environ.get(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,.onrender.com"
).split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "donate",
    "ai",
    "otp_auth",
    "apps.accounts",
    "apps.doctors",
    "apps.appointments",
    "apps.admin_panel",
    "apps.billing",
    "apps.common",
    "apps.analytics_api",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "medfind_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # On Render, frontend is served separately (Firebase/static host)
        # so we just point to a local templates folder (no TemplateView at /)
        "DIRS": [],
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

WSGI_APPLICATION = "medfind_project.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # Fallback: SQLite (Render free tier without PostgreSQL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ── Cache — no Redis on free tier ────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── MongoDB (Atlas free tier — chat logs, analytics, audit) ──────────────────
MONGODB_URI  = os.environ.get("MONGODB_URI",  "")   # Set in Render env vars
MONGODB_NAME = os.environ.get("MONGODB_NAME", "medfind")

# ── AI ────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")
AI_MAX_TOKENS   = int(os.environ.get("AI_MAX_TOKENS", "1500"))
AI_MAX_HISTORY  = 14

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# ── Static Files — WhiteNoise ─────────────────────────────────────────────────
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR.parent / "frontend" / "static"
] if (BASE_DIR.parent / "frontend" / "static").exists() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "https://medfind-bangladesh.web.app,https://www.medfind-bangladesh.com,https://baborkhan.github.io"
).split(",") if o.strip()]

# ── CSRF ──────────────────────────────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "https://medfind-bangladesh.web.app,https://www.medfind-bangladesh.com,https://medfind-bangladesh-ai-healthcare-platform.onrender.com,https://baborkhan.github.io"
).split(",") if o.strip()]

# ── Security ──────────────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER      = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
SECURE_SSL_REDIRECT            = False  # Render handles HTTPS at the proxy level
SECURE_PROXY_SSL_HEADER        = ("HTTP_X_FORWARDED_PROTO", "https")  # Trust Render's proxy
SECURE_HSTS_SECONDS            = 31536000   # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True
X_FRAME_OPTIONS                = "DENY"
# W008 silenced: Render's load balancer terminates SSL — app itself runs HTTP internally
SILENCED_SYSTEM_CHECKS         = ["security.W008"]

# ── Session ───────────────────────────────────────────────────────────────────
SESSION_ENGINE     = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400 * 7

# ── Email — Gmail SMTP ────────────────────────────────────────────────────────
EMAIL_BACKEND       = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST          = "smtp.gmail.com"
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL  = f"MedFind Bangladesh <{os.environ.get('EMAIL_HOST_USER', 'noreply@medfind.com')}>"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Dhaka"

# ── DRF + JWT ─────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/hour",
        "user": "200/hour",
    },
}

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
USE_I18N = True
USE_TZ   = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "ai": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}


# ── Startup Validation ────────────────────────────────────────────────────────
import logging as _log
_logger = _log.getLogger('django')

def _startup_check():
    issues = []
    if not GEMINI_API_KEY:
        issues.append('❌ GEMINI_API_KEY missing — AI will not work. Set in Render Dashboard.')
    else:
        _logger.info('✅ GEMINI_API_KEY configured (len=%d)', len(GEMINI_API_KEY))

    if not EMAIL_HOST_USER:
        issues.append('❌ EMAIL_HOST_USER missing — OTP emails will fail.')
    else:
        _logger.info('✅ EMAIL configured: %s', EMAIL_HOST_USER)

    if issues:
        for issue in issues:
            _logger.warning(issue)

_startup_check()
