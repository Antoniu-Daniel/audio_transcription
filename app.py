# app.py

from flask import Flask, render_template, request, jsonify
from transformers import pipeline

app = Flask(__name__)

# Load the speech recognition pipeline
asr = pipeline("automatic-speech-recognition", model="gigant/romanian-wav2vec2") 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        audio_file = request.files['audio_file']
        # Process the uploaded audio file (e.g., using librosa)
        # ... (Audio processing logic here) ...
        transcription = asr(audio_data)  # Assuming audio_data is prepared correctly
        return jsonify({'transcription': transcription['text']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
