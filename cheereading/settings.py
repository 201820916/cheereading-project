"""
Django settings for cheereading project. (Production Ready)
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. CORE SETTINGS (보안 및 배포 설정)
# ==============================================================================

# ⚠️ [보안] SECRET_KEY를 환경 변수에서 불러옵니다.
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 
    'django-insecure-3r-ary4or_!rp%7c7ywz86@(0fj9$tyw02q-f(85(c!$8g^as7' # 로컬 개발용 (이것도 바꿔주는게 좋음)
)

# ⚠️ [보안] DEBUG 모드를 환경 변수에서 불러옵니다.
# Render에서는 자동으로 'False'가 됩니다.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ⚠️ [배포] ALLOWED_HOSTS 설정
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# ==============================================================================
# 2. APPLICATION DEFINITION
# ==============================================================================

INSTALLED_APPS = [
    'users.apps.UsersConfig', 
    'books.apps.BooksConfig',
    'plans.apps.PlansConfig',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # 👈 Whitenoise는 여기에 필요 없습니다.
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 👈 여기에만 있으면 됩니다.
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cheereading.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # 👈 BASE_DIR / 'templates'
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

WSGI_APPLICATION = 'cheereading.wsgi.application'


# ==============================================================================
# 3. DATABASE (로컬 MariaDB / 서버 PostgreSQL 자동 전환)
# ==============================================================================

DATABASES = {
    'default': {
        # 로컬 개발 환경 (MariaDB/MySQL)
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cheereading',  # 👈 [본인 로컬 DB 이름]으로 수정
        'USER': 'root',           # 👈 [본인 로컬 DB 유저]로 수정
        'PASSWORD': 'password',   # 👈 [본인 로컬 DB 비번]으로 수정
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Render 서버 환경일 경우 (DATABASE_URL 환경 변수가 감지되면)
# Render의 PostgreSQL 설정으로 덮어씁니다.
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True # Render의 PostgreSQL은 SSL이 필수입니다.
    )

# ==============================================================================
# 4. PASSWORD & INTERNATIONALIZATION
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# 5. STATIC FILES (CSS, JS) - Whitenoise 설정
# ==============================================================================

STATIC_URL = 'static/'
# 👈 [필수] collectstatic이 파일을 모을 폴더 (배포용)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 👈 [필수] 개발 중 정적 파일이 있는 원본 폴더 (개발용)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# 👈 [필수] Django 4.2+ 권장 스토리지 설정
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ==============================================================================
# 6. MEDIA FILES (User Uploads)
# ==============================================================================

# ⚠️ [경고] Render는 재배포 시 'media' 폴더의 파일이 모두 삭제됩니다.
# 졸업 작품 시연용으로만 임시 사용하고, 파일이 사라지는 것을 감수해야 합니다.
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==============================================================================
# 7. AUTH & EMAIL (보안 설정)
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = '/users/profile/'
LOGIN_URL = '/users/login/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ⚠️ [보안] 이메일 설정도 환경 변수에서 불러옵니다.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'kkupsh2@gmail.com' # 👈 보내는 이메일 주소 (이건 노출돼도 괜찮음)

# ⚠️ [보안] Render의 'Environment' 탭에 등록해야 합니다.
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

SITE_ID = 1
