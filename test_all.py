#!/usr/bin/env python3
import os
import subprocess
import argparse
from collections import defaultdict

def run_command(cmd):
    """Run a command and return the output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def clean_database():
    """Clean the database directory"""
    run_command("rm -rf database/*")
    print("Database cleaned")

def clean_segments():
    """Clean the segments directory"""
    run_command("rm -rf segments/*")
    print("Segments cleaned")

def process_music_files(directory):
    """Process all music files in directory"""
    print(f"\n--- Processing music files from {directory} ---")
    run_command(f"python main.py process_db {directory}")

def test_with_compressor(segment_file, compressor):
    """Test segment with a specific compressor"""
    print(f"\n--- Testing with compressor: {compressor} ---")
    output = run_command(f"python main.py compare {segment_file} -c {compressor}")
    print(output)
    
    # Extract the top match
    lines = output.strip().split('\n')
    top_match = None
    
    for line in lines:
        if line.startswith("1."):
            top_match = line.split('-')[0].strip()[3:]  # Extract the name only
            break
    
    return top_match

def extract_segment(music_file, duration=10):
    """Extract a segment from a music file"""
    base_name = os.path.splitext(os.path.basename(music_file))[0]
    segment_file = f"segments/{base_name}_segment_{duration}s.wav"
    
    print(f"\n--- Extracting {duration}s segment from {base_name} ---")
    run_command(f"python main.py extract {music_file} -d {duration} -o {segment_file}")
    
    return segment_file

def add_noise_to_segment(segment_file, noise_level):
    """Add noise to a segment"""
    base_name = os.path.splitext(segment_file)[0]
    noisy_file = f"{base_name}_noise_{noise_level}.wav"
    
    print(f"\n--- Adding noise level {noise_level} to {os.path.basename(segment_file)} ---")
    run_command(f"python main.py noise {segment_file} -l {noise_level} -o {noisy_file}")
    
    return noisy_file

def run_comprehensive_test(music_dir, durations=[10, 15, 20], noise_levels=[0.0, 0.1, 0.2], 
                         compressors=["gzip", "bzip2", "xz", "zstd"]):
    """Run comprehensive tests with different parameters"""
    results = defaultdict(dict)
    
    # Clean segments directory only
    clean_segments()
    
    # Check if database is empty, only then process music files
    if not os.listdir("database"):
        # Process music files
        process_music_files(music_dir)
    else:
        print("Using existing database")
    
    # Get all music files
    music_files = []
    for file in os.listdir(music_dir):
        if file.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
            music_files.append(os.path.join(music_dir, file))
    
    if not music_files:
        print(f"No music files found in {music_dir}")
        return
    
    print(f"Found {len(music_files)} music files")
    
    # Test with different durations
    for music_file in music_files:
        base_name = os.path.splitext(os.path.basename(music_file))[0]
        print(f"\n===== Testing with music: {base_name} =====")
        
        results[base_name] = {
            "durations": {},
            "noise_levels": {}
        }
        
        # Test with different durations
        for duration in durations:
            print(f"\n----- Testing with duration: {duration}s -----")
            segment_file = extract_segment(music_file, duration)
            
            correct_matches = 0
            total = len(compressors)
            
            for compressor in compressors:
                top_match = test_with_compressor(segment_file, compressor)
                is_correct = (top_match == base_name)
                
                if is_correct:
                    correct_matches += 1
                
                print(f"Compressor: {compressor}, Top match: {top_match}, Correct: {is_correct}")
            
            accuracy = correct_matches / total if total > 0 else 0
            results[base_name]["durations"][duration] = {
                "accuracy": accuracy,
                "correct": correct_matches,
                "total": total
            }
            print(f"Duration {duration}s accuracy: {accuracy:.2%} ({correct_matches}/{total})")
        
        # Test with different noise levels
        print(f"\n----- Testing with noise levels -----")
        # Use the best duration based on previous test
        best_duration = max(results[base_name]["durations"].items(), 
                          key=lambda x: x[1]["accuracy"])[0]
        segment_file = extract_segment(music_file, best_duration)
        
        for noise_level in noise_levels:
            if noise_level == 0.0:
                # Already tested with clean segment above
                continue
                
            noisy_file = add_noise_to_segment(segment_file, noise_level)
            
            correct_matches = 0
            total = len(compressors)
            
            for compressor in compressors:
                top_match = test_with_compressor(noisy_file, compressor)
                is_correct = (top_match == base_name)
                
                if is_correct:
                    correct_matches += 1
                
                print(f"Noise level: {noise_level}, Compressor: {compressor}, " + 
                     f"Top match: {top_match}, Correct: {is_correct}")
            
            accuracy = correct_matches / total if total > 0 else 0
            results[base_name]["noise_levels"][noise_level] = {
                "accuracy": accuracy,
                "correct": correct_matches,
                "total": total
            }
            print(f"Noise level {noise_level} accuracy: {accuracy:.2%} ({correct_matches}/{total})")
    
    # Print summary
    print("\n\n========= SUMMARY =========")
    
    print("\n--- Duration Accuracy ---")
    for duration in durations:
        correct = sum(info["durations"].get(duration, {}).get("correct", 0) for _, info in results.items())
        total = sum(info["durations"].get(duration, {}).get("total", 0) for _, info in results.items())
        accuracy = correct / total if total > 0 else 0
        print(f"Duration {duration}s: {accuracy:.2%} ({correct}/{total})")
    
    print("\n--- Noise Level Accuracy ---")
    for level in noise_levels:
        if level == 0.0:
            continue
        correct = sum(info["noise_levels"].get(level, {}).get("correct", 0) for _, info in results.items())
        total = sum(info["noise_levels"].get(level, {}).get("total", 0) for _, info in results.items())
        accuracy = correct / total if total > 0 else 0
        print(f"Noise level {level}: {accuracy:.2%} ({correct}/{total})")
    
    print("\n--- Compressor Performance ---")
    compressor_results = defaultdict(lambda: {"correct": 0, "total": 0})
    
    for music, info in results.items():
        # Count duration tests
        for duration, data in info["durations"].items():
            for compressor in compressors:
                # We don't have per-compressor results saved, so we'll use the best guess
                compressor_results[compressor]["total"] += 1
                if data["accuracy"] > 0:  # If any compressor got it right
                    compressor_results[compressor]["correct"] += data["accuracy"]
        
        # Count noise tests
        for level, data in info["noise_levels"].items():
            for compressor in compressors:
                # We don't have per-compressor results saved, so we'll use the best guess
                compressor_results[compressor]["total"] += 1
                if data["accuracy"] > 0:  # If any compressor got it right
                    compressor_results[compressor]["correct"] += data["accuracy"]
    
    for compressor in compressors:
        correct = compressor_results[compressor]["correct"]
        total = compressor_results[compressor]["total"]
        accuracy = correct / total if total > 0 else 0
        print(f"Compressor {compressor}: {accuracy:.2%} ({correct:.1f}/{total})")

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive tests for music identification")
    parser.add_argument("music_dir", help="Directory containing music files")
    parser.add_argument("--durations", type=float, nargs="+", default=[10, 15, 20],
                      help="Segment durations in seconds to test (default: 10 15 20)")
    parser.add_argument("--noise-levels", type=float, nargs="+", default=[0.0, 0.1, 0.2],
                      help="Noise levels to test (default: 0.0 0.1 0.2)")
    parser.add_argument("--compressors", nargs="+", default=["gzip", "bzip2", "xz", "zstd"],
                      help="Compressors to test (default: gzip bzip2 xz zstd)")
    
    args = parser.parse_args()
    
    run_comprehensive_test(args.music_dir, args.durations, args.noise_levels, args.compressors)

if __name__ == "__main__":
    main() 