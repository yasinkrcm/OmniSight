from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # YOLO modellerini Django açılışında yükle (import sırasında değil)
        from api.views import _preload_models
        _preload_models()
