import cv2
import numpy as np
import tkinter as tk
import threading
import mediapipe as mp
import pyttsx3
import speech_recognition as sr
from difflib import SequenceMatcher
import time

engine = pyttsx3.init()

# Paths
REFERENCE_IMG_PATH = "C:/Users/yerra/OneDrive/Pictures/Camera Roll/WIN_20250626_09_10_39_Pro.jpg"
REFERENCE_AUDIO_PATH = "C:/Users/yerra/Downloads/WhatsApp Ptt 2025-06-25 at 11.25.33 PM.wav"

# ========== Core Functions ==========

def speak(text):
    engine.say(text)
    engine.runAndWait()

def type_text(box, text):
    box.config(state=tk.NORMAL)
    box.insert(tk.END, "[JARVIS]: " + text + "\n")
    box.see(tk.END)
    box.update()
    box.config(state=tk.DISABLED)
    speak(text)

def record_and_transcribe(duration=5, out="temp_voice.wav"):
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source, phrase_time_limit=duration)
        with open(out, "wb") as f:
            f.write(audio.get_wav_data())
    with sr.AudioFile(out) as source:
        audio_data = r.record(source)
    try:
        return r.recognize_google(audio_data)
    except:
        return ""

def transcribe_audio(file):
    r = sr.Recognizer()
    with sr.AudioFile(file) as source:
        audio_data = r.record(source)
    try:
        return r.recognize_google(audio_data)
    except:
        return ""

def normalize_text(text):
    return ''.join(c.lower() for c in text if c.isalnum() or c.isspace()).strip()

def match_strings(a, b):
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    return SequenceMatcher(None, a_norm, b_norm).ratio()

def voice_verification(box):
    type_text(box, "Please say your passphrase.")
    user = record_and_transcribe()
    ref = transcribe_audio(REFERENCE_AUDIO_PATH)
    score = match_strings(user, ref)
    if score > 0.4:  # lowered threshold
        type_text(box, "Voice verified.")
        return True
    else:
        type_text(box, "Voice not verified.")
        return False

def extract_face_bbox(image):
    mp_face = mp.solutions.face_detection
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.6) as detector:
        results = detector.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if results.detections:
            return results.detections[0].location_data.relative_bounding_box
        else:
            return None

def face_verification(box):
    type_text(box, "Starting face scan.")
    cap = cv2.VideoCapture(0)
    time.sleep(2)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        type_text(box, "Camera error.")
        return False

    ref_img = cv2.imread(REFERENCE_IMG_PATH)
    if ref_img is None:
        type_text(box, "Reference image not found.")
        return False

    ref_box = extract_face_bbox(ref_img)
    cam_box = extract_face_bbox(frame)

    if ref_box is None or cam_box is None:
        type_text(box, "Face not detected.")
        return False

    ref = np.array([ref_box.xmin, ref_box.ymin, ref_box.width, ref_box.height])
    cam = np.array([cam_box.xmin, cam_box.ymin, cam_box.width, cam_box.height])
    diff = np.linalg.norm(ref - cam)

    if diff < 0.2:
        type_text(box, "Face verified.")
        return True
    else:
        type_text(box, "Face not verified.")
        return False

# ========== Terminal-Style UI ==========

class TerminalApp:
    def __init__(self, root):
        self.root = root
        root.title("JARVIS TERMINAL")
        root.geometry("600x400")
        root.configure(bg="black")

        self.text = tk.Text(root, bg="black", fg="lime", font=("Courier", 12))
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.insert(tk.END, "[JARVIS]: Welcome to the JARVIS Security System.\n")
        self.text.insert(tk.END, "[JARVIS]: Press 1 for Face Scan\n")
        self.text.insert(tk.END, "[JARVIS]: Press 2 for Voice Verification\n")
        self.text.insert(tk.END, "[JARVIS]: Press 3 for Full Verification\n")
        self.text.insert(tk.END, "[JARVIS]: Press Q to Quit\n")
        self.text.config(state=tk.DISABLED)

        root.bind("<Key>", self.key_pressed)

    def key_pressed(self, event):
        key = event.char.lower()
        if key == '1':
            threading.Thread(target=self.run_face, daemon=True).start()
        elif key == '2':
            threading.Thread(target=self.run_voice, daemon=True).start()
        elif key == '3':
            threading.Thread(target=self.run_full, daemon=True).start()
        elif key == 'q':
            self.root.destroy()

    def run_face(self):
        face_verification(self.text)

    def run_voice(self):
        voice_verification(self.text)

    def run_full(self):
        type_text(self.text, "Running full scan...")
        face_ok = face_verification(self.text)
        voice_ok = voice_verification(self.text)
        if face_ok and voice_ok:
            type_text(self.text, "Access granted.")
        else:
            type_text(self.text, "Access denied.")

# ========== Launch App ==========

# ========== Launch App ==========

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-fullscreen', True)  # Full screen mode
    root.configure(bg="black")
    app = TerminalApp(root)
    root.mainloop()

