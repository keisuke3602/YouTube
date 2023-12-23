"""
pip install moviepy
pip install ffmpeg-python
pip install Pillow==8.2.0
"""
import glob
import gspread
import datetime
import textwrap
import numpy as np
from moviepy.config import change_settings
from moviepy.editor import *
from moviepy.editor import AudioFileClip
from moviepy.editor import ImageClip
from pydub import AudioSegment
from google.cloud import texttospeech
from oauth2client.service_account import ServiceAccountCredentials
change_settings({"IMAGEMAGICK_BINARY": "/usr/local/bin/convert"})

def add_silence_to_audio(audio_file_path, silence_duration_before = 600, silence_duration_after = 700):
    audio = AudioSegment.from_file(audio_file_path, format="mp3")
    silence_before = AudioSegment.silent(duration=silence_duration_before)
    silence_after = AudioSegment.silent(duration=silence_duration_after)
    final_audio = silence_before + audio + silence_after
    final_audio.export(audio_file_path, format="mp3")

def create_video(selected_file, selected_rows):
        scope = ["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/keisukewatanabe/', scope)
        client = gspread.authorize(creds)
        sheet = client.open("YouTube_Long_Format").sheet1
        selected_rows = int(selected_rows)
        texts = sheet.col_values(1)[:selected_rows]
        if selected_rows > len(texts):
            print("Error: The number of quotes entered exceeds the number of quotes on the Spreadsheet.")
            return


        bgm = AudioFileClip('/Users/keisukewatanabe/Desktop/moviepy/music/')
        clips = []
        audio_clips = []
        start_time = 0

        key_path = "/Users/keisukewatanabe/Desktop/Shorts/"
        client = texttospeech.TextToSpeechClient.from_service_account_json(key_path)
        
        file_list = glob.glob('input/' + selected_file)
        if file_list:
            temp_clip = ImageClip(file_list[0])
            temp_clip = temp_clip.resize(height=1080)
            img_width = temp_clip.size[0]
            print("Img_width: " + str(img_width))

        for i, text in enumerate(texts):
            if len(text) > 300:
                continue

            num_chars = len(text.replace('\n', ''))
            if 150 <= num_chars:
                fontsize = 36
            elif 75 < num_chars < 150:
                fontsize = 46
            else:
                fontsize = 56

            wrap_length = 28 if fontsize == 36 else 24
            text = textwrap.fill(text, wrap_length)

            temp_txt_clip = TextClip(text, fontsize=fontsize, color='white')
            txt_width = temp_txt_clip.size[0]
            print("txt_width: " + str(txt_width))

            half_txt_space = (1920 - img_width) / 2
            print("half_txt_space: " + str(half_txt_space))

            position_x = img_width + half_txt_space - (txt_width / 2)
            print("Position X: " + str(position_x))
            position_y = ("center")

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )

            audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            sample_rate_hertz=44100
            )

            response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            speech_file = f"speech_{i}.mp3"
            with open(speech_file, "wb") as out:
                out.write(response.audio_content)

            add_silence_to_audio(speech_file)

            audio = AudioFileClip(speech_file, fps=44100).set_start(start_time)
            print(f"Generated audio clip with duration {audio.duration} and fps {audio.fps}")
            audio_clips.append(audio)

            os.remove(speech_file)

            duration = audio.duration

            txt_clip = TextClip(text, fontsize = fontsize, color='white')
            txt_clip = txt_clip.set_duration(duration).set_start(start_time)
            txt_clip = txt_clip.set_position((position_x, position_y))
            clips.append(txt_clip)
            
            start_time += duration

        total_duration = start_time

        loops_required = max(1, int(np.ceil(total_duration / bgm.duration)))
        bgm = concatenate_audioclips([bgm] * loops_required)
        bgm = bgm.subclip(0, total_duration)

        for m in file_list:
            clip = ImageClip(m).set_duration(total_duration)
            clip = clip.resize(height=1080)
            clip = clip.set_position("left")
            clips.insert(0, clip)

        final_audio = concatenate_audioclips(audio_clips)

        final_audio_bgm = CompositeAudioClip([final_audio, bgm.volumex(0.3)])
        concat_clip = CompositeVideoClip(clips, size=(1920,1080))

        if audio.duration > concat_clip.duration:
            audio = audio.subclip(0, concat_clip.duration)

        concat_clip = concat_clip.set_audio(final_audio_bgm)
        output_directory = "output"
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        selected_file_sanitized = selected_file.replace(" ", "_")
        output_filename = os.path.join(output_directory,f"{selected_file_sanitized}_{current_time}.mp4")
        concat_clip.write_videofile(output_filename, fps=24, codec='libx264', audio_codec='aac', audio_bitrate="320k") #,write_logfile=True)

if __name__ == '__main__':
    app.run(debug=True)
