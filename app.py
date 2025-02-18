# Install necessary dependencies
#!pip install gradio openai-whisper torch torchaudio

import gradio as gr
import whisper
import torch

# Load the Whisper model
model = whisper.load_model("large")

# Define the transcription function
def transcribe_audio(audio_file):
    # Load the audio file
    audio = whisper.load_audio(audio_file)
    # Transcribe the audio
    result = model.transcribe(audio)
    # Return the transcribed text
    return result["text"]

# Create the Gradio interface
interface = gr.Interface(
    fn=transcribe_audio,
    inputs=gr.Audio(type="filepath", label="Upload Audio File"),
    outputs=gr.Textbox(label="Transcribed Text"),
    title="Audio Transcription with OpenAI Whisper",
    description="Upload an audio file to transcribe it using OpenAI's Whisper model."
)

# Launch the Gradio app
interface.launch(share=True)