import gradio as gr
import whisper
import time
import os

def transcribe(audio, not_robot, model_size):
    if not_robot == False:
        transcript = "ERROR: please pass pseudoCaptcha"
        txt_filename = "captcha_error.txt"
        with open(txt_filename, "w") as f:
            f.write(transcript)
        elapsed_time = f"Elapsed time:0.01 seconds"
        return transcript, txt_filename, elapsed_time
        return "please check pseudoCaptcha!", "", "0.00 seconds"
    start_time = time.time()
    model = whisper.load_model(model_size)
    result = model.transcribe(audio)
    transcript = result["text"]
    
    # Save transcript to a file
    txt_filename = "transcript.txt"
    with open(txt_filename, "w") as f:
        f.write(transcript)
    
    elapsed_time = time.time() - start_time
    return transcript, txt_filename, f"Elapsed Time: {elapsed_time:.2f} seconds"

gui = gr.Interface(
    fn=transcribe,
    inputs=[gr.Audio(type="filepath"), gr.Checkbox(label="I am not a psychiatrist"), gr.Dropdown(["medium", "large"], label="Model Size")],
    outputs=[gr.Textbox(label="Transcript"), gr.File(label="Download TXT"), gr.Textbox(label="Elapsed Time")],
    title="Whisper Transcription",
    description="Upload an audio file and choose a model size to transcribe it."
)

gui.launch()