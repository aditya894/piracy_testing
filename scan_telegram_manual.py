# scan_telegram_manual.py
import os
import re
import sys
import json
import hashlib
from typing import Optional

import requests
from decouple import config
from telethon import TelegramClient, functions, types

# ---------- Config (env/.env) ----------
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")
PLATFORM_NAME = os.getenv("PLATFORM_NAME", "telegram")

API_ID = int(config("TG_API_ID"))
API_HASH = config("TG_API_HASH")
SESSION_FILE = config("TG_SESSION_FILE", default=".tg_session")

AUTH = (ADMIN_USER, ADMIN_PASS)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

URL_RE = re.compile(r"(https?://\S+)", re.IGNORECASE)


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def make_hash(chat_id: int, msg_id: int, text: str, url: Optional[str]) -> str:
    # Stable hash over chat, message id, url (if any) and text
    parts = [str(chat_id), str(msg_id), url or "", text or ""]
    return sha256("|".join(parts))


def get_or_create_platform_id() -> int:
    # Try fetch existing
    r = requests.get(f"{API_BASE}/api/platforms/", auth=AUTH, headers=HEADERS)
    r.raise_for_status()
    for p in r.json().get("results", []):
        if p.get("name") == PLATFORM_NAME:
            return p["id"]

    # Create if not found
    payload = {
        "name": PLATFORM_NAME,
        "display_name": "Telegram",
        "base_url": "https://t.me",
        "is_active": True,
    }
    r = requests.post(f"{API_BASE}/api/platforms/", auth=AUTH, headers=HEADERS, data=json.dumps(payload))
    r.raise_for_status()
    return r.json()["id"]


def message_link_for_private(entity_id: int, msg_id: int) -> str:
    # Works for private megagroups/channels: https://t.me/c/<peer_id>/<msg_id>
    # entity_id from Telethon for mega-groups is already the numeric peer id without -100 prefix in most cases.
    return f"https://t.me/c/{abs(entity_id)}/{msg_id}"


def post_scanned_content(platform_id: int, payload: dict) -> requests.Response:
    payload["platform"] = platform_id
    # POST
    return requests.post(
        f"{API_BASE}/api/scanned-content/",
        auth=AUTH,
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )


async def ensure_join_if_invite(client: TelegramClient, target: str):
    # Accept "https://t.me/+xxxx" and regular @ links. If already a member, Telegram raises a friendly error.
    if target.startswith("https://t.me/+"):
        try:
            invite_hash = target.rsplit("+", 1)[-1]
            await client(functions.messages.ImportChatInviteRequest(invite_hash))
            print("Invite link: joined.")
        except Exception as e:
            msg = str(e)
            if "already a participant" in msg:
                print("Invite link: already a participant.")
            else:
                print("Invite link join skipped:", msg)


def extract_urls(text: str) -> list[str]:
    return URL_RE.findall(text or "") if text else []


def build_payload(entity: types.TypePeer, m: types.Message, platform_id: int) -> dict:
    text = (m.message or "").strip()
    urls = extract_urls(text)
    url = urls[0] if urls else message_link_for_private(entity.id, m.id)
    return {
        "platform_content_id": f"{entity.id}-{m.id}",
        "content_type": "text",
        "content_url": url,
        "text_content": text,
        "content_hash": make_hash(entity.id, m.id, text, url),
    }


async def main():
    if len(sys.argv) < 2:
        print('Usage:\n  python scan_telegram_manual.py "<group title | invite link | @username>" [limit]\n')
        sys.exit(2)

    target = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    platform_id = get_or_create_platform_id()

    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start()  # uses your existing .tg_session
    print("Using session:", os.path.abspath(SESSION_FILE))

    await ensure_join_if_invite(client, target)

    # Resolve entity (title, @username, or invite link already joined)
    entity = await client.get_entity(target)
    print("Resolved entity:", entity.id)

    created = skipped = 0
    async for m in client.iter_messages(entity, limit=limit):
        # Only handle human messages (text/media captions); skip service messages
        if not isinstance(m, types.Message) or (not m.message and not m.media):
            continue

        try:
            payload = build_payload(entity, m, platform_id)
            # minimal guard: content_hash is required by your API
            if not payload["content_hash"]:
                print("skip: empty content_hash")
                skipped += 1
                continue

            resp = post_scanned_content(platform_id, payload)
            if resp.status_code in (200, 201):
                created += 1
            else:
                print(f"skip: {resp.status_code} -> {resp.text}")
                skipped += 1
        except Exception as e:
            print("skip:", e)
            skipped += 1

    print(f"Created {created} ScannedContent rows (skipped {skipped}).")
    await client.disconnect()


if __name__ == "__main__":
    # Run the async main
    import asyncio
    asyncio.run(main())
