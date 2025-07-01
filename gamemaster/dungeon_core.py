# dungeon_core.py
import ollama
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image
import os

# Load Stable Diffusion model once
model_id = "CompVis/stable-diffusion-v1-4"
pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)
pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

def get_story_and_options(history: str):
    prompt = f"""
You are a Dungeon Master AI. Continue the story and provide 3 choices.

Story so far:
{history}

Continue and give 3 options.
"""
    response = ollama.chat(model="mistral", messages=[
        {"role": "user", "content": prompt}
    ])
    text = response["message"]["content"]
    
    story_lines, choices = [], []
    for line in text.strip().split("\n"):
        if line.strip().startswith(tuple("123456789")):
            choices.append(line.strip())
        else:
            story_lines.append(line.strip())
    
    story = " ".join(story_lines).strip()
    return story, choices[:3]

def generate_image(prompt: str, filename="scene.png") -> str:
    image: Image.Image = pipe(prompt).images[0]
    os.makedirs("generated", exist_ok=True)
    filepath = os.path.join("generated", filename)
    image.save(filepath)
    return filepath
