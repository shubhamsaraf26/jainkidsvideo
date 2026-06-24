from openai import OpenAI
from datetime import datetime
from pathlib import Path
import os

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

prompt = """
Generate a completely new Jain kids story.

Format exactly:

TITLE: ...

DESCRIPTION:
...

SCRIPT:
Hindi narration suitable for children and 60-second video.

SCENES:
10 detailed colorful 3D cartoon scene prompts.

Story must:
- Be Jain religion based
- Teach Ahimsa, Compassion, Truth, Forgiveness, Aparigraha or Self Discipline
- Be unique every day
- Hindi language
"""

response = client.responses.create(
    model="gpt-5",
    input=prompt
)

story = response.output_text

today = datetime.now().strftime("%Y-%m-%d")

Path("stories").mkdir(exist_ok=True)

filename = f"stories/{today}-jain-story.txt"

with open(filename, "w", encoding="utf-8") as f:
    f.write(story)

print(f"Created {filename}")