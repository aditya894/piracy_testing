from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import ScanJob, ScanSchedule, ScannedContent
from .services import ScanJobManager
from users.models import ActivityLog
from detection.models import DetectionJob
from detection.services import ContentDetectionManager
import logging
logger=logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_scan_job_task(self, scan_job_id):
    try:
        scan_job=ScanJob.objects.get(id=scan_job_id)
        manager=ScanJobManager(scan_job.user)
        result=manager.execute_scan_job(scan_job)
        if result['status']=='success' and result.get('items_found',0)>0:
            trigger_content_detection_task.delay(scan_job_id)
        ActivityLog.objects.create(user=scan_job.user, action='scan_completed', description=f"Scan on {scan_job.platform.display_name} status: {result['status']}")
    except Exception as exc:
        logger.error(f"Error executing scan job {scan_job_id}: {exc}"); raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def trigger_content_detection_task(self, scan_job_id):
    try:
        scan_job=ScanJob.objects.get(id=scan_job_id)
        scanned_qs=ScannedContent.objects.filter(scan_job=scan_job)
        for content in scanned_qs:
            dj=DetectionJob.objects.create(user=scan_job.user, scanned_content=content, detection_types=['text','image','video'], similarity_threshold=getattr(getattr(scan_job.user,'configuration',None),'similarity_threshold',0.8))
            execute_detection_job_task.delay(dj.id)
    except Exception as exc:
        logger.error(f"Error triggering detection for scan job {scan_job_id}: {exc}")

@shared_task(bind=True, max_retries=3)
def execute_detection_job_task(self, detection_job_id):
    try:
        detection_job=DetectionJob.objects.get(id=detection_job_id)
        manager=ContentDetectionManager(detection_job.user)
        manager.run_detection(detection_job)
    except Exception as exc:
        logger.error(f"Error executing detection job {detection_job_id}: {exc}"); raise self.retry(exc=exc, countdown=60)

@shared_task
def cleanup_old_scan_data():
    from datetime import timedelta
    cutoff=timezone.now()-timedelta(days=90)
    ScannedContent.objects.filter(created_at__lt=cutoff).delete()
    return {'status':'ok','cutoff':cutoff.isoformat()}

@shared_task
def generate_weekly_report(): return {'status':'ok'}
@shared_task
def health_check(): return {'status':'healthy','timestamp': timezone.now().isoformat()}
