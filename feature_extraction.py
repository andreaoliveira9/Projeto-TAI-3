#!/usr/bin/env python3
import os
import subprocess
import tempfile
import numpy as np
import librosa
import json
from audio_processing import convert_to_mono_wav

# Path to GetMaxFreqs executable - update this based on your system
GETMAXFREQS_PATH = "./GetMaxFreqs"

def check_getmaxfreqs():
    """Check if GetMaxFreqs executable exists and is callable"""
    if not os.path.exists(GETMAXFREQS_PATH):
        print(f"WARNING: GetMaxFreqs executable not found at {GETMAXFREQS_PATH}")
        return False
    return True

def convert_to_frequencies_external(audio_file, output_file=None):
    """
    Convert audio file to frequency representation using external GetMaxFreqs tool
    
    Args:
        audio_file (str): Path to input audio file (should be mono WAV)
        output_file (str, optional): Path to output frequency file
        
    Returns:
        str: Path to the frequency file or None if failed
    """
    if not check_getmaxfreqs():
        print("Using internal frequency extraction instead.")
        return convert_to_frequencies_internal(audio_file, output_file)
        
    if output_file is None:
        output_file = os.path.splitext(audio_file)[0] + ".freq"
    
    # Ensure audio is in mono WAV format
    mono_wav = convert_to_mono_wav(audio_file)
    
    try:
        # Run GetMaxFreqs
        subprocess.run([GETMAXFREQS_PATH, mono_wav, output_file], check=True)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error calling GetMaxFreqs: {e}")
        return None

def convert_to_frequencies_internal(audio_file, output_file=None):
    """
    Convert audio file to frequency representation using internal implementation
    
    Args:
        audio_file (str): Path to input audio file
        output_file (str, optional): Path to output frequency file
        
    Returns:
        str: Path to the frequency file or None if failed
    """
    if output_file is None:
        output_file = os.path.splitext(audio_file)[0] + ".freq"
        
    try:
        # Load the audio file
        y, sr = librosa.load(audio_file, sr=None, mono=True)
        
        # Parameters for frequency extraction - increased for better resolution
        frame_length = 8192  # Increased for better frequency resolution
        hop_length = 256     # Small hop for more overlap
        num_freqs = 20       # More frequencies to capture more details
        
        # Get spectrogram
        D = np.abs(librosa.stft(y, n_fft=frame_length, hop_length=hop_length))
        
        # Extract additional features
        # Mel-frequency cepstral coefficients (MFCCs)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfccs, axis=1).tolist()
        mfcc_std = np.std(mfccs, axis=1).tolist()  # Add standard deviation for robustness
        
        # Spectral centroid
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = float(np.mean(centroid))
        
        # Spectral contrast
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = np.mean(contrast, axis=1).tolist()
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1).tolist()
        
        # Find top frequencies for each frame
        freq_data = []
        freqs = librosa.fft_frequencies(sr=sr, n_fft=frame_length)
        
        for frame in range(D.shape[1]):
            # Get the magnitudes for this frame
            magnitudes = D[:, frame]
            
            # Find the indices of the top frequencies
            top_indices = np.argsort(magnitudes)[-num_freqs:]
            
            # Get the actual frequencies and their magnitudes
            frame_freqs = [(freqs[idx], float(magnitudes[idx])) for idx in top_indices]
            
            # Sort by magnitude (highest first)
            frame_freqs.sort(key=lambda x: x[1], reverse=True)
            
            freq_data.append(frame_freqs)
        
        # Create a more comprehensive feature representation
        feature_data = {
            "freq_frames": freq_data,
            "mfcc": mfcc_mean,
            "mfcc_std": mfcc_std,
            "centroid": centroid_mean,
            "contrast": contrast_mean,
            "chroma": chroma_mean,
            "duration": len(y) / sr
        }
        
        # Save the frequency data
        with open(output_file, 'w') as f:
            json.dump(feature_data, f)
            
        return output_file
        
    except Exception as e:
        print(f"Error extracting frequencies: {e}")
        return None

def convert_to_frequencies(audio_file, output_file=None):
    """
    Convert audio file to frequency representation, trying external tool first
    then falling back to internal implementation if needed
    
    Args:
        audio_file (str): Path to input audio file
        output_file (str, optional): Path to output frequency file
        
    Returns:
        str: Path to the frequency file or None if failed
    """
    # Always use internal implementation instead of trying to use GetMaxFreqs
    print("Using internal frequency extraction")
    return convert_to_frequencies_internal(audio_file, output_file)

def process_directory(directory):
    """
    Process all audio files in a directory and save frequency representations to database
    
    Args:
        directory (str): Directory containing audio files
    """
    os.makedirs("database", exist_ok=True)
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip directories and non-audio files
        if os.path.isdir(filepath) or not filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
            continue
            
        print(f"Processing {filename}...")
        
        # Generate output path in database directory
        output_file = os.path.join("database", os.path.splitext(filename)[0] + ".freq")
        
        # Convert to frequency representation
        convert_to_frequencies(filepath, output_file)
        
    print(f"Processed {len(os.listdir('database'))} files to database directory") 