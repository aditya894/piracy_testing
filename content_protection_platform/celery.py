import os
from celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE','content_protection_platform.settings')
app = Celery('content_protection_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'cleanup-old-scan-data-daily': {'task':'scanning.tasks.cleanup_old_scan_data','schedule':24*60*60},
    'weekly-report': {'task':'scanning.tasks.generate_weekly_report','schedule':7*24*60*60},
    'health-check': {'task':'scanning.tasks.health_check','schedule':60},
}
@app.task(bind=True)
def debug_task(self): print(f'Request: {self.request!r}')
