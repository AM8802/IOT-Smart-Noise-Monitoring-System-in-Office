from os import system
import speech_recognition as sr
from gpt4all import GPT4All
import sys
import warnings
import time
import webbrowser
import random
import pandas as pd
from imageio_ffmpeg import get_ffmpeg_exe
import whisper
import customtkinter as ctk
import threading
import json
import websocket

# Load models
base_model = whisper.load_model("small")
print("Whisper model loaded successfully.")

warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")

whisper.audio.FFMPEG_PATH = "C:\\Users\\abdel\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\imageio_ffmpeg\\binaries\\ffmpeg-win64-v4.2.2.exe"

ffmpeg_path = get_ffmpeg_exe()
print(f"Using ffmpeg binary at: {ffmpeg_path}")

model = GPT4All(model_name="q4_0-orca-mini-3b.gguf", allow_download=True)
assistant_name = "andy"
listening_for_trigger_word = True
should_run = True
source = sr.Microphone()
recognizer = sr.Recognizer()

if sys.platform != 'darwin':
    import pyttsx3
    engine = pyttsx3.init()

# WebSocket for monitoring system
def connect_to_websocket():
    def on_message(ws, message):
        global monitoring_active, first_reading, waiting_for_command
        try:
            data = json.loads(message)
            noise_level = data.get("noise", 0)
            if monitoring_active and not waiting_for_command and noise_level > 90:
                respond(f"Alert! High noise level detected: {noise_level} dB.")
                announce_readings(data)
                ask_to_stop_or_resume()
            elif first_reading:
                announce_readings(data)
                first_reading = False
        except json.JSONDecodeError:
            print("Error decoding WebSocket message.")

    def on_error(ws, error):
        print(f"WebSocket error: {error}")

    def on_close(ws):
        print("WebSocket closed.")

    def on_open(ws):
        print("WebSocket connection established.")

    ws = websocket.WebSocketApp(
        "ws://localhost:8884",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    threading.Thread(target=ws.run_forever, daemon=True).start()

monitoring_active = True
first_reading = True
waiting_for_command = False
connect_to_websocket()

def respond(text):
    update_display(f"Micheal Scott: {text}")
    if sys.platform == 'darwin':
        ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,?!-_$:+-/ ")
        clean_text = ''.join(c for c in text if c in ALLOWED_CHARS)
        system(f"say '{clean_text}'")
    else:
        engine.say(text)
        engine.runAndWait()

def listen_for_command():
    update_display("Listening...")
    with source as s:
        recognizer.adjust_for_ambient_noise(s)
        audio = recognizer.listen(s)
    try:
        with open("command.wav", "wb") as f:
            f.write(audio.get_wav_data())
        command = base_model.transcribe("command.wav", fp16=False)
        if command and command['text']:
            update_display(f"You: {command['text']}")
            return command['text'].lower()
        return None
    except sr.UnknownValueError:
        respond("Could not understand audio. Please try again.")
        return None
    except sr.RequestError:
        respond("Unable to access the Google Speech Recognition API.")
        return None

def perform_command(command):
    global monitoring_active, should_run, waiting_for_command
    if command:
        if "stop sending alerts" in command:
            monitoring_active = False
            should_run = False
            waiting_for_command = False
            respond("Alerts have been disabled. Goodbye!")
            root.quit()
        elif "resume alerts" in command:
            monitoring_active = True
            waiting_for_command = False
            respond("Alerts have been enabled.")
        else:
            respond("Thinking...")
            output = model.generate(command, max_tokens=50)
            respond(output)
            waiting_for_command = False

def announce_readings(data):
    respond(
        f"Current readings: Noise: {data.get('noise', 'N/A')} dB, "
        f"Temperature: {data.get('temperature', 'N/A')} °C, "
        f"Humidity: {data.get('humidity', 'N/A')} %, "
        f"Light Intensity: {data.get('light', 'N/A')} lux."
    )

def ask_to_stop_or_resume():
    global waiting_for_command
    waiting_for_command = True
    respond("Would you like me to stop sending alerts or resume monitoring?")
    command = listen_for_command()
    if command:
        perform_command(command)

def update_display(response):
    text_output.configure(state="normal")
    text_output.insert(ctk.END, response + "\n")
    text_output.configure(state="disabled")

def initial_greeting():
    respond("Hello! I am here to monitor your office and assist you with any needs. Let me know if you'd like me to stop or resume alerts.")

def auto_listen():
    initial_greeting()
    while should_run:
        command = listen_for_command()
        if command:
            perform_command(command)

# Setting up customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Setup GUI
root = ctk.CTk()
root.geometry("500x600")
root.title("Micheal Scott")

root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=0)
root.rowconfigure(2, weight=1)
root.columnconfigure(0, weight=1)

frame = ctk.CTkFrame(root)
frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

frame.rowconfigure((0, 1, 2), weight=1)
frame.columnconfigure(0, weight=1)

ctk.CTkLabel(frame, text="Micheal Scott:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
text_output = ctk.CTkTextbox(frame, width=400, height=300)
text_output.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
text_output.configure(state="disabled")

threading.Thread(target=auto_listen, daemon=True).start()

root.mainloop()