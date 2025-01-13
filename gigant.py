from flask import Flask, request, jsonify
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import soundfile as sf
import io
import librosa
import tempfile
import os

app = Flask(__name__)

# Initialize the model and processor globally
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    "gigant/whisper-medium-romanian",
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained("gigant/whisper-medium-romanian")

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=128,
    chunk_length_s=30,
    batch_size=16,
    torch_dtype=torch_dtype,
    device=device,
)

def process_audio(audio_data, sample_rate):
    """Process audio data and return transcription."""
    # Ensure audio is in the correct format (16kHz, mono)
    if sample_rate != 16000:
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
    
    try:
        result = pipe(audio_data)
        return result["text"]
    except Exception as e:
        return str(e)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            file.save(temp_file.name)
            
            # Load the audio file
            audio_data, sample_rate = librosa.load(temp_file.name, sr=None)
            
        # Remove temporary file
        os.unlink(temp_file.name)
        
        # Process the audio
        transcription = process_audio(audio_data, sample_rate)
        
        return jsonify({
            'transcription': transcription,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model': 'gigant/whisper-medium-romanian',
        'device': str(device)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)