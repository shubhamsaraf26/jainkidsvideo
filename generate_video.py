import os, requests
from moviepy.editor import *
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ===== ENV KEYS =====
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")

# ===== FILE PATHS =====
STORY_FILE = "stories/story1.txt"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== READ STORY =====
with open(STORY_FILE, "r", encoding="utf-8") as f:
    data = f.read()

title = data.split("TITLE:")[1].split("DESCRIPTION:")[0].strip()
description = data.split("DESCRIPTION:")[1].split("SCRIPT:")[0].strip()
script = data.split("SCRIPT:")[1].split("SCENES:")[0].strip()
scenes = data.split("SCENES:")[1].strip().split("\n")

# ===== GENERATE VOICE =====
print("🔊 Generating voice with ElevenLabs...")

voice_url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
voice_headers = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}
voice_payload = {"text": script}

voice_response = requests.post(voice_url, json=voice_payload, headers=voice_headers)
voice_path = f"{OUTPUT_DIR}/voice.mp3"

with open(voice_path, "wb") as f:
    f.write(voice_response.content)

print("✅ Voice generated")

# ===== GENERATE IMAGES (Pollinations AI - Retry Only, No Fallback) =====
print("🎨 Generating images using Pollinations AI...")

image_paths = []

for i, prompt in enumerate(scenes):
    clean_prompt = prompt.replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/Cute%20colorful%20cartoon%20style,%20{clean_prompt}?width=1024&height=1024"
    
    img_path = f"{OUTPUT_DIR}/scene{i}.png"
    success = False

    # Retry up to 5 times
    for attempt in range(5):
        try:
            print(f"🌐 Downloading image {i+1}, attempt {attempt+1}/5")
            response = requests.get(url, timeout=120)

            if response.status_code == 200 and len(response.content) > 1000:
                with open(img_path, "wb") as f:
                    f.write(response.content)
                success = True
                break

        except Exception:
            print("⚠️ Connection timeout... retrying")

    # If still failed -> stop pipeline
    if not success:
        raise Exception(f"❌ Pollinations image generation failed for scene {i+1}. Re-run workflow.")

    image_paths.append(img_path)

print("✅ Images generated successfully")

# ===== CREATE VIDEO =====
print("🎬 Creating video...")

audio = AudioFileClip(voice_path)
duration_per_image = audio.duration / len(image_paths)

clips = []
for img in image_paths:
    clip = ImageClip(img).set_duration(duration_per_image)
    clips.append(clip)

video = concatenate_videoclips(clips, method="compose")
video = video.set_audio(audio)

final_video = f"{OUTPUT_DIR}/final_video.mp4"
video.write_videofile(final_video, fps=24)

print("✅ Video created")

# ===== UPLOAD TO YOUTUBE =====
print("📤 Uploading to YouTube...")

creds = Credentials(
    None,
    refresh_token=YOUTUBE_REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=YOUTUBE_CLIENT_ID,
    client_secret=YOUTUBE_CLIENT_SECRET
)

youtube = build("youtube", "v3", credentials=creds)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    },
    media_body=MediaFileUpload(final_video)
)

request.execute()

print("🎉 AI Video Generated & Uploaded Successfully!")
