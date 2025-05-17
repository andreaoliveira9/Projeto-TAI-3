#!/usr/bin/env python3
import os
import argparse
import random
import shutil
from audio_processing import extract_random_segment, add_noise
from feature_extraction import convert_to_frequencies
from ncd import calculate_ncd_with_database
from music_identification import identify_music, evaluate_compressor_performance

def setup_test_environment(music_dir, num_segments=3, duration=10, noise_levels=[0.0, 0.1, 0.2]):
    """
    Create a complete test environment:
    1. Create segments from music files
    2. Create versions with different noise levels
    3. Convert all to frequency representation
    
    Args:
        music_dir: Directory with music files
        num_segments: Number of segments to extract from each file
        duration: Duration of each segment in seconds
        noise_levels: List of noise levels to apply
    
    Returns:
        Dictionary with test file information
    """
    # Create test directories
    os.makedirs("segments", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    os.makedirs("test", exist_ok=True)
    
    # Track all files created
    test_files = {
        "music_files": [],
        "segments": [],
        "noisy_segments": {},
        "freq_files": [],
        "database_files": [],
    }
    
    # Find music files
    music_files = []
    for filename in os.listdir(music_dir):
        if filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
            music_files.append(os.path.join(music_dir, filename))
            test_files["music_files"].append(filename)
    
    if not music_files:
        print(f"No music files found in {music_dir}")
        return test_files
        
    print(f"Found {len(music_files)} music files")
    
    # Process for database - convert original files to frequency representation
    for music_file in music_files:
        base_name = os.path.splitext(os.path.basename(music_file))[0]
        db_file = os.path.join("database", f"{base_name}.freq")
        print(f"Converting {base_name} to frequency representation for database...")
        convert_to_frequencies(music_file, db_file)
        test_files["database_files"].append(db_file)
    
    # Create segments from each file
    for music_file in music_files:
        base_name = os.path.splitext(os.path.basename(music_file))[0]
        
        # Extract segments
        for i in range(num_segments):
            segment_file = os.path.join("segments", f"{base_name}_segment_{i}.wav")
            print(f"Extracting segment {i+1}/{num_segments} from {base_name}...")
            extract_random_segment(music_file, segment_file, duration)
            test_files["segments"].append(segment_file)
            
            # Create noisy versions
            for noise_level in noise_levels:
                if noise_level == 0.0:
                    continue  # Skip 0.0 noise level - already have clean segment
                    
                noisy_file = os.path.join("segments", f"{base_name}_segment_{i}_noise_{noise_level}.wav")
                print(f"  Adding noise level {noise_level} to segment {i+1}...")
                add_noise(segment_file, noisy_file, noise_level)
                
                if noise_level not in test_files["noisy_segments"]:
                    test_files["noisy_segments"][noise_level] = []
                test_files["noisy_segments"][noise_level].append(noisy_file)
                
            # Convert segment to frequency representation
            freq_file = os.path.join("test", f"{base_name}_segment_{i}.freq")
            print(f"  Converting segment {i+1} to frequency representation...")
            convert_to_frequencies(segment_file, freq_file)
            test_files["freq_files"].append(freq_file)
            
            # Also convert noisy segments
            for noise_level in noise_levels:
                if noise_level == 0.0:
                    continue
                noisy_file = os.path.join("segments", f"{base_name}_segment_{i}_noise_{noise_level}.wav")
                noisy_freq_file = os.path.join("test", f"{base_name}_segment_{i}_noise_{noise_level}.freq")
                print(f"  Converting noisy segment (level {noise_level}) to frequency representation...")
                convert_to_frequencies(noisy_file, noisy_freq_file)
                test_files["freq_files"].append(noisy_freq_file)
    
    return test_files

def run_tests(compressors=None):
    """
    Run tests on all frequency files in the test directory.
    
    Args:
        compressors: List of compressors to use (default: gzip, bzip2, lzma, zstd)
    """
    if compressors is None:
        compressors = ["gzip", "bzip2", "lzma", "zstd"]
    
    # Find test frequency files
    test_files = [os.path.join("test", f) for f in os.listdir("test") if f.endswith(".freq")]
    
    if not test_files:
        print("No test files found in test directory")
        return
        
    # Test each frequency file with each compressor
    for test_file in test_files:
        print(f"\nTesting {os.path.basename(test_file)}:")
        
        for compressor in compressors:
            print(f"\nUsing compressor: {compressor}")
            results = calculate_ncd_with_database(test_file, compressor)
            
            # Get top matches
            top_matches = identify_music(results, 3)
            
            print(f"Top 3 matches:")
            for i, (name, distance) in enumerate(top_matches, 1):
                print(f"  {i}. {name} - NCD: {distance:.4f}")
                
            # Check if correct
            test_file_name = os.path.basename(test_file)
            actual_name = test_file_name.split("_segment_")[0]  # Extract original name
            predicted_name = top_matches[0][0] if top_matches else None
            
            if actual_name == predicted_name:
                print(f"✓ Correct identification!")
            else:
                print(f"✗ Incorrect identification. Expected: {actual_name}, Got: {predicted_name}")

def main():
    parser = argparse.ArgumentParser(description="Run a complete test of the music identification system")
    parser.add_argument("music_dir", help="Directory containing music files")
    parser.add_argument("--segments", type=int, default=3, help="Number of segments to extract per file (default: 3)")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration of segments in seconds (default: 10)")
    parser.add_argument("--noise-levels", type=float, nargs="+", default=[0.0, 0.1, 0.2], 
                        help="Noise levels to test (default: 0.0 0.1 0.2)")
    parser.add_argument("--skip-setup", action="store_true", help="Skip setup and use existing test files")
    parser.add_argument("--compressors", nargs="+", default=["gzip", "bzip2", "lzma", "zstd"], 
                        help="Compressors to test (default: gzip bzip2 lzma zstd)")
    
    args = parser.parse_args()
    
    if not args.skip_setup:
        test_files = setup_test_environment(
            args.music_dir,
            num_segments=args.segments,
            duration=args.duration,
            noise_levels=args.noise_levels
        )
        
        print(f"\nSetup complete:")
        print(f"- {len(test_files['music_files'])} music files processed")
        print(f"- {len(test_files['segments'])} segments extracted")
        print(f"- {sum(len(files) for files in test_files['noisy_segments'].values())} noisy segments created")
        print(f"- {len(test_files['freq_files'])} frequency files generated")
        print(f"- {len(test_files['database_files'])} database files created")
    
    # Run the tests
    run_tests(args.compressors)
    
    # Evaluate performance for each compressor
    print("\n--- Evaluating compressor performance ---")
    results = evaluate_compressor_performance("test", args.compressors)
    
    print("\nSummary:")
    for compressor in args.compressors:
        correct = results[compressor]["correct"]
        total = results[compressor]["total"]
        accuracy = results[compressor]["accuracy"]
        print(f"{compressor}: {correct}/{total} correct ({accuracy:.2%} accuracy)")

if __name__ == "__main__":
    main() 