#!/usr/bin/env python3
import os
import subprocess
import tempfile
import numpy as np
import librosa
import json
from audio_processing import convert_to_mono_wav

# Path to GetMaxFreqs executable - update this based on your system
GETMAXFREQS_PATH = "./GetMaxFreqs_exec"


def check_getmaxfreqs():
    """Check if GetMaxFreqs executable exists and is callable"""
    if not os.path.exists(GETMAXFREQS_PATH):
        print(f"WARNING: GetMaxFreqs executable not found at {GETMAXFREQS_PATH}")
        return False
    return True


def convert_to_frequencies_external(
    audio_file, output_file=None, num_freqs=4, frame_length=1024
):
    """
    Convert audio file to frequency representation using external GetMaxFreqs tool
    Args:
        audio_file (str): Path to input audio file (should be mono WAV)
        output_file (str, optional): Path to output frequency file
        num_freqs (int): Number of significant frequencies (NF)
        frame_length (int): FFT window size (WS)
    Returns:
        str: Path to the frequency file or None if failed
    """
    if not check_getmaxfreqs():
        print("Using internal frequency extraction instead.")
        return convert_to_frequencies_internal(
            audio_file, output_file, num_freqs=num_freqs, frame_length=frame_length
        )
    if output_file is None:
        output_file = os.path.splitext(audio_file)[0] + ".freq"
    mono_wav = convert_to_mono_wav(audio_file)
    stereo_wav = tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-i", mono_wav, "-ac", "2", stereo_wav],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Passar NF e WS como argumentos para o GetMaxFreqs, se suportado
        subprocess.run(
            [
                GETMAXFREQS_PATH,
                "-w",
                output_file,
                "--nf",
                str(num_freqs),
                "--ws",
                str(frame_length),
                stereo_wav,
            ],
            check=True,
        )
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error calling GetMaxFreqs: {e}")
        return None
    finally:
        if os.path.exists(stereo_wav):
            os.remove(stereo_wav)


def convert_to_frequencies_internal(
    audio_file, output_file=None, num_freqs=4, frame_length=1024
):
    """
    Convert audio file to frequency representation using internal implementation
    Args:
        audio_file (str): Path to input audio file
        output_file (str, optional): Path to output frequency file
        num_freqs (int): Number of significant frequencies (NF)
        frame_length (int): FFT window size (WS)
    Returns:
        str: Path to the frequency file or None if failed
    """
    if output_file is None:
        output_file = os.path.splitext(audio_file)[0] + ".freq"
    try:
        y, sr = librosa.load(audio_file, sr=None, mono=True)
        hop_length = 256
        D = np.abs(librosa.stft(y, n_fft=frame_length, hop_length=hop_length))
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfccs, axis=1).tolist()
        mfcc_std = np.std(mfccs, axis=1).tolist()
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = float(np.mean(centroid))
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = np.mean(contrast, axis=1).tolist()
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1).tolist()
        freq_data = []
        freqs = librosa.fft_frequencies(sr=sr, n_fft=frame_length)
        for frame in range(D.shape[1]):
            magnitudes = D[:, frame]
            top_indices = np.argsort(magnitudes)[-num_freqs:]
            frame_freqs = [(freqs[idx], float(magnitudes[idx])) for idx in top_indices]
            frame_freqs.sort(key=lambda x: x[1], reverse=True)
            freq_data.append(frame_freqs)
        feature_data = {
            "freq_frames": freq_data,
            "mfcc": mfcc_mean,
            "mfcc_std": mfcc_std,
            "centroid": centroid_mean,
            "contrast": contrast_mean,
            "chroma": chroma_mean,
            "duration": len(y) / sr,
        }
        with open(output_file, "w") as f:
            json.dump(feature_data, f)
        return output_file
    except Exception as e:
        print(f"Error extracting frequencies: {e}")
        return None


def convert_to_frequencies(
    audio_file, output_file=None, num_freqs=4, frame_length=1024
):
    """
    Convert audio file to frequency representation, trying external tool first
    then falling back to internal implementation if needed
    Args:
        audio_file (str): Path to input audio file
        output_file (str, optional): Path to output frequency file
        num_freqs (int): Number of significant frequencies (NF)
        frame_length (int): FFT window size (WS)
    Returns:
        str: Path to the frequency file or None if failed
    """
    result = convert_to_frequencies_external(
        audio_file, output_file, num_freqs=num_freqs, frame_length=frame_length
    )
    if result is None:
        print("External conversion failed, falling back to internal implementation")
        return convert_to_frequencies_internal(
            audio_file, output_file, num_freqs=num_freqs, frame_length=frame_length
        )
    return result


def process_directory(directory):
    """
    Process all audio files in a directory and save frequency representations to database

    Args:
        directory (str): Directory containing audio files
    """
    os.makedirs(directory, exist_ok=True)

    wav_count = 0

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)

        # Skip directories and non-audio files
        if os.path.isdir(filepath) or not filename.lower().endswith(
            (".mp3", ".wav", ".flac", ".ogg", ".m4a")
        ):
            continue

        wav_count += 1
        print(f"Processing {filename}...")

        # Generate output path in database directory
        output_file = os.path.join(directory, os.path.splitext(filename)[0] + ".freq")

        # Convert to frequency representation
        convert_to_frequencies(filepath, output_file)

    # Count number of .freq files in output directory
    freq_count = sum(1 for f in os.listdir(directory) if f.lower().endswith(".freq"))

    print(f"✅ Successfully processed {freq_count}/{wav_count} files")
