# webhooks/views.py
import json
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from scanning.models import Platform, ScanJob, ScannedContent
from django.utils import timezone
import hashlib

def _ensure_platform(name, display, base):
    p, _ = Platform.objects.get_or_create(name=name, defaults={"display_name":display, "base_url":base})
    return p

class TelegramWebhookView(APIView):
    authentication_classes = []  # you can add auth for prod
    permission_classes = []

    def post(self, request, secret):
        if secret != settings.TELEGRAM.get("WEBHOOK_SECRET"):
            return Response({"error":"unauthorized"}, status=401)
        data = request.data
        # Telegram webhook payload
        msg = data.get("message") or data.get("channel_post")
        if not msg: return Response({"ok": True})
        text = msg.get("text") or msg.get("caption") or ""
        chat = msg.get("chat", {})
        author = chat.get("title") or chat.get("username") or str(chat.get("id"))
        message_id = msg.get("message_id")
        url = f"https://t.me/{chat.get('username')}/{message_id}" if chat.get("username") else ""

        platform = _ensure_platform("telegram", "Telegram", "https://t.me")
        # You may create a synthetic ScanJob or keep None; here we keep None
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        ScannedContent.objects.create(
            scan_job=None,
            platform=platform,
            platform_content_id=str(message_id),
            content_url=url or "https://t.me",
            content_type="text",
            title=f"Telegram message {message_id}",
            description=None,
            author=author,
            author_url=url,
            published_at=timezone.now(),
            text_content=text,
            media_urls=[],
            metadata={"raw": data},
            content_hash=content_hash
        )
        return Response({"ok": True})

class WhatsAppVerifyView(APIView):
    """
    GET verification for WhatsApp Cloud API: Meta calls with hub.mode, hub.verify_token, hub.challenge
    """
    authentication_classes = []; permission_classes = []
    def get(self, request):
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == settings.WHATSAPP.get("VERIFY_TOKEN"):
            return HttpResponse(challenge, status=200)
        return HttpResponse("forbidden", status=403)

class WhatsAppWebhookView(APIView):
    """
    POST receiver: turns inbound messages to ScannedContent
    """
    authentication_classes = []; permission_classes = []
    def post(self, request):
        data = request.data
        platform = _ensure_platform("whatsapp", "WhatsApp", "https://www.whatsapp.com")
        # Parse message(s)
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    from_num = msg.get("from")
                    text = (msg.get("text") or {}).get("body") or ""
                    mid = msg.get("id")
                    url = f"https://wa.me/{from_num}"
                    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    ScannedContent.objects.create(
                        scan_job=None, platform=platform, platform_content_id=mid,
                        content_url=url, content_type="text",
                        title=f"WhatsApp message {mid}", author=from_num,
                        author_url=url, published_at=timezone.now(),
                        text_content=text, media_urls=[], metadata={"raw": msg},
                        content_hash=content_hash
                    )
        return Response({"ok": True})
