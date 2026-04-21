import os
from pathlib import Path
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Base directory: ResumeBuilder/
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(dotenv_path=BASE_DIR / '.env')
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-for-dev-only')

if not SECRET_KEY:
    SECRET_KEY = 'django-insecure-debug-key-only'

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# ──────────────────────────────────────────────
# Development settings (set DEBUG=False for production)
# ──────────────────────────────────────────────
DEBUG = True
ALLOWED_HOSTS = ['*', 'pranav_builds.pythonanywhere.com']

# ──────────────────────────────────────────────
# Apps
# ──────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'builder',
]

# ──────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ResumeProject.urls'

# ──────────────────────────────────────────────
# Templates — point to ResumeBuilder/templates/
# ──────────────────────────────────────────────
TEMPLATES_DIR = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ResumeProject.wsgi.application'

# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ──────────────────────────────────────────────
# Internationalization
# ──────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────
# Static & Media files
# ──────────────────────────────────────────────
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ──────────────────────────────────────────────
# Auth redirects
# ──────────────────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ──────────────────────────────────────────────
# Default primary key field type
# ──────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
