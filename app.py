#!/usr/bin/env python3
import argparse
import whisper
import time
import os
import sys
from pathlib import Path

def print_header():
    """Print a friendly header"""
    print("\n🎵 Whisper Audio Transcription Tool 🎵")
    print("=" * 40)

def get_file_size(filepath):
    """Get human-readable file size"""
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def prompt_for_model():
    """Interactive model selection"""
    print("\n📋 Available Models:")
    print("1. medium - Good balance of speed and accuracy")
    print("2. large  - Higher accuracy, slower processing")
    
    while True:
        choice = input("\nChoose model (1-2) or press Enter for medium: ").strip()
        if choice == "" or choice == "1":
            return "medium"
        elif choice == "2":
            return "large"
        else:
            print("Please enter 1, 2, or press Enter for default")

def prompt_for_audio_file():
    """Interactive file selection with validation"""
    audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma', '.mp4', '.mov', '.avi'}
    
    while True:
        file_path = input("\nEnter path to audio file: ").strip()
        
        # Remove quotes if present
        file_path = file_path.strip('"\'')
        
        if not file_path:
            print("Please enter a file path")
            continue
            
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in audio_extensions:
            print(f"Unsupported file type: {file_ext}")
            print(f"Supported formats: {', '.join(sorted(audio_extensions))}")
            continue
            
        return file_path

def show_file_info(file_path):
    """Display file information"""
    file_size = get_file_size(file_path)
    file_name = os.path.basename(file_path)
    print(f"\n📁 File: {file_name}")
    print(f"📊 Size: {file_size}")

def transcribe_with_progress(audio_path, model_size):
    """Transcribe with user-friendly progress updates"""
    print(f"\n🔄 Loading {model_size} model...")
    
    start_time = time.time()
    
    try:
        model = whisper.load_model(model_size)
        load_time = time.time() - start_time
        print(f"✅ Model loaded in {load_time:.1f} seconds")
        
        print("🎯 Starting transcription...")
        transcribe_start = time.time()
        
        result = model.transcribe(audio_path)
        transcript = result["text"]
        
        transcribe_time = time.time() - transcribe_start
        total_time = time.time() - start_time
        
        return transcript, total_time, transcribe_time
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None, 0, 0

def save_transcript(transcript, audio_path, custom_output=None):
    """Save transcript with user-friendly output"""
    if custom_output:
        output_file = custom_output
    else:
        base_name = Path(audio_path).stem
        output_file = f"{base_name}_transcript.txt"
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        print(f"💾 Transcript saved: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error saving file: {str(e)}")
        return None

def interactive_mode():
    """Run in interactive mode"""
    print_header()
    
    # Get audio file
    audio_path = prompt_for_audio_file()
    show_file_info(audio_path)
    
    # Get model choice
    model_size = prompt_for_model()
    
    # Ask about output file
    custom_output = input("\nCustom output filename (or press Enter for auto): ").strip()
    if not custom_output:
        custom_output = None
    
    # Perform transcription
    transcript, total_time, transcribe_time = transcribe_with_progress(audio_path, model_size)
    
    if transcript is None:
        return 1
    
    # Save transcript
    output_file = save_transcript(transcript, audio_path, custom_output)
    if output_file is None:
        return 1
    
    # Show results
    print(f"\n🎉 Transcription Complete!")
    print(f"⏱️  Total time: {total_time:.1f} seconds")
    print(f"📝 Transcript length: {len(transcript)} characters")
    
    # Ask if user wants to see transcript
    show_transcript = input("\nShow transcript? (y/N): ").strip().lower()
    if show_transcript in ['y', 'yes']:
        print("\n📄 Transcript:")
        print("-" * 50)
        print(transcript)
        print("-" * 50)
    
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="🎵 User-friendly audio transcription using Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python whisper_cli.py                              # Interactive mode
  python whisper_cli.py audio.wav                    # Quick transcription
  python whisper_cli.py audio.mp3 --model large     # Use large model
  python whisper_cli.py audio.wav --output my.txt   # Custom output
        """
    )
    
    parser.add_argument(
        "audio_file",
        nargs='?',
        help="Path to audio file (optional - will prompt if not provided)"
    )
    
    parser.add_argument(
        "--model", "-m",
        choices=["medium", "large"],
        help="Whisper model size (will prompt if not provided)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path for transcript"
    )
    
    parser.add_argument(
        "--show", "-s",
        action="store_true",
        help="Show transcript in terminal after completion"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output mode"
    )
    
    args = parser.parse_args()
    
    # If no audio file provided, run interactive mode
    if not args.audio_file:
        return interactive_mode()
    
    # Validate audio file
    if not os.path.exists(args.audio_file):
        print(f"❌ Error: Audio file '{args.audio_file}' not found")
        return 1
    
    # Use provided or prompt for model
    model_size = args.model
    if not model_size and not args.quiet:
        model_size = prompt_for_model()
    else:
        model_size = model_size or "medium"
    
    if not args.quiet:
        print_header()
        show_file_info(args.audio_file)
    
    # Perform transcription
    if args.quiet:
        print("Processing...")
        start_time = time.time()
        model = whisper.load_model(model_size)
        result = model.transcribe(args.audio_file)
        transcript = result["text"]
        total_time = time.time() - start_time
        transcribe_time = total_time
    else:
        transcript, total_time, transcribe_time = transcribe_with_progress(args.audio_file, model_size)
    
    if transcript is None:
        return 1
    
    # Save transcript
    output_file = save_transcript(transcript, args.audio_file, args.output)
    if output_file is None:
        return 1
    
    # Show results
    if not args.quiet:
        print(f"\n🎉 Transcription Complete!")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📝 Transcript length: {len(transcript)} characters")
    
    # Show transcript if requested
    if args.show:
        print("\n📄 Transcript:")
        print("-" * 50)
        print(transcript)
        print("-" * 50)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)