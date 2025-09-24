# scanning/telegram_mtproto.py
import asyncio, hashlib
from telethon import TelegramClient
from django.conf import settings
from django.utils import timezone
from .models import Platform, ScannedContent

def _platform():
    from .views import _ensure_platform as ep
    return ep("telegram", "Telegram", "https://t.me")

async def _scan_channel_async(channel, keywords, limit=50):
    cfg = settings.TELEGRAM
    client = TelegramClient(cfg["SESSION_FILE"], cfg["API_ID"], cfg["API_HASH"])
    await client.start()
    results = []
    async for msg in client.iter_messages(entity=channel, limit=limit, search=" | ".join(keywords)):
        text = msg.message or ""
        url = f"https://t.me/{channel.lstrip('@')}/{msg.id}" if channel.startswith("@") else ""
        results.append({
            "id": str(msg.id), "text": text, "url": url,
            "date": msg.date, "author": getattr(msg.sender, "username", None),
        })
    await client.disconnect()
    return results

def scan_channel(channel_handle: str, keywords: list[str], limit=50) -> int:
    """Returns number of ScannedContent rows created."""
    platform = _platform()
    found = asyncio.run(_scan_channel_async(channel_handle, keywords, limit))
    n = 0
    for item in found:
        content_hash = hashlib.sha256((item["text"] or "").encode("utf-8")).hexdigest()
        ScannedContent.objects.create(
            scan_job=None, platform=platform,
            platform_content_id=item["id"], content_url=item["url"] or "https://t.me",
            content_type="text", title=f"Telegram message {item['id']}",
            author=item.get("author"), author_url=item.get("url"),
            published_at=item["date"] or timezone.now(),
            text_content=item["text"], media_urls=[], metadata={"keywords": keywords},
            content_hash=content_hash
        )
        n += 1
    return n
