"""
Telegram News Bot - Render Web Service
Them web server de Render khong sleep
"""

import asyncio
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, Button
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
CHANNEL_IDS = [int(x.strip()) for x in os.environ['CHANNEL_ID'].split(',')]
SOURCE_CHANNELS = os.environ['SOURCE_CHANNELS'].split(',')
ZALO_LINK = os.environ['ZALO_LINK']
SESSION_STRING = os.environ.get('SESSION_STRING', '')
PORT = int(os.environ.get('PORT', 8080))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

last_msg_ids = {}
CHAT_BUTTON = [Button.url("💬 Chat", ZALO_LINK)]
msg_count = 0
BUTTON_EVERY = 50


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass


def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    server.serve_forever()


async def send_msg(client, msg, text, buttons=None):
    has_media = msg.media and isinstance(
        msg.media, (MessageMediaPhoto, MessageMediaDocument)
    )
    for channel_id in CHANNEL_IDS:
        try:
            if has_media:
                await client.send_file(
                    channel_id, msg.media,
                    caption=text, buttons=buttons,
                    supports_streaming=True
                )
            else:
                await client.send_message(channel_id, text, buttons=buttons)
            logger.info(f"Gui den kenh {channel_id} OK!")
        except Exception as e:
            logger.error(f"Loi gui den kenh {channel_id}: {e}")


async def check_channel(client, channel):
    global msg_count
    try:
        msgs = await client.get_messages(channel, limit=5)
        if channel not in last_msg_ids:
            if msgs:
                last_msg_ids[channel] = msgs[0].id
                logger.info(f"[{channel}] Khoi tao ID: {msgs[0].id}")
            return
        new_msgs = [m for m in msgs if m.id > last_msg_ids[channel]]
        if not new_msgs:
            return
        last_msg_ids[channel] = new_msgs[0].id
        for msg in reversed(new_msgs):
            text = msg.text or msg.caption or ""
            if len(text.strip()) < 5:
                continue
            msg_count += 1
            logger.info(f"[{channel}] Tin #{msg_count}: {text[:60]}...")
            buttons = CHAT_BUTTON if msg_count % BUTTON_EVERY == 0 else None
            await send_msg(client, msg, text, buttons)
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Loi check [{channel}]: {e}")


async def main():
    logger.info("Khoi dong bot...")

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logger.info(f"Web server chay tren port {PORT}")

    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    logger.info("Ket noi Telegram OK!")
    logger.info(f"Theo doi: {SOURCE_CHANNELS}")

    while True:
        for channel in SOURCE_CHANNELS:
            await check_channel(client, channel)
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(main())