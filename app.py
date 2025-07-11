#!/usr/bin/env python3
import argparse
import whisper
import time
import os
import sys

def transcribe_audio(audio_path, model_size, output_file=None):
    """
    Transcribe audio file using Whisper model
    
    Args:
        audio_path (str): Path to the audio file
        model_size (str): Whisper model size ('medium' or 'large')
        output_file (str, optional): Output file path for transcript
    
    Returns:
        tuple: (transcript, elapsed_time)
    """
    # Check if audio file exists
    if not os.path.exists(audio_path):
        print(f"Error: Audio file '{audio_path}' not found.")
        sys.exit(1)
    
    print(f"Loading Whisper model: {model_size}")
    start_time = time.time()
    
    try:
        model = whisper.load_model(model_size)
        print(f"Transcribing audio file: {audio_path}")
        result = model.transcribe(audio_path)
        transcript = result["text"]
        
        elapsed_time = time.time() - start_time
        
        # Determine output filename
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            output_file = f"{base_name}_transcript.txt"
        
        # Save transcript to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        return transcript, elapsed_time, output_file
        
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using OpenAI's Whisper model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python whisper_cli.py audio.wav
  python whisper_cli.py audio.mp3 --model large
  python whisper_cli.py audio.wav --model medium --output my_transcript.txt
  python whisper_cli.py audio.wav --quiet
        """
    )
    
    parser.add_argument(
        "audio_file",
        help="Path to the audio file to transcribe"
    )
    
    parser.add_argument(
        "--model", "-m",
        choices=["medium", "large"],
        default="medium",
        help="Whisper model size to use (default: medium)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path for the transcript (default: <audio_filename>_transcript.txt)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output except for errors"
    )
    
    parser.add_argument(
        "--show-transcript",
        action="store_true",
        help="Display the transcript in the terminal"
    )
    
    args = parser.parse_args()
    
    # Perform transcription
    transcript, elapsed_time, output_file = transcribe_audio(
        args.audio_file, 
        args.model, 
        args.output
    )
    
    # Display results
    if not args.quiet:
        print(f"\nTranscription completed!")
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        print(f"Transcript saved to: {output_file}")
        
        if args.show_transcript:
            print(f"\nTranscript:")
            print("-" * 50)
            print(transcript)
            print("-" * 50)
        else:
            print(f"\nUse --show-transcript to display the transcript in terminal")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())