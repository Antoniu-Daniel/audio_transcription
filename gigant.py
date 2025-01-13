from flask import Flask, request, jsonify, render_template
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Load the model and processor
processor = WhisperProcessor.from_pretrained("gigant/whisper-medium-romanian")
model = WhisperForConditionalGeneration.from_pretrained("gigant/whisper-medium-romanian")

# Configure upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def index():
    return render_template("gigant.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files["audio"]
    filename = secure_filename(audio_file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    audio_file.save(filepath)

    try:
        # Process and transcribe audio
        input_features = processor(filepath, return_tensors="pt", sampling_rate=16000).input_features
        predicted_ids = model.generate(input_features)
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

        return jsonify({"transcription": transcription})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(filepath)  # Cleanup uploaded file after processing

if __name__ == "__main__":
    app.run(debug=True)