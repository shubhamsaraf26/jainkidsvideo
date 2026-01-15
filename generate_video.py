import os, requests
from moviepy.editor import *
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
OPENAI_IMAGE_KEY = os.getenv("OPENAI_IMAGE_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

story_file = "stories/story1.txt"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Read story file
with open(story_file, "r", encoding="utf-8") as f:
    data = f.read()

title = data.split("TITLE:")[1].split("DESCRIPTION:")[0].strip()
description = data.split("DESCRIPTION:")[1].split("SCRIPT:")[0].strip()
script = data.split("SCRIPT:")[1].split("SCENES:")[0].strip()
scenes = data.split("SCENES:")[1].strip().split("\n")

# Generate Voice using ElevenLabs
voice_url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
voice_data = {"text": script, "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}}
r = requests.post(voice_url, json=voice_data, headers=headers)
voice_path = f"{output_dir}/voice.mp3"
open(voice_path, "wb").write(r.content)

# Generate Images using OpenAI
image_paths = []
for i, prompt in enumerate(scenes):
    img_api = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {OPENAI_IMAGE_KEY}"}
    payload = {"prompt": prompt, "n": 1, "size": "1024x1024"}
    res = requests.post(img_api, json=payload, headers=headers).json()
    img_url = res["data"][0]["url"]
    img_data = requests.get(img_url).content
    path = f"{output_dir}/scene{i}.png"
    open(path, "wb").write(img_data)
    image_paths.append(path)

# Create Video
audio = AudioFileClip(voice_path)
duration_per_image = audio.duration / len(image_paths)

clips = []
for img in image_paths:
    clip = ImageClip(img).set_duration(duration_per_image)
    clips.append(clip)

video = concatenate_videoclips(clips, method="compose")
video = video.set_audio(audio)

final_video_path = f"{output_dir}/final_video.mp4"
video.write_videofile(final_video_path, fps=24)

# Upload to YouTube
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {"title": title, "description": description, "categoryId": "22"},
        "status": {"privacyStatus": "public"}
    },
    media_body=MediaFileUpload(final_video_path)
)
request.execute()

print("Video Generated & Uploaded Successfully!")
