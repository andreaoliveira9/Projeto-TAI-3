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

app = Flask(__name__)

# Ensure the templates directory exists
os.makedirs("templates", exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


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
            # Convert to mono WAV
            mono_wav = convert_to_mono_wav(temp_wav.name)

            # Convert to frequency representation
            temp_freq = tempfile.NamedTemporaryFile(suffix=".freq", delete=False)
            freq_file = convert_to_frequencies(mono_wav, temp_freq.name)

            if freq_file is None:
                return (
                    jsonify(
                        {"error": "Failed to convert audio to frequency representation"}
                    ),
                    500,
                )

            # Calculate NCD with database
            ncd_results = calculate_ncd_with_database(freq_file, compressor="bzip2")

            # Identify the music
            matches = identify_music(ncd_results, num_results=3)

            # Format results
            results = [
                {"name": name, "distance": f"{distance:.4f}"}
                for name, distance in matches
            ]

            no_matches = all(result["distance"] == 1 for result in results)

            if no_matches:
                return jsonify({"success": True, "matches": []})

            return jsonify({"success": True, "matches": results})

        finally:
            # Clean up temporary files
            os.unlink(temp_wav.name)
            if mono_wav and mono_wav != temp_wav.name:
                os.unlink(mono_wav)
            if freq_file:
                os.unlink(freq_file)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
