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

# ===== ALWAYS PICK LATEST STORY FILE =====
STORY_DIR = "stories"

story_files = sorted([f for f in os.listdir(STORY_DIR) if f.endswith(".txt")])

if not story_files:
    print("⚠️ No story files found in stories folder. Exiting.")
    exit(0)

STORY_FILE = os.path.join(STORY_DIR, story_files[-1])

print(f"📘 Processing latest story file: {STORY_FILE}")

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
print("🔊 Generating voice...")

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

# ===== GENERATE IMAGES (Pollinations) =====
print("🎨 Generating images...")

image_paths = []

for i, prompt in enumerate(scenes):
    clean_prompt = prompt.replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/Cute%20colorful%20cartoon%20style,%20{clean_prompt}?width=1024&height=1024"

    img_path = f"{OUTPUT_DIR}/scene{i}.png"
    success = False

    for attempt in range(5):
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(img_path, "wb") as f:
                    f.write(response.content)
                success = True
                break
        except:
            print("⚠️ Image timeout... retrying")

    if not success:
        raise Exception(f"❌ Image generation failed for scene {i+1}")

    image_paths.append(img_path)

print("✅ Images generated")

# ===== CREATE VIDEO =====
print("🎬 Creating video...")

audio = AudioFileClip(voice_path)
duration_per_image = audio.duration / len(image_paths)

clips = []
for img in image_paths:
    clips.append(ImageClip(img).set_duration(duration_per_image))

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

print("🎉 Video Generated & Uploaded Successfully!")