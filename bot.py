from pyrogram import Client, filters
import os
import requests
import subprocess

# Environment variables
print("DEBUG: API_ID =", os.environ.get("API_ID"))
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SIGHTENGINE_USER = os.environ.get("SIGHTENGINE_USER")
SIGHTENGINE_SECRET = os.environ.get("SIGHTENGINE_SECRET")

# Init bot
app = Client("nsfw_filter_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_frame(media_path):
    """Extract a frame from video, animation, or sticker."""
    output_image = media_path + "_frame.jpg"
    try:
        cmd = ["ffmpeg", "-y", "-i", media_path, "-vf", "thumbnail", "-frames:v", "1", output_image]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(output_image):
            return output_image
    except Exception as e:
        print("Error extracting frame:", e)
    return None

def is_nsfw(image_path):
    """Send image to Sightengine API and detect NSFW."""
    try:
        url = "https://api.sightengine.com/1.0/check.json"
        files = {'media': open(image_path, 'rb')}
        data = {
            'models': 'nudity',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET
        }
        response = requests.post(url, files=files, data=data, timeout=30)
        result = response.json()
        print("API response:", result)

        score = result.get("nudity", {}).get("raw", 0)
        return score >= 0.2  # High sensitivity
    except Exception as e:
        print("API error:", e)
        return False

@app.on_message(filters.group & (filters.photo | filters.sticker | filters.video | filters.animation))
def handle_media(client, message):
    media_path = None
    try:
        print(f"Media received from {message.from_user.first_name}")
        media_path = client.download_media(message)
        print("Downloaded:", media_path)

        if message.video or message.animation or message.sticker:
            image_path = extract_frame(media_path)
        else:
            image_path = media_path

        if image_path and is_nsfw(image_path):
            message.delete()
            print("NSFW content detected. Message deleted.")
        else:
            print("Content is safe.")

    except Exception as e:
        print("Error:", e)
    finally:
        for path in [media_path, image_path] if 'image_path' in locals() else [media_path]:
            if path and os.path.exists(path):
                os.remove(path)

print("Bot is running and monitoring group messages...")
app.run()
