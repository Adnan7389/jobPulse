from pathlib import Path
import os
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-test-key-replace-me')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:8002', 'http://127.0.0.1:8002'])
# Allow dynamic origins if they start with http:// or https://
for origin in env.list('CSRF_TRUSTED_ORIGINS_EXTRA', default=[]):
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)
CORS_ALLOW_ALL_ORIGINS = True  # For bot-backend communication if needed

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    
    # Local
    'apps.users',
    'apps.channels',
    'apps.jobs',
    'apps.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@db:5432/jobpulse')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')

# Auto-fix: Upstash requires SSL (rediss://)
if 'upstash' in CELERY_BROKER_URL:
    if not CELERY_BROKER_URL.startswith('rediss://'):
        CELERY_BROKER_URL = CELERY_BROKER_URL.replace('redis://', 'rediss://')
    
    # Celery Result Backend is strict: needs ssl_cert_reqs in the URL or specific options
    if 'ssl_cert_reqs' not in CELERY_BROKER_URL:
        separator = '&' if '?' in CELERY_BROKER_URL else '?'
        CELERY_BROKER_URL = f"{CELERY_BROKER_URL}{separator}ssl_cert_reqs=none"
    
    os.environ['CELERY_BROKER_URL'] = CELERY_BROKER_URL

if 'upstash' in CELERY_RESULT_BACKEND:
    if not CELERY_RESULT_BACKEND.startswith('rediss://'):
        CELERY_RESULT_BACKEND = CELERY_RESULT_BACKEND.replace('redis://', 'rediss://')
    
    if 'ssl_cert_reqs' not in CELERY_RESULT_BACKEND:
        separator = '&' if '?' in CELERY_RESULT_BACKEND else '?'
        CELERY_RESULT_BACKEND = f"{CELERY_RESULT_BACKEND}{separator}ssl_cert_reqs=none"
        
    os.environ['CELERY_RESULT_BACKEND'] = CELERY_RESULT_BACKEND

if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': 'none'}
    CELERY_RESULT_BACKEND_USE_SSL = {'ssl_cert_reqs': 'none'}
else:
    CELERY_BROKER_USE_SSL = False
    CELERY_RESULT_BACKEND_USE_SSL = False

# Bot Integration
BOT_INTERNAL_URL = env('BOT_INTERNAL_URL', default='http://127.0.0.1:8080')
