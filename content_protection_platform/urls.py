from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import home
from content_protection_platform.webhooks.views import (
    TelegramWebhookView,
    # NOTE: Prefer a single class to handle both GET (verify) and POST (messages):
    WhatsAppWebhookView,
)
from scanning.views import TelegramManualScanView

from users.views import UserViewSet, ClientConfigurationViewSet, ActivityLogViewSet
from scanning.views import PlatformViewSet, ScanJobViewSet, ScanScheduleViewSet, ScannedContentViewSet
from detection.views import (
    ProtectedContentViewSet, DetectionJobViewSet, ContentMatchViewSet,
    AIModelViewSet, FeedbackDataViewSet
)
from legal.views import (
    JurisdictionViewSet, DMCAClaimViewSet, CourtOrderViewSet,
    EvidenceLogViewSet, LegalComplianceViewSet
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"client-configs", ClientConfigurationViewSet, basename="client-config")
router.register(r"activity-logs", ActivityLogViewSet, basename="activity-log")

router.register(r"platforms", PlatformViewSet, basename="platform")
router.register(r"scan-jobs", ScanJobViewSet, basename="scan-job")
router.register(r"scan-schedules", ScanScheduleViewSet, basename="scan-schedule")
router.register(r"scanned-content", ScannedContentViewSet, basename="scanned-content")

router.register(r"protected-content", ProtectedContentViewSet, basename="protected-content")
router.register(r"detection-jobs", DetectionJobViewSet, basename="detection-job")
router.register(r"content-matches", ContentMatchViewSet, basename="content-match")
router.register(r"ai-models", AIModelViewSet, basename="ai-model")
router.register(r"feedback-data", FeedbackDataViewSet, basename="feedback-data")

router.register(r"jurisdictions", JurisdictionViewSet, basename="jurisdiction")
router.register(r"dmca-claims", DMCAClaimViewSet, basename="dmca-claim")
router.register(r"court-orders", CourtOrderViewSet, basename="court-order")
router.register(r"evidence-logs", EvidenceLogViewSet, basename="evidence-log")
router.register(r"legal-compliance", LegalComplianceViewSet, basename="legal-compliance")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("api/", include(router.urls)),

    # Telegram Bot webhook
    path("webhooks/telegram/<str:secret>/", TelegramWebhookView.as_view(), name="telegram-webhook"),

    # WhatsApp Cloud API: use ONE endpoint; implement get() + post() in WhatsAppWebhookView
    path("webhooks/whatsapp/", WhatsAppWebhookView.as_view(), name="whatsapp-webhook"),

    # Telegram manual scan (MTProto)
    path("api/scan/telegram/manual/", TelegramManualScanView.as_view(), name="telegram-manual-scan"),
]
