# Music Identification using NCD (Normalized Compression Distance)

This project implements a music identification system using Normalized Compression Distance (NCD) to identify songs from short segments. The system compares the performance of various compressors for this task.

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

The project requires Python 3.12+ and the following libraries (listed in `requirements.txt`):
- librosa
- numpy
- scipy
- matplotlib
- scikit-learn
- pydub
- soundfile
- and more (see `requirements.txt` for the complete list)

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
- `evaluate_compressors.py`: Script to evaluate different compressors
- `audio_processing.py`: Functions for audio handling
- `feature_extraction.py`: Functions for converting audio to frequency features
- `ncd.py`: Functions for NCD calculation
- `music_identification.py`: Functions for music identification
- `main.py`: Main command line interface
- `demo.ipynb`: Jupyter notebook for system demonstration

## Test Music Files

Download test music files from:
URL: https://filesender.fccn.pt/?s=download&token=141af58e-6b32-4826-a84d-777097c0b377

## References

Rudi Cilibrasi, Paul Vitányi, and Ronald de Wolf, *Algorithmic Clustering of Music Based on String Compression*, Computer Music Journal, 28:4, pp. 49–67, 2004.
