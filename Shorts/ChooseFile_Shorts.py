from flask import Flask, request, render_template, redirect, url_for
from flask import jsonify
import os
import logging
import YouTube_Shorts

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/input')
def list_files():
    files = os.listdir('input')
    return render_template('ChooseFile_Shorts.html', files=files)

@app.route('/create_video', methods=['POST'])
def create_video():
    try:
        try:
            num_videos = int(request.form.get('num_videos', 0))
        except ValueError:
            num_videos = 0
        
        creatable_videos = YouTube_Shorts.count_creatable_video()
        created_count = YouTube_Shorts.create_video(num_videos=num_videos)
        
        if created_count < num_videos:
            return jsonify(message=f'The maximum number of videos creatable is {creatable_videos}'), 400
        else:
            return jsonify(message="Video created successfully!"), 200
    except Exception as e:
        app.logger.error(f"Error in create_video: {e}")
        print(f"Error: {e}")
        return str(e), 500

@app.route('/some_route', methods=['POST'])
def some_route():
    try:
        return "Success"
    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        return str(e), 500

@app.errorhandler(400)
def bad_request_error(error):
    app.logger.error(f"Bad Request Error: {error}")
    return "Bad Request", 400

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal Server Error: {error}")
    return "Internal Server Error", 500

#Check this later
stream_handler = logging.StreamHandler()
app.logger.addHandler(stream_handler)
app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.run(debug=True)