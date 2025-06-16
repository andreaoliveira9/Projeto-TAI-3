#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import os
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
from audio_processing import convert_to_mono_wav
from feature_extraction import convert_to_frequencies
from ncd import calculate_ncd_with_database
from music_identification import identify_music
import base64
from pydub import AudioSegment
import collections
from statistics import mode, multimode
import socket
import math

app = Flask(__name__)

# Ensure the templates directory exists
os.makedirs("templates", exist_ok=True)


def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


@app.route("/")
def index():
    return render_template("index.html")


def process_segment(audio_segment, temp_dir):
    """Process a single audio segment and return its identification results"""
    # Save segment to temporary file
    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", dir=temp_dir, delete=False)
    audio_segment.export(temp_wav.name, format="wav")

    try:
        # Convert to mono WAV
        mono_wav = convert_to_mono_wav(temp_wav.name)

        # Convert to frequency representation
        temp_freq = tempfile.NamedTemporaryFile(
            suffix=".freq", dir=temp_dir, delete=False
        )
        freq_file = convert_to_frequencies(mono_wav, temp_freq.name)

        if freq_file is None:
            return None

        # Calculate NCD with database
        ncd_results = calculate_ncd_with_database(freq_file, compressor="bzip2")

        # Identify the music
        matches = identify_music(ncd_results, num_results=3)

        return matches

    finally:
        # Clean up temporary files
        os.unlink(temp_wav.name)
        if mono_wav and mono_wav != temp_wav.name:
            os.unlink(mono_wav)
        if freq_file:
            os.unlink(freq_file)


@app.route("/record", methods=["POST"])
def record_audio():
    try:
        audio_b64 = request.get_json()["audio"]

        # Decode base64 to bytes
        audio_bytes = base64.b64decode(audio_b64)

        # Save to temporary WAV file
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with open(temp_wav.name, "wb") as f:
            f.write(audio_bytes)

        try:
            # Load the audio file
            audio = AudioSegment.from_file(temp_wav.name)

            # Create a temporary directory for segment processing
            temp_dir = tempfile.mkdtemp()

            # Process multiple overlapping segments
            segment_duration = 7000  # 7 seconds
            overlap = 1000  # 1 second overlap
            all_matches = []

            for start_ms in range(
                0, len(audio) - segment_duration, segment_duration - overlap
            ):
                segment = audio[start_ms : start_ms + segment_duration]
                matches = process_segment(segment, temp_dir)
                if matches:
                    all_matches.extend(matches)

            if not all_matches:
                return jsonify({"success": True, "matches": []})

            # Get all song names from matches
            song_names = [name for name, _ in all_matches]

            # Count occurrences of each song
            song_counts = collections.Counter(song_names)

            # Get the most common songs (up to 3)
            most_common = song_counts.most_common(3)

            # For each most common song, calculate its average distance
            final_matches = []
            for name, count in most_common:
                # Get all distances for this song
                distances = [
                    float(distance)
                    for song_name, distance in all_matches
                    if song_name == name
                ]
                # Calculate average distance
                avg_distance = sum(distances) / len(distances)
                final_matches.append((name, avg_distance))

            no_matches = all(
                math.isclose(match[1], 1.0, rel_tol=1e-9) for match in final_matches
            )

            if no_matches:
                return jsonify({"success": True, "matches": []})

            # Format results
            results = [
                {"name": name, "distance": f"{distance:.4f}"}
                for name, distance in final_matches
            ]

            return jsonify({"success": True, "matches": results})

        finally:
            # Clean up temporary files
            os.unlink(temp_wav.name)
            # Clean up temporary directory
            for file in os.listdir(temp_dir):
                os.unlink(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"\nServidor rodando em:")
    print(f"Local:   https://localhost:5001")
    print(f"Rede:    https://{local_ip}:5001")
    print("\nAcesse qualquer um dos endereços acima para usar a aplicação.")
    app.run(host="0.0.0.0", port=5001, debug=True, ssl_context="adhoc")
