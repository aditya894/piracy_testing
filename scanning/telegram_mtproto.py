import asyncio
import hashlib
import re
from typing import Iterable, Optional, List, Dict, Union
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone

from telethon import TelegramClient, functions
from telethon.errors import UserAlreadyParticipantError
from telethon.tl.types import Message

from .models import Platform, ScannedContent

# -------- text/link helpers ---------------------------------------------------
_LINK_RE = re.compile(r"(https?://\S+|t\.me/\S+|tg://\S+)", re.IGNORECASE)

def _extract_links(text: str) -> List[str]:
    if not text:
        return []
    return _LINK_RE.findall(text)

def _is_suspicious(text: str,
                   keywords: Optional[Iterable[str]],
                   allow_domains: Optional[Iterable[str]]) -> bool:
    if not text:
        return False

    # If keywords were provided, use them (case-insensitive)
    if keywords:
        t = text.lower()
        return any(str(k).lower() in t for k in keywords)

    # Otherwise: suspicious == contains a link not on the allow-list (or any link if no allow-list)
    links = _extract_links(text)
    if not links:
        return False
    if not allow_domains:
        return True

    allow = [d.lower().strip() for d in allow_domains if d]
    for raw in links:
        # t.me / tg:// special-cases
        if raw.lower().startswith(("t.me/", "http://t.me/", "https://t.me/", "tg://")):
            host = "t.me"
        else:
            try:
                host = urlparse(raw).netloc.lower()
            except Exception:
                host = ""

        if not any(host.endswith(ad) for ad in allow):
            # found a link NOT on the allow-list -> suspicious
            return True

    return False

def _author_from(msg: Message) -> Optional[str]:
    try:
        if msg.sender and getattr(msg.sender, "username", None):
            return f"@{msg.sender.username}"
        if msg.sender and (getattr(msg.sender, "first_name", None) or getattr(msg.sender, "last_name", None)):
            fn = (msg.sender.first_name or "").strip()
            ln = (msg.sender.last_name or "").strip()
            full = (fn + " " + ln).strip()
            return full or None
    except Exception:
        pass
    return None

def _message_url(entity, msg: Message) -> Optional[str]:
    try:
        username = getattr(entity, "username", None)
        if username:
            return f"https://t.me/{username}/{msg.id}"
    except Exception:
        pass
    return None

# -------- entity helpers ------------------------------------------------------
def _parse_channel_ref(raw: Union[str, int]) -> Union[str, int]:
    """
    Accepts:
      -100xxxxxxxxx (supergroup/channel ID),
      @username,
      https://t.me/<username>,
      https://t.me/c/<internal_id>/<msg_id> (private groups -> converts to -100<internal_id>)
    Returns either an int id or the cleaned string that Telethon can resolve.
    """
    if isinstance(raw, int):
        return raw
    s = str(raw).strip()

    # t.me/c/<internal_id>/... -> convert to -100<internal_id>
    low = s.lower()
    if low.startswith("https://t.me/c/") or low.startswith("http://t.me/c/"):
        try:
            part = s.split("/c/", 1)[1].split("/", 1)[0]
            return int("-100" + part)
        except Exception:
            pass

    # numeric id
    if s.startswith("-100") and s[4:].isdigit():
        try:
            return int(s)
        except Exception:
            pass

    # https://t.me/<username> -> <username>
    if low.startswith("https://t.me/") or low.startswith("http://t.me/"):
        return s.split("t.me/", 1)[1].split("?")[0].strip("/")

    # @username or invite links stay as-is (invite handling done later for users)
    return s

async def _resolve_entity(client: TelegramClient, channel_ref: Union[str, int], use_bot: bool):
    """
    - If bot: must already be a member/admin; cannot import invite links. Resolve by id or @username.
    - If user: can resolve and auto-join invite links (t.me/+HASH or t.me/joinchat/HASH).
    """
    # invite link join (user only)
    if not use_bot and isinstance(channel_ref, str):
        low = channel_ref.lower()
        invite_hash = None
        if "t.me/+" in low:
            invite_hash = channel_ref.split("+", 1)[1]
        elif "t.me/joinchat/" in low:
            invite_hash = channel_ref.split("joinchat/", 1)[1]
        if invite_hash:
            try:
                await client(functions.messages.ImportChatInviteRequest(invite_hash))
            except UserAlreadyParticipantError:
                pass  # already in

    # resolve entity
    return await client.get_entity(channel_ref)

