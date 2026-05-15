"""
Telegram News Bot
- Copy truc tiep media (anh/video) khong qua download
- Moi 50 tin gui 1 lan button Chat
"""

import asyncio
import logging
import sys
import io
from telethon import TelegramClient, Button
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from config import (
    API_ID, API_HASH, PHONE_NUMBER,
    CHANNEL_ID, SOURCE_CHANNELS, ZALO_LINK
)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

last_msg_ids = {}
CHAT_BUTTON = [Button.url("💬 Chat", ZALO_LINK)]
msg_count = 0
BUTTON_EVERY = 50


async def send_msg(client, msg, text, buttons=None):
    """Gui tin - dung media goc truc tiep, khong download"""
    try:
        has_media = msg.media and isinstance(
            msg.media, (MessageMediaPhoto, MessageMediaDocument)
        )

        if has_media:
            # Dung media object goc truc tiep, giu nguyen chat luong
            await client.send_file(
                CHANNEL_ID,
                msg.media,          # Dung truc tiep, khong download
                caption=text,
                buttons=buttons,
                supports_streaming=True  # Ho tro stream video
            )
            logger.info("Gui media goc OK!")
        else:
            await client.send_message(
                CHANNEL_ID, text,
                buttons=buttons
            )
            logger.info("Gui text OK!")

    except Exception as e:
        logger.error(f"Loi gui: {e}")
        # Fallback: gui text thoi
        try:
            await client.send_message(CHANNEL_ID, text, buttons=buttons)
        except:
            pass


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
            if buttons:
                logger.info(f"Tin thu {msg_count} - Them button Chat!")

            await send_msg(client, msg, text, buttons)
            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Loi check [{channel}]: {e}")


async def main():
    logger.info("Khoi dong bot...")

    client = TelegramClient('user_session', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)

    logger.info("Ket noi OK!")
    logger.info(f"Theo doi: {SOURCE_CHANNELS}")

    while True:
        for channel in SOURCE_CHANNELS:
            await check_channel(client, channel)
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(main())