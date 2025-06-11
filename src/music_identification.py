#!/usr/bin/env python3
import os
import json
from collections import defaultdict, Counter

def identify_music(ncd_results, num_results=5):
    """
    Identify the most likely music matches from NCD results.
    
    Args:
        ncd_results (dict): Dictionary mapping music names to NCD values
        num_results (int): Number of top results to return
        
    Returns:
        list: List of tuples (name, distance) sorted by distance
    """
    # Sort results by NCD value (lower is better)
    sorted_results = sorted(ncd_results.items(), key=lambda x: x[1])
    
    # Return top results
    return sorted_results[:num_results]

def evaluate_compressor_performance(directory, compressors=None):
    """
    Evaluate the performance of different compressors on a test set.
    
    Args:
        directory (str): Directory containing test segments with known sources
        compressors (list): List of compressors to test
        
    Returns:
        dict: Dictionary with accuracy metrics for each compressor
    """
    from ncd import calculate_ncd_with_database
    
    if compressors is None:
        compressors = ["gzip", "bzip2", "xz", "zstd"]
    
    results = defaultdict(lambda: {"correct": 0, "total": 0})
    
    # Get all segments in the directory
    segment_files = [f for f in os.listdir(directory) if f.endswith(".freq")]
    
    for segment_file in segment_files:
        # Extract ground truth from filename (assumed format: original_name_segment.freq)
        original_name = segment_file.split("_")[0]
        segment_path = os.path.join(directory, segment_file)
        
        print(f"Testing {segment_file} (ground truth: {original_name})")
        
        # Test with each compressor
        for compressor in compressors:
            ncd_results = calculate_ncd_with_database(segment_path, compressor)
            
            # Get top match
            top_matches = identify_music(ncd_results, 1)
            if top_matches and top_matches[0][0] == original_name:
                results[compressor]["correct"] += 1
                
            results[compressor]["total"] += 1
    
    # Calculate accuracy for each compressor
    for compressor in compressors:
        correct = results[compressor]["correct"]
        total = results[compressor]["total"]
        accuracy = (correct / total) if total > 0 else 0
        results[compressor]["accuracy"] = accuracy
        
        print(f"{compressor}: {correct}/{total} correct ({accuracy:.2%})")
    
    return results

def analyze_errors(test_directory, compressor="gzip"):
    """
    Analyze identification errors to find patterns.
    
    Args:
        test_directory (str): Directory containing test segments
        compressor (str): Compressor to use
        
    Returns:
        dict: Error analysis data
    """
    from ncd import calculate_ncd_with_database
    
    error_data = {
        "confusion_matrix": defaultdict(Counter),
        "misclassified_segments": [],
        "ncd_differences": []
    }
    
    # Get all segments in the directory
    segment_files = [f for f in os.listdir(test_directory) if f.endswith(".freq")]
    
    for segment_file in segment_files:
        # Extract ground truth from filename
        original_name = segment_file.split("_")[0]
        segment_path = os.path.join(test_directory, segment_file)
        
        # Get NCD results
        ncd_results = calculate_ncd_with_database(segment_path, compressor)
        
        # Get top match
        top_matches = identify_music(ncd_results, 1)
        
        if top_matches and top_matches[0][0] != original_name:
            predicted = top_matches[0][0]
            
            # Update confusion matrix
            error_data["confusion_matrix"][original_name][predicted] += 1
            
            # Store misclassified segment info
            error_data["misclassified_segments"].append({
                "segment": segment_file,
                "ground_truth": original_name,
                "predicted": predicted,
                "ncd_to_predicted": ncd_results[predicted],
                "ncd_to_truth": ncd_results.get(original_name, float('inf'))
            })
            
            # Store NCD difference between truth and prediction
            if original_name in ncd_results:
                ncd_diff = ncd_results[predicted] - ncd_results[original_name]
                error_data["ncd_differences"].append(ncd_diff)
                
    return error_data 