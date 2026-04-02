import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Seguridad: SECRET_KEY desde variable de entorno
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Clave API para endpoints de escritura
API_KEY = os.environ.get('API_KEY', 'dev-api-key-change-in-production')

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Dominio del sitio (para sitemap, robots, Open Graph)
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'http://localhost:8000')
SITE_AUTHOR = os.environ.get('SITE_AUTHOR', '')
SITE_AUTHOR_URL = os.environ.get('SITE_AUTHOR_URL', '')

# IPs excluidas del analizador de logs (separadas por coma)
WHITELIST_IPS = set(
    ip.strip() for ip in os.environ.get('WHITELIST_IPS', '127.0.0.1,::1').split(',') if ip.strip()
)


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'monitor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'monitor.middleware.RateLimitMiddleware',
]

ROOT_URLCONF = 'server_analytics.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'csp.context_processors.nonce',
                'monitor.context_processors.site_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'server_analytics.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

FORMAT_MODULE_PATH = [
    'server_analytics.formats',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
]

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CARDS_DIR = BASE_DIR / 'cards'

# ============================================================
# SEGURIDAD — Headers HTTP
# ============================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# En producción con HTTPS:
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'strict'

# ============================================================
# RATE LIMITING
# ============================================================
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60

CSRF_FAILURE_VIEW = 'monitor.views.csrf_failure'

# ============================================================
# CSP — Content Security Policy (django-csp 4.0)
# ============================================================
from csp.constants import NONE, SELF, NONCE

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [NONE],
        "script-src": [SELF, NONCE, "https://cdn.jsdelivr.net"],
        "style-src": [SELF, NONCE, "https://fonts.googleapis.com"],
        "font-src": [SELF, "https://fonts.gstatic.com"],
        "img-src": [SELF, "data:"],
        "connect-src": [SELF, "https://cdn.jsdelivr.net", "https://fonts.googleapis.com", "https://fonts.gstatic.com"],
        "frame-ancestors": [NONE],
        "base-uri": [SELF],
        "form-action": [SELF],
        "object-src": [NONE],
        "manifest-src": [SELF],
        "worker-src": [SELF],
    },
}
