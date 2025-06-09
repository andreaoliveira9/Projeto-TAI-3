#!/usr/bin/env python3
import os
import random
import numpy as np
from pydub import AudioSegment
import librosa
import soundfile as sf
import subprocess

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


def add_noise(input_file, output_file, noise_level=0.1, use_sox=False, noise_type="whitenoise",
              add_reverb=False, apply_eq=False, speed=None, pitch=None):    
    """
    Add white or pink noise to an audio file using either librosa+numpy or SoX.
    
    Args:
        input_file (str): Path to input audio file
        output_file (str): Path to output noisy audio file
        noise_level (float): Noise level (0.0-1.0)
        use_sox (bool): If True, use SoX instead of librosa
        noise_type (str): 'whitenoise' or 'pinknoise'
    Returns:
        str or None: Path to output or None on failure
    """
    if use_sox:
        try:
            # Get duration of input audio
            result = subprocess.run(["soxi", "-D", input_file], capture_output=True, text=True)
            duration = float(result.stdout.strip())

            sample_rate = get_sample_rate(input_file)

            # If noise_level is 0, skip noise synthesis and apply effects directly

            if noise_level == 0:
                effects_chain = build_sox_effects_chain(
                    duration=duration,
                    noise_type=noise_type,
                    noise_level=0,
                    reverb=add_reverb,
                    eq=apply_eq,
                    speed=speed,
                    pitch=pitch,
                    sample_rate=sample_rate
                )


                sox_command = f'sox "{input_file}" "{output_file}" {effects_chain}'
                print("SOX CMD:", sox_command)

            else:
                effects_chain = build_sox_effects_chain(
                    duration=duration,
                    noise_type=noise_type,
                    noise_level=noise_level,
                    reverb=add_reverb,
                    eq=apply_eq,
                    speed=speed,
                    pitch=pitch,
                    sample_rate=sample_rate
                )
                sox_command = (
                    f'sox "{input_file}" -p | '
                    f'sox -m -p "|sox -n -p {effects_chain}" '
                    f'"{output_file}"'
                )

            subprocess.run(sox_command, shell=True, check=True)
            return output_file

        except Exception as e:
            print(f"Error adding noise with SoX: {e}")
            return None

    else:
        try:
            y, sr = librosa.load(input_file, sr=None)
            noise = np.random.normal(0, y.std() * noise_level, y.shape)
            y_noisy = np.clip(y + noise, -1.0, 1.0)
            sf.write(output_file, y_noisy, sr)
            return output_file
        except Exception as e:
            print(f"Error adding noise with librosa: {e}")
            return None
        

def get_sample_rate(path):
    try:
        result = subprocess.run(["soxi", "-r", path], capture_output=True, text=True)
        return int(result.stdout.strip())
    except:
        return 44100  # fallback
        
        
def build_sox_effects_chain(
    duration,
    noise_type="whitenoise",
    noise_level=0.1,
    reverb=False,
    eq=False,
    speed=None,
    pitch=None, 
    sample_rate=44100
):
    effects = [f'rate {sample_rate}']
    effects.append(f'rate {sample_rate}')
    if noise_level > 0:
        effects.append(f'synth {duration} {noise_type} vol {noise_level}')

    if reverb:
        effects.append("reverb")

    if eq:
        effects.append("equalizer 1000 1q -10")
        effects.append("equalizer 8000 1q +6")

    if speed:
        effects.append(f"speed {speed}")

    if pitch:
        effects.append(f"pitch {pitch}")

    return " ".join(effects)




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