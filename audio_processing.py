#!/usr/bin/env python3
import os
import random
import numpy as np
from pydub import AudioSegment
import librosa
import soundfile as sf

def extract_random_segment(input_file, output_file, duration=10.0):
    """
    Extract a random segment of specified duration from an audio file
    
    Args:
        input_file (str): Path to input audio file
        output_file (str): Path to output segment file
        duration (float): Duration of segment in seconds
    """
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
        
        # Calculate total duration in milliseconds
        total_duration_ms = len(audio)
        segment_duration_ms = int(duration * 1000)
        
        # Make sure we can extract a full segment
        if total_duration_ms <= segment_duration_ms:
            print(f"Warning: Audio is shorter than {duration}s. Using whole file.")
            segment = audio
        else:
            # Choose a random start position
            max_start_pos = total_duration_ms - segment_duration_ms
            start_pos = random.randint(0, max_start_pos)
            
            # Extract the segment
            segment = audio[start_pos:start_pos + segment_duration_ms]
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Export the segment
        segment.export(output_file, format="wav")
        
        return output_file
        
    except Exception as e:
        print(f"Error extracting segment: {e}")
        return None

def add_noise(input_file, output_file, noise_level=0.1):
    """
    Add white noise to an audio file
    
    Args:
        input_file (str): Path to input audio file
        output_file (str): Path to output noisy audio file
        noise_level (float): Noise level (0.0-1.0)
    """
    try:
        # Load audio file using librosa
        y, sr = librosa.load(input_file, sr=None)
        
        # Generate white noise with the same shape as the signal
        noise = np.random.normal(0, y.std() * noise_level, y.shape)
        
        # Add noise to the signal
        y_noisy = y + noise
        
        # Ensure the output stays in the [-1, 1] range
        y_noisy = np.clip(y_noisy, -1.0, 1.0)
        
        # Write the noisy audio to file
        sf.write(output_file, y_noisy, sr)
        
        return output_file
        
    except Exception as e:
        print(f"Error adding noise: {e}")
        return None

def convert_to_mono_wav(input_file, output_file=None):
    """
    Convert any audio file to mono WAV format at 44100Hz
    
    Args:
        input_file (str): Path to input audio file
        output_file (str, optional): Path to output WAV file. If None, uses input name with .wav extension
        
    Returns:
        str: Path to the converted file
    """
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".wav"
        
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
        
        # Convert to mono
        audio = audio.set_channels(1)
        
        # Convert to 44100Hz
        audio = audio.set_frame_rate(44100)
        
        # Export as WAV
        audio.export(output_file, format="wav")
        
        return output_file
        
    except Exception as e:
        print(f"Error converting audio: {e}")
        return None 