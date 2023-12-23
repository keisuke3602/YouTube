from flask import Flask, request, render_template, redirect, url_for
import os
import YouTube

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/input')
def list_files():
    files = os.listdir('input')
    return render_template('ChooseFile.html', files=files)

@app.route('/create_video', methods=['POST'])
def create_video():
    selected_file = request.form['selected_file']
    selected_rows = int(request.form.get('selected_rows', 0)) + 1
    YouTube.create_video(selected_file, selected_rows)
    return ('', 204)

if __name__ == "__main__":
    app.run(debug=True)