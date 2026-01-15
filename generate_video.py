import os, requests
from moviepy.editor import *
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")

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
voice_url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
voice_data = {"text": script}
voice_response = requests.post(voice_url, json=voice_data, headers=headers)

voice_path = f"{OUTPUT_DIR}/voice.mp3"
open(voice_path, "wb").write(voice_response.content)

# ===== GENERATE IMAGES =====
image_paths = []
for i, prompt in enumerate(scenes):
    response = requests.post(
        "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json={"inputs": f"Cute cartoon style, {prompt}"}
    )
    img_path = f"{OUTPUT_DIR}/scene{i}.png"
    open(img_path, "wb").write(response.content)
    image_paths.append(img_path)

# ===== CREATE VIDEO =====
audio = AudioFileClip(voice_path)
duration = audio.duration / len(image_paths)

clips = [ImageClip(img).set_duration(duration) for img in image_paths]
video = concatenate_videoclips(clips, method="compose").set_audio(audio)

final_video = f"{OUTPUT_DIR}/final_video.mp4"
video.write_videofile(final_video, fps=24)

# ===== UPLOAD TO YOUTUBE =====
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
        "snippet": {"title": title, "description": description, "categoryId": "22"},
        "status": {"privacyStatus": "public"}
    },
    media_body=MediaFileUpload(final_video)
)

request.execute()
print("AI Video Generated & Uploaded Successfully!")
