import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import moviepy.editor as mp
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import re
import pyttsx3
import wave
import contextlib

# Add FFmpeg path to environment variables
os.environ["PATH"] += os.pathsep + r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"

def create_text_clip(text, size, font_size=48, font_color="white", bg_color=None):
    img = Image.new('RGBA', size, (0, 0, 0, 0))  # Transparent background
    draw = ImageDraw.Draw(img)
    
    # Ensure Nunito font is installed and accessible
    font_path = "Nunito-Bold.ttf"  # Update this path
    font = ImageFont.truetype(font_path, font_size)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size[0]-text_width)/2, (size[1]-text_height)/2)  # Center of the screen
    
    # Optional: Add a semi-transparent background for better readability
    if bg_color:
        bg_bbox = (position[0]-10, position[1]-10, position[0]+text_width+10, position[1]+text_height+10)
        draw.rectangle(bg_bbox, fill=(0, 0, 0, 128))  # Semi-transparent black
    
    draw.text(position, text, font=font, fill=font_color)
    
    # Convert RGBA to RGB
    rgb_img = Image.new('RGB', size, (0, 0, 0))  # Black background
    rgb_img.paste(img, mask=img.split()[3])  # 3 is the alpha channel
    
    return np.array(rgb_img)

def split_text_to_words(text):
    return re.findall(r'\S+', text)

def get_audio_duration(audio_path):
    with contextlib.closing(wave.open(audio_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration

def get_word_timings(audio_path, words):
    total_duration = get_audio_duration(audio_path)
    avg_duration = total_duration / len(words)
    
    word_timings = []
    current_time = 0
    for word in words:
        word_timings.append((word, current_time, current_time + avg_duration))
        current_time += avg_duration
    
    return word_timings

def get_available_voices():
    engine = pyttsx3.init()
    return engine.getProperty('voices')

def generate_speech(text, voice_id, output_path):
    engine = pyttsx3.init()
    engine.setProperty('voice', voice_id)
    engine.save_to_file(text, output_path)
    engine.runAndWait()

def process_video():
    video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4")])
    if not video_path:
        return

    text = text_input.get("1.0", tk.END).strip()
    if not text:
        result_label.config(text="Please enter some text for subtitles and dubbing.")
        return

    words = split_text_to_words(text)
    if not words:
        result_label.config(text="No valid words found in the input text.")
        return

    # Generate AI dubbing with selected voice
    voice_id = voice_combobox.get()
    generate_speech(text, voice_id, "temp_audio.wav")

    # Get timings for each word
    word_timings = get_word_timings("temp_audio.wav", words)

    # Load video
    video = mp.VideoFileClip(video_path)
    
    # Create subtitle function
    def make_subtitle(t):
        current_words = [word for word, start, end in word_timings if start <= t < end]
        subtitle_text = " ".join(current_words)
        return create_text_clip(subtitle_text, (video.w, video.h))

    # Create subtitle clip
    subtitle = mp.VideoClip(make_subtitle, duration=video.duration)
    subtitle = subtitle.set_position('center')  # Center of the screen

    # Load AI dubbing audio
    dubbing_audio = mp.AudioFileClip("temp_audio.wav")

    # Combine video, subtitles, and dubbing
    final_audio = mp.CompositeAudioClip([video.audio, dubbing_audio])
    final_video = mp.CompositeVideoClip([video, subtitle])
    final_video = final_video.set_audio(final_audio)

    # Write output video
    output_path = os.path.splitext(video_path)[0] + "_with_subtitles_and_dubbing.mp4"
    final_video.write_videofile(output_path)

    # Clean up temporary files
    os.remove("temp_audio.wav")

    result_label.config(text=f"Video processed successfully!\nSaved as: {output_path}")

# Create GUI
root = tk.Tk()
root.title("Video Subtitle and Dubbing Generator")

text_input_label = tk.Label(root, text="Enter text for subtitles and dubbing:")
text_input_label.pack(pady=5)

text_input = scrolledtext.ScrolledText(root, width=50, height=10)
text_input.pack(pady=5)

voice_label = tk.Label(root, text="Select voice:")
voice_label.pack(pady=5)

voices = get_available_voices()
voice_combobox = ttk.Combobox(root, values=[voice.name for voice in voices])
voice_combobox.set(voices[0].name)  # Set default voice
voice_combobox.pack(pady=5)

process_button = tk.Button(root, text="Process Video", command=process_video)
process_button.pack(pady=10)

result_label = tk.Label(root, text="")
result_label.pack(pady=5)

root.mainloop()
