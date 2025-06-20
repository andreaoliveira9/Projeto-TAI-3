# Projeto-TAI-3
Terceiro projeto Teoria Algorítmica da Informação

Nota: 19

## Overview

NCD is an approximation of the non-computable Normalized Information Distance (NID) using standard compression algorithms. This implementation identifies music tracks from small segments (e.g., 10 seconds) by comparing their frequency representations.

## Features

- Extract random segments from music files
- Convert audio files to frequency representations
- Calculate NCD between audio files using multiple compressors (gzip, bzip2, lzma, zstd)
- Identify music from segments based on NCD values
- Add noise to test system robustness
- Evaluate and visualize performance of different compressors

## Requirements

### Python Dependencies

The project requires Python 3.12+ and the libraries listed in `requirements.txt`.

### Compressors

The following compressors are required:
- gzip
- bzip2
- lzma
- zstd

## Installation

1. Clone this repository
   ```
   git clone https://github.com/andreaoliveira9/Projeto-TAI-3.git
   cd src
   ```

2. Create a virtual environment
   ```
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages
   ```
   pip install -r requirements.txt
   ```

## Running the Demo (demo.ipynb)

The `demo.ipynb` notebook provides a complete demonstration of the music identification system. To run it:

1. Make sure all dependencies are installed
2. Place the music file you want to identify in the `demo_music` directory (WAV format)
3. Run the notebook cells in sequence to:
   - Convert music files to frequency representations
   - Extract music segments (optional)
   - Add noise to segments (optional)
   - Convert segments to frequency representations
   - Identify music by comparing segments with the database

## Using the Web Interface

The web interface allows you to record a music segment directly from yout microphone and automatically identify the most likely song.

### How to use

1. **Run the web server:**
   ```bash
   python web_interface.py
   ```

2. **Open your browser** and go to:
   ```
   http://127.0.0.1:5000
   ```

3. **Record a music segment** (10 seconds) using the button in the interface.
4. Wait for processing. The most likely song name will be displayed in a highlighted style.

---

## Using the Command-Line Live Identifier

The script `live_music_identification.py` allows you to identify a song by recording 10 seconds from your microphone via the terminal.

### How to use

1. **Run the script:**
   ```bash
   python live_music_identification.py
   ```

2. **Follow the instructions in the terminal:**
   - The script will record 10 seconds from your microphone.
   - After recording, the audio will be processed and the most likely song name will be displayed in the terminal.

---

## How It Works

The system works by:
1. Converting audio files to frequency representations
2. Calculating the Normalized Compression Distance (NCD) between a query segment and all files in the database
3. Ranking the results by similarity (lower NCD means higher similarity)
4. Returning the most likely matches

NCD is calculated as:

$$
\text{NCD}(x, y) = \frac{C(x, y) - \min\{C(x), C(y)\}}{\max\{C(x), C(y)\}}
$$

where C(x) is the compressed size of x, and C(x,y) is the compressed size of x and y concatenated.

## Directory Structure

- `/database`: Contains frequency representations of music files
- `/segments`: Contains extracted segments for testing
- `/demo_music`: Contains music files for demonstration
- `/demo_segments`: Contains extracted segments for demonstration
- `/test`: Contains .freq files
- `/results`: Contains evaluation results and performance metrics
- `/musics`: Contains the original music files subdivided into genres
- `/GetMaxFreqs`: Contains the external frequency extraction tool
- `evaluate_compressors.py`: Script to evaluate different compressors
- `audio_processing.py`: Functions for audio handling
- `feature_extraction.py`: Functions for converting audio to frequency features
- `ncd.py`: Functions for NCD calculation
- `music_identification.py`: Functions for music identification
- `main.py`: Main command line interface
- `demo.ipynb`: Jupyter notebook for system demonstration
- `web_interface.py`: Web server for the music identification interface
- `live_music_identification.py`: Command-line tool for live music identification
- `test.py`: Test suite for the music identification system
- `templates/`: Contains HTML templates for the web interface
  - `index.html`: Main page of the web interface

## Test Music Files

Download test music files from:
URL: https://filesender.fccn.pt/?s=download&token=141af58e-6b32-4826-a84d-777097c0b377

## References

Rudi Cilibrasi, Paul Vitányi, and Ronald de Wolf, *Algorithmic Clustering of Music Based on String Compression*, Computer Music Journal, 28:4, pp. 49–67, 2004.
