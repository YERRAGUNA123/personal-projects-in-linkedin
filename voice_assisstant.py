import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import platform
import subprocess
import speech_recognition as sr
import threading

COMMANDS_FILE = "commands.json"

# ----------- Voice + File Opening Logic -------------
def open_path(path):
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open: {e}")

def recognize_and_execute():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text="🎙️ Listening...")
        audio = r.listen(source)
    try:
        command = r.recognize_google(audio).lower()
        status_label.config(text=f"🔊 Heard: {command}")

        if command in command_map:
            path = command_map[command]
            status_label.config(text=f"📂 Opening: {path}")
            open_path(path)
        else:
            status_label.config(text="❌ Command not found.")

    except sr.UnknownValueError:
        status_label.config(text="😕 Didn't catch that.")
    except sr.RequestError:
        status_label.config(text="⚠️ Speech service error.")

def run_voice_command():
    threading.Thread(target=recognize_and_execute).start()

# ----------- GUI + Command Storage -------------
def load_commands():
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_commands():
    with open(COMMANDS_FILE, "w") as f:
        json.dump(command_map, f, indent=2)

def add_command():
    key = entry_command.get().strip().lower()
    path = entry_path.get().strip()

    if not key or not path:
        messagebox.showwarning("Input Missing", "Please enter both command and path.")
        return

    command_map[key] = path
    listbox.insert(tk.END, f"{key} → {path}")
    save_commands()
    entry_command.delete(0, tk.END)
    entry_path.delete(0, tk.END)

def choose_file_or_folder():
    path = filedialog.askopenfilename()
    if not path:
        path = filedialog.askdirectory()
    if path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, path)

# ----------- UI Setup -------------
app = tk.Tk()
app.title("🎤 Voice Assistant UI")
app.geometry("500x500")

command_map = load_commands()

# Command Entry
tk.Label(app, text="Voice Command:").pack()
entry_command = tk.Entry(app, width=40)
entry_command.pack(pady=5)

tk.Label(app, text="File or Folder Path:").pack()
entry_path = tk.Entry(app, width=40)
entry_path.pack(pady=5)

tk.Button(app, text="Browse", command=choose_file_or_folder).pack(pady=2)
tk.Button(app, text="➕ Add Command", command=add_command).pack(pady=10)

# List of Commands
tk.Label(app, text="📝 Saved Commands:").pack()
listbox = tk.Listbox(app, width=60)
listbox.pack(pady=5)
for cmd, path in command_map.items():
    listbox.insert(tk.END, f"{cmd} → {path}")

# Voice Button
tk.Button(app, text="🎙️ Speak Command", command=run_voice_command, bg="green", fg="white").pack(pady=20)
status_label = tk.Label(app, text="Status: Waiting for command...")
status_label.pack(pady=10)

app.mainloop()
