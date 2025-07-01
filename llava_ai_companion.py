import torch
from transformers import LlavaForConditionalGeneration, LlavaProcessor
from PIL import Image
import requests
import mss
import time
import json
import pyttsx3
import re

# === CONFIG ===
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama2"  # Change to whatever you're using
DEVICE = "cpu"


# === SETUP MODELS ===
print("⏳ Loading LLaVA model...")
processor = LlavaProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
model = LlavaForConditionalGeneration.from_pretrained("llava-hf/llava-1.5-7b-hf").to(DEVICE)

engine = pyttsx3.init()

# === HELPERS ===
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def get_screen_image():
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

def caption_image(image):
    image = image.convert("RGB")  # Make sure image is in RGB mode
    prompt = "Describe this image."
    
    # 👇 NEW: Pass image first to avoid deprecation warning
    inputs = processor(images=image, text=prompt, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=100)
    
    raw_caption = processor.tokenizer.decode(output[0], skip_special_tokens=True).strip()
    
    # Optional: clean caption
    cleaned = raw_caption.lower()
    for phrase in ["a photo of ", "a picture of ", "an image of "]:
        if cleaned.startswith(phrase):
            cleaned = cleaned.replace(phrase, "", 1)
    return cleaned[0].upper() + cleaned[1:]


def get_ollama_response(caption):
    prompt = f"You're an AI companion. React to this description: \"{caption}\" with a short, natural-sounding comment or joke."

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt},
            stream=True
        )
        parts = []
        for line in response.iter_lines():
            if line:
                try:
                    json_line = line.decode("utf-8")
                    part = json.loads(json_line).get("response", "")
                    parts.append(part)
                except json.JSONDecodeError:
                    continue
        return remove_emojis("".join(parts).strip())
    except Exception as e:
        return f"[Error getting Ollama response]: {e}"

def speak(text):
    engine.say(text)
    engine.runAndWait()

# === MAIN LOOP ===
if __name__ == "__main__":
    print("✅ Ready. Starting AI Companion Loop.")
    while True:
        try:
            image = get_screen_image()
            caption = caption_image(image)
            print(f"[CAPTION]: {caption}")
            response = get_ollama_response(caption)
            print(f"[OLLAMA]: {response}")
            speak(response)
        except Exception as e:
            print(f"[ERROR]: {e}")
        time.sleep(10)
