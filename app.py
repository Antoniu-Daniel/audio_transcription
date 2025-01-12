import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the whisper.cpp executable
WHISPER_CPP_EXEC = "../../whisper.cpp/build/bin/whisper-cli"  # Update with the correct path if needed
MODEL_PATH = "../../whisper.cpp/models/ggml-medium.bin"  # Update with your model path

# Upload folder for audio files
UPLOAD_FOLDER = "/tmp/uploads"
CONVERTED_FOLDER = "/tmp/converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'flac'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_wav(input_path, output_path):
    """
    Convert audio file to 16kHz WAV format using FFmpeg
    """
    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-ar', '16000',
            '-ac', '1',
            '-c:a', 'pcm_s16le',
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {result.stderr}")
            raise Exception("FFmpeg conversion failed")
            
        logger.info(f"Successfully converted {input_path} to WAV")
        return True
        
    except Exception as e:
        logger.error(f"Error during audio conversion: {str(e)}")
        raise

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        # Check if executable and model exist
        if not os.path.isfile(WHISPER_CPP_EXEC):
            logger.error(f"Whisper executable not found at {WHISPER_CPP_EXEC}")
            return jsonify({"error": "Transcription service not properly configured"}), 500

        if not os.path.isfile(MODEL_PATH):
            logger.error(f"Model file not found at {MODEL_PATH}")
            return jsonify({"error": "Transcription model not found"}), 500

        # Check for FFmpeg installation
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return jsonify({"error": "FFmpeg not installed"}), 500

        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        # Secure the filename
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        wav_filename = os.path.splitext(filename)[0] + '.wav'
        output_path = os.path.join(CONVERTED_FOLDER, wav_filename)

        try:
            # Save the uploaded file
            file.save(input_path)
            os.chmod(input_path, 0o666)
            logger.info(f"Saved uploaded file: {input_path}")

            # Convert to WAV format
            convert_to_wav(input_path, output_path)
            logger.info(f"Converted to WAV: {output_path}")

            # Run whisper.cpp transcription
            logger.info("Starting transcription process")
            result = subprocess.run(
                [WHISPER_CPP_EXEC, "-m", MODEL_PATH, "--language", "ro", "--output-txt", "-f", output_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Check if transcription was successful
            if result.returncode != 0:
                logger.error(f"Transcription failed: {result.stderr}")
                return jsonify({"error": "Transcription failed: " + result.stderr.strip()}), 500

            # Extract transcription output
            transcription = result.stdout.strip()
            logger.info("Transcription completed successfully")
            return jsonify({"transcription": transcription})

        except subprocess.TimeoutExpired:
            logger.error("Transcription process timed out")
            return jsonify({"error": "Transcription process timed out"}), 500
        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error: {str(e)}")
            return jsonify({"error": "Failed to run transcription process"}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        # Clean up uploaded and converted files
        try:
            if 'input_path' in locals() and os.path.exists(input_path):
                os.remove(input_path)
                logger.info(f"Cleaned up input file: {input_path}")
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
                logger.info(f"Cleaned up converted file: {output_path}")
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

if __name__ == "__main__":
    # Ensure the upload and converted folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(CONVERTED_FOLDER, exist_ok=True)
    
    # Add SSL context if needed
    # app.run(debug=True, ssl_context='adhoc')  # Uncomment for HTTPS
    app.run(debug=True)
