#!/usr/bin/env python3
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import librosa
import tempfile
from ncd import calculate_ncd_with_database
from music_identification import identify_music
from audio_processing import convert_to_mono_wav
from feature_extraction import convert_to_frequencies


def record_audio(duration=10, sample_rate=44100):
    """
    Record audio from the microphone

    Args:
        duration (float): Recording duration in seconds
        sample_rate (int): Sample rate for recording

    Returns:
        tuple: (audio_data, sample_rate)
    """
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    print("Recording finished!")
    return recording, sample_rate


def save_temp_audio(audio_data, sample_rate):
    """
    Save audio data to a temporary WAV file

    Args:
        audio_data (numpy.ndarray): Audio data
        sample_rate (int): Sample rate

    Returns:
        str: Path to temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(temp_file.name, audio_data, sample_rate)
    return temp_file.name


def main():
    # Record audio
    audio_data, sample_rate = record_audio(duration=10)

    # Save to temporary file
    temp_wav = save_temp_audio(audio_data, sample_rate)

    try:
        # Convert to mono WAV if needed
        mono_wav = convert_to_mono_wav(temp_wav)

        # Convert to frequency representation
        temp_freq = tempfile.NamedTemporaryFile(suffix=".freq", delete=False)
        freq_file = convert_to_frequencies(mono_wav, temp_freq.name)

        if freq_file is None:
            print("Error: Failed to convert audio to frequency representation")
            return

        # Calculate NCD with database
        ncd_results = calculate_ncd_with_database(freq_file, compressor="bzip2")

        # Identify the music
        matches = identify_music(ncd_results, num_results=3)

        print("\nTop matches:")
        for name, distance in matches:
            print(f"- {name}: {distance:.4f}")

    finally:
        # Clean up temporary files
        os.unlink(temp_wav)
        if mono_wav and mono_wav != temp_wav:
            os.unlink(mono_wav)
        if freq_file:
            os.unlink(freq_file)


if __name__ == "__main__":
    main()
