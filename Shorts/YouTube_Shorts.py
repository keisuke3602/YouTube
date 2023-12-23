import glob
import gspread
import datetime
import textwrap
import pandas as pd
import logging
import os
from moviepy.editor import *
from moviepy.config import change_settings
from moviepy.editor import AudioFileClip
from moviepy.editor import ImageClip
from pydub import AudioSegment
from google.cloud import texttospeech
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image

logger = logging.getLogger('YouTube_Shorts')

change_settings({"IMAGEMAGICK_BINARY": "/usr/local/bin/convert"})

def add_silence_to_audio(audio_file_path, silence_duration_before = 600, silence_duration_after = 700):
    audio = AudioSegment.from_file(audio_file_path, format="mp3")
    silence_before = AudioSegment.silent(duration=silence_duration_before)
    silence_after = AudioSegment.silent(duration=silence_duration_after)
    final_audio = silence_before + audio + silence_after
    final_audio.export(audio_file_path, format="mp3")

def get_data_as_dataframe(sheet):
    data = sheet.get_all_values()
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    return df

def count_creatable_video():
    scope = ["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/keisukewatanabe/Desktop/Shorts/keys/YouTube_text_to_speech_speedy-anthem-340212-e4195f19e826.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1e_3MvXLtcQz0QtT4vOjW-__uN6ReKDU9CVKvW76KjAE").worksheet("GCol")
    df = get_data_as_dataframe(sheet)
    count = 0
    for _, row in df.iterrows():
        if row['Status'] != 'Created' and row['Status'] != 'Skipped':
            count += 1
    return count

def convert_gray_to_rgb(img_path):
    with Image.open(img_path) as img:
        if img.mode == 'L':  
            rgb_img = img.convert('RGB')
            rgb_img.save(img_path)

def create_video(num_videos):
    logger.debug("Starting create_video function in YouTube_Shorts")
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/keisukewatanabe/Desktop/Shorts/keys/YouTube_text_to_speech_speedy-anthem-340212-e4195f19e826.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1e_3MvXLtcQz0QtT4vOjW-__uN6ReKDU9CVKvW76KjAE").worksheet("GCol")
        df = get_data_as_dataframe(sheet)
        #bgm = AudioFileClip('../Assets/music/Kevin_MacLeod_-_Canon_in_D_Major.mp3')
        creatable_videos = count_creatable_video()

        if num_videos > creatable_videos:
            message = f"The maximum number of videos creatable is {creatable_videos}."
            print(message)
            num_videos = creatable_videos

        index = 2
        created_count = 0

        for index, row in df.iterrows():
            index += 2
            status = row['Status']
            print(f"Row: {index}, Status: {status}")
            if status != 'Created':

                author_name = row['Author']
                author = "3 Quotes from " + author_name
                quote1 = row['Quote1']
                quote2 = row['Quote2']
                quote3 = row['Quote3']

                if not quote1 or not quote3:
                    print(f"Row: {index}, Quote1 or Quote3 is empty. Skipping this row.")
                    continue

                if len(quote1) > 280 or len(quote2) > 280 or len(quote3) > 280:
                    print(f"Row: {index}, Author: {author_name} has a quote longer than 300 characters. Skipping...")
                    df.at[index-2, 'Status'] = 'Skipped'
                    continue

                expected_filename = f"{author_name.replace(' ', '_')}.jpg"
                if expected_filename not in os.listdir('input'):
                    continue

                texts = [author, quote1, quote2, quote3]
                audio_clips = []
                clips = []
                start_time = 0

                key_path = "/Users/keisukewatanabe/Desktop/Shorts/keys/YouTube_text_to_speech_speedy-anthem-340212-e4195f19e826.json"
                client = texttospeech.TextToSpeechClient.from_service_account_json(key_path)

                for i, text in enumerate(texts):

                    num_chars = len(text.replace('\n', ''))
                    fontsize = 48 if num_chars > 100 else 58
                    position = ("center", 500) if fontsize == 58 else ("center", 400)
                    
                    wrap_length = 28 if fontsize == 36 else 24
                    text = textwrap.fill(text, wrap_length)

                    synthesis_input = texttospeech.SynthesisInput(text=text)
                    voice = texttospeech.VoiceSelectionParams(
                        language_code="en-US",
                        ssml_gender=texttospeech.SsmlVoiceGender.MALE
                    )

                    audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                    )

                    response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                    )

                    speech_file = f"speech_{i}.mp3"
                    with open(speech_file, "wb") as out:
                        out.write(response.audio_content)

                    add_silence_to_audio(speech_file)

                    audio = AudioFileClip(speech_file, fps=22050).set_start(start_time)
                    print(f"Generated audio clip with duration {audio.duration} and fps {audio.fps}")
                    audio_clips.append(audio)

                    os.remove(speech_file)

                    duration = audio.duration

                    txt_clip = TextClip(text, fontsize = fontsize, color='white')
                    txt_clip = txt_clip.set_duration(duration).set_start(start_time)
                    txt_clip = txt_clip.set_position(position)
                    clips.append(txt_clip)
                    
                    start_time += duration

                total_duration = start_time

                file_path = 'input/' + expected_filename
                convert_gray_to_rgb(file_path)

                file_list = glob.glob('input/' + expected_filename)
                for m in file_list:
                    clip = ImageClip(m).set_duration(total_duration).resize(width=1080)
                    clip = clip.set_position(("center", 1100))
                    clips.insert(0, clip)

                final_audio = concatenate_audioclips(audio_clips)

                concat_clip = CompositeVideoClip(clips, size=(1080,1920))

                concat_clip = concat_clip.set_audio(final_audio)
                current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{author_name}_{current_time}.mp4"
                concat_clip.write_videofile(output_filename, fps=24, codec='libx264', audio_codec='aac') #,write_logfile=True)
                
                df.at[index-2, 'Status'] = 'Created'
                df.at[index-2, 'File Name'] = output_filename
                created_count += 1
                if created_count >= num_videos:
                    break
            index += 1
        set_with_dataframe(sheet, df)
        return created_count
    except Exception:
        logger.exception("Error occurred in create_video function")

if __name__ == '__main__':
    app.run(debug=True)