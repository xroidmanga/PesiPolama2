import os
import random
import asyncio
import aiohttp
import tempfile
import subprocess
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import logging
import shutil
from PIL import Image
from io import BytesIO

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

def get_random_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache"
    }

API_ID = int(os.environ.get("API_ID", 21003880))
API_HASH = os.environ.get("API_HASH", "bf157632e77ea8b28ff3e186dc95ab35")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8156784176:AAFu4Yr_t2zu2cFGunPxFyyQIKRQ4hTFmwo")
CHANNEL_ID = -1002569442302
# Hey man your ☝️ channel ID direct add here


BLACKLIST_FILE = "blacklist.txt"

def is_blacklisted(name: str) -> bool:
    if not os.path.exists(BLACKLIST_FILE):
        return False
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        return name.strip().lower() in (line.strip().lower() for line in f)

def add_to_blacklist(name: str):
    with open(BLACKLIST_FILE, "a", encoding="utf-8") as f:
        f.write(f"{name.strip()}\n")

app = Flask(__name__)
bot = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.route('/')
def home():
    return '✅ Bot is running!'

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

API_LIST = [
    "https://you-pom-lover.vercel.app/xvideos/10/Bangladeshi",
    "https://you-pom-lover.vercel.app/xvideos/10/desi",
    "https://you-pom-lover.vercel.app/xnxx/10/college",
    "https://you-pom-lover.vercel.app/xnxx/10/school",
    "https://you-pom-lover.vercel.app/xvideos/10/stepdaughter",
    "https://you-pom-lover.vercel.app/xvideos/10/sister",
    "https://you-pom-lover.vercel.app/xvideos/10/bhabhi"
]

async def fetch_api_data(session, api_url):
    try:
        async with session.get(api_url, headers=get_random_headers(), timeout=20) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("data", [])
            else:
                logger.warning(f"API status: {resp.status} from {api_url}")
    except Exception as e:
        logger.error(f"API Fetch Error from {api_url}: {e}")
    return []

async def download_video(video_url, output_path):
    try:
        cmd = [
            "aria2c",
            video_url,
            "--out", os.path.basename(output_path),
            "--dir", os.path.dirname(output_path),
            "--allow-overwrite=true",
            "--max-connection-per-server=16",
            "--split=16",
            "--summary-interval=0",
            "--console-log-level=warn"
        ]
        
        logger.info(f"Downloading video: {video_url}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            await asyncio.wait_for(process.communicate(), timeout=300)
        except asyncio.TimeoutError:
            logger.error("Download timed out")
            process.kill()
            await process.communicate()
            return False
        
        if process.returncode != 0:
            logger.error(f"Download failed with code {process.returncode}")
            return False
        
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
        
    except Exception as e:
        logger.error(f"Download exception: {str(e)}")
        return False

async def prepare_thumbnail(url, path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img_bytes = await resp.read()
                    img = Image.open(BytesIO(img_bytes)).convert("RGB")
                    img.save(path, "JPEG")
                    return True
    except Exception as e:
        logger.error(f"Thumbnail convert failed: {e}")
    return False

async def auto_post():
    logger.info("🔁 Auto post started...")

    while True:
        try:
            for selected_api in API_LIST:
                logger.info(f"🌐 Processing API: {selected_api}")
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    async with aiohttp.ClientSession() as session:
                        api_data = await fetch_api_data(session, selected_api)

                    if not api_data:
                        logger.warning(f"⚠️ No data from API: {selected_api}")
                        await asyncio.sleep(60)  # wait before next API
                        continue

                    success_count = 0
                    for idx, item in enumerate(api_data[:5]):
                        if 'name' not in item or 'content_url' not in item:
                            logger.warning(f"❌ Invalid item at index {idx}: {item}")
                            continue

                        video_name = item['name'].strip()
                        video_url = item['content_url']
                        thumb_url = item.get('thumbnail')

                        if is_blacklisted(video_name):
                            logger.info(f"🚫 Skipping blacklisted video: {video_name}")
                            continue

                        caption = (
                            f"🎀 <b>{video_name}</b>\n"
                            f"✦▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬✦\n"
                            f"🐉 {item.get('description', 'No description available.')}\n\n"
                            f"<b>⚡️ Stay tuned for more videos on our channel!</b>"
                        )

                        file_name = f"video_{idx}_{random.randint(1000,9999)}.mp4"
                        file_path = os.path.join(temp_dir, file_name)

                        download_success = await download_video(video_url, file_path)
                        if not download_success:
                            logger.error(f"❌ Download failed for video {idx}")
                            continue

                        thumb_path = os.path.join(temp_dir, f"thumb_{idx}.jpg")
                        thumb_ok = await prepare_thumbnail(thumb_url, thumb_path)
                        thumb_file = thumb_path if thumb_ok else None

                        buttons = InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎥 Watch online 🎥", url=video_url)],
                            [InlineKeyboardButton("🎀 Join Our Channel 🎀", url="https://t.me/offltbw")]
                        ])

                        try:
                            await bot.send_video(
                                chat_id=CHANNEL_ID,
                                video=file_path,
                                caption=caption,
                                parse_mode=ParseMode.HTML,
                                reply_markup=buttons,
                                supports_streaming=True,
                                thumb=thumb_file
                            )
                            add_to_blacklist(video_name)
                            success_count += 1
                            logger.info(f"✅ Posted: {video_name}")
                        except Exception as e:
                            logger.error(f"❌ Error sending video: {e}")

                        # Delay between each video
                        await asyncio.sleep(30)  # <-- To avoid Telegram rate limit

                logger.info(f"✅ Finished API: {selected_api} | Videos posted: {success_count}")
                await asyncio.sleep(60)  # Wait between APIs

        except Exception as e:
            logger.exception(f"🚨 Auto post error: {e}")
        
        # After full round
        logger.info("🕒 Sleeping for 5 minutes before next round...")
        await asyncio.sleep(300)

@bot.on_message(filters.command("start"))
async def start_bot(client, message):
    await message.reply("🤖 Bot is running!")

if __name__ == "__main__":
    if shutil.which("aria2c") is None:
        logger.error("aria2c is not installed! Please install it first.")
        exit(1)
    
    Thread(target=run_flask, daemon=True).start()
    bot.loop.create_task(auto_post())
    
    logger.info("🤖 Bot is starting...")
    bot.run()
