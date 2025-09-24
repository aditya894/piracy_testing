from rest_framework import viewsets, permissions
from .models import Platform, ScanJob, ScanSchedule, ScannedContent, PlatformCredential
from .serializers import PlatformSerializer, ScanJobSerializer, ScanScheduleSerializer, ScannedContentSerializer, PlatformCredentialSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .telegram_mtproto import scan_channel

class TelegramManualScanView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        channel = request.data.get("channel") or settings.TELEGRAM.get("TEST_CHANNEL")
        keywords = request.data.get("keywords") or []
        if not channel or not keywords:
            return Response({"error":"channel and keywords required"}, status=400)
        count = scan_channel(channel, keywords, limit=50)
        return Response({"status":"ok","items_created":count})

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes=[permissions.IsAuthenticated]

class PlatformViewSet(BaseViewSet):
    queryset=Platform.objects.all(); serializer_class=PlatformSerializer

class ScanJobViewSet(BaseViewSet):
    queryset=ScanJob.objects.all(); serializer_class=ScanJobSerializer

class ScanScheduleViewSet(BaseViewSet):
    queryset=ScanSchedule.objects.all(); serializer_class=ScanScheduleSerializer

class ScannedContentViewSet(BaseViewSet):
    queryset=ScannedContent.objects.all(); serializer_class=ScannedContentSerializer
