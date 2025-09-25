from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Platform, ScanJob, ScanSchedule, ScannedContent, PlatformCredential
from .serializers import (
    PlatformSerializer,
    ScanJobSerializer,
    ScanScheduleSerializer,
    ScannedContentSerializer,
    PlatformCredentialSerializer,
)

def _ensure_platform(name: str, display_name: str, base_url: str) -> Platform:
    plat, _ = Platform.objects.get_or_create(
        name=name,
        defaults={"display_name": display_name, "base_url": base_url, "is_active": True},
    )
    changed = False
    if plat.display_name != display_name:
        plat.display_name = display_name
        changed = True
    if plat.base_url != base_url:
        plat.base_url = base_url
        changed = True
    if changed:
        plat.save(update_fields=["display_name", "base_url"])
    return plat

from .telegram_mtproto import scan_channel

class TelegramManualScanView(APIView):
    """
    POST JSON:
    {
      "channel": "<-100id | @username | https://t.me/username | https://t.me/c/<id>/<msg>>",
      "limit": 50,                               # optional
      "keywords": ["foo","bar"],                 # optional; if omitted, we scan links
      "allow_domains": ["t.me","edx.org"]        # optional allow-list
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        _ensure_platform("telegram", "Telegram", "https://t.me")

        channel = data.get("channel") or settings.TELEGRAM.get("TEST_CHANNEL")
        if not channel:
            return Response({"error": "channel is required"}, status=400)

        limit = int(data.get("limit") or 50)

        keywords = data.get("keywords")
        if isinstance(keywords, list) and len(keywords) == 0:
            keywords = None

        allow_domains = data.get("allow_domains") or None
        if isinstance(allow_domains, list) and len(allow_domains) == 0:
            allow_domains = None

        try:
            created_count = scan_channel(
                channel,
                keywords=keywords,
                limit=limit,
                allow_domains=allow_domains,
            )
        except RuntimeError as e:
            return Response({"error": str(e)}, status=400)

        return Response({"status": "ok", "items_created": created_count})


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

class PlatformViewSet(BaseViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer

class PlatformCredentialViewSet(BaseViewSet):
    queryset = PlatformCredential.objects.all()
    serializer_class = PlatformCredentialSerializer

class ScanJobViewSet(BaseViewSet):
    queryset = ScanJob.objects.all()
    serializer_class = ScanJobSerializer

class ScanScheduleViewSet(BaseViewSet):
    queryset = ScanSchedule.objects.all()
    serializer_class = ScanScheduleSerializer

class ScannedContentViewSet(BaseViewSet):
    queryset = ScannedContent.objects.all().order_by("-created_at")
    serializer_class = ScannedContentSerializer