# -------- async fetch (NO ORM here) ------------------------------------------
async def _collect_messages_async(channel: Union[str, int],
                                  keywords: Optional[Iterable[str]],
                                  limit: int,
                                  allow_domains: Optional[Iterable[str]]) -> List[Dict]:
    cfg = settings.TELEGRAM
    api_id = int(cfg["API_ID"])
    api_hash = cfg["API_HASH"]
    session_file = cfg.get("SESSION_FILE", ".tg_session")
    bot_token = cfg.get("BOT_TOKEN")
    prefer_bot = bool(bot_token)  # default to bot if available

    client = TelegramClient(session_file, api_id, api_hash)

    # Start client
    if prefer_bot:
        await client.start(bot_token=bot_token)
        use_bot = True
    else:
        # user session (will require a valid .tg_session already)
        await client.start()
        use_bot = False

    # Parse/resolve
    ref = _parse_channel_ref(channel)
    try:
        entity = await _resolve_entity(client, ref, use_bot)
    except Exception as e:
        await client.disconnect()
        if isinstance(ref, str) and ("t.me/+" in ref or "joinchat" in ref) and prefer_bot:
            raise RuntimeError(
                "Bots cannot join invite links. Pass the numeric chat id (-100...) "
                "or @username for channels where the bot is already a member."
            ) from e
        raise RuntimeError(f"Could not access channel '{channel}': {e}") from e

    # Iterate
    items: List[Dict] = []
    async for msg in client.iter_messages(entity, limit=limit):
        text = (getattr(msg, "message", "") or "").strip()
        if not _is_suspicious(text, keywords, allow_domains):
            continue

        platform_content_id = f"{getattr(entity, 'id', 'unknown')}:{msg.id}"
        url = _message_url(entity, msg) or "https://t.me"
        author = _author_from(msg)
        published_at = msg.date or timezone.now()

        items.append(
            dict(
                platform_content_id=platform_content_id,
                content_url=url,
                author=author,
                text=text,
                published_at=published_at,
            )
        )

    await client.disconnect()
    return items

# -------- public sync wrapper (does ORM only) --------------------------------
def scan_channel(channel: Union[str, int],
                 keywords: Optional[Iterable[str]] = None,
                 limit: int = 50,
                 allow_domains: Optional[Iterable[str]] = None) -> int:
    """
    Fetch from Telegram (async), then persist to DB (sync).
    - keywords: if provided, match by keywords (case-insensitive).
    - allow_domains: if provided (and no keywords), only links NOT on this allow-list are saved.
    """
    items = asyncio.run(_collect_messages_async(channel, keywords, limit, allow_domains))

    plat, _ = Platform.objects.get_or_create(
        name="telegram",
        defaults={"display_name": "Telegram", "base_url": "https://t.me", "is_active": True},
    )

    created = 0
    for it in items:
        content_hash = hashlib.sha256(
            f"{it['platform_content_id']}|{it['text']}".encode("utf-8")
        ).hexdigest()

        defaults = dict(
            scan_job=None,
            platform=plat,
            content_url=it["content_url"],
            content_type="text",
            title=f"Telegram message {it['platform_content_id'].split(':')[-1]}",
            description=None,
            author=it["author"],
            author_url=None,
            published_at=it["published_at"],
            view_count=None,
            like_count=None,
            share_count=None,
            text_content=it["text"],
            media_urls=[],
            metadata={
                "keywords": list(keywords) if keywords else None,
                "allow_domains": list(allow_domains) if allow_domains else None,
            },
            content_hash=content_hash,
        )

        _, was_created = ScannedContent.objects.update_or_create(
            platform=plat,
            platform_content_id=it["platform_content_id"],
            defaults=defaults,
        )
        if was_created:
            created += 1

    return created
