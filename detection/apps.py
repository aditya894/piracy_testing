from django.apps import AppConfig
from django.conf import settings
class DetectionConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='detection'
    def ready(self):
        if getattr(settings,'CONFIGURE_MODELS_ON_STARTUP', False):
            from .services import initialize_ai_models
            initialize_ai_models()
