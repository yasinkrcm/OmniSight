import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'daphne',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'channels',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'OPTIONS']

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MongoDB (via pymongo — used directly in views, not through Django ORM)
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DB_NAME = 'ml_website'

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Pre-configured model paths
MODEL_PATHS = {
    'car_damage': os.path.join(BASE_DIR.parent, 'CarModel.pt'),
    'ppe': os.path.join(BASE_DIR.parent, 'ppe.pt'),
    'peoplecounter': os.path.join(BASE_DIR, 'yolo26n.pt'),
}

# Roboflow PPE model config (Serverless REST API)
# API anahtarını ortam değişkeninden oku — asla koda gömme!
ROBOFLOW_API_KEY = os.environ.get('ROBOFLOW_API_KEY', '')
ROBOFLOW_PPE_URL = 'https://serverless.roboflow.com/ppe-gzzdx/1'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.JSONParser',
    ],
}

# Max upload size: 500MB (for .pt model files)
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000
