#!/usr/bin/env python3
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from ncd import compare_compressors
from music_identification import evaluate_compressor_performance

def plot_compression_sizes(files, compressors=None):
    """
    Plot the compression sizes for different files and compressors
    """
    if compressors is None:
        compressors = ["gzip", "bzip2", "xz", "zstd"]
    
    from ncd import compress_file
    
    results = {}
    for file in files:
        results[os.path.basename(file)] = {}
        for compressor in compressors:
            size = compress_file(file, compressor)
            results[os.path.basename(file)][compressor] = size
    
    # Plot results
    fig, ax = plt.subplots(figsize=(10, 6))
    
    width = 0.2
    x = np.arange(len(files))
    
    for i, compressor in enumerate(compressors):
        sizes = [results[os.path.basename(file)][compressor] for file in files]
        ax.bar(x + i*width, sizes, width, label=compressor)
    
    ax.set_xlabel('Files')
    ax.set_ylabel('Compressed size (bytes)')
    ax.set_title('Compression sizes by compressor')
    ax.set_xticks(x + width * (len(compressors)-1)/2)
    ax.set_xticklabels([os.path.basename(file) for file in files], rotation=45, ha='right')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('compression_sizes.png')
    plt.close()

def plot_ncd_comparison(file_pairs, compressors=None):
    """
    Plot NCD values for pairs of files using different compressors
    """
    if compressors is None:
        compressors = ["gzip", "bzip2", "xz", "zstd"]
    
    ncd_values = {}
    pair_labels = []
    
    for file1, file2 in file_pairs:
        pair_name = f"{os.path.basename(file1)} - {os.path.basename(file2)}"
        pair_labels.append(pair_name)
        
        results = compare_compressors(file1, file2, compressors)
        ncd_values[pair_name] = results
    
    # Plot results
    fig, ax = plt.subplots(figsize=(12, 6))
    
    width = 0.2
    x = np.arange(len(pair_labels))
    
    for i, compressor in enumerate(compressors):
        ncd_vals = [ncd_values[pair].get(compressor, np.nan) for pair in pair_labels]
        ax.bar(x + i*width, ncd_vals, width, label=compressor)
    
    ax.set_xlabel('File pairs')
    ax.set_ylabel('NCD value')
    ax.set_title('NCD comparison by compressor')
    ax.set_xticks(x + width * (len(compressors)-1)/2)
    ax.set_xticklabels(pair_labels, rotation=45, ha='right')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('ncd_comparison.png')
    plt.close()

def plot_compressor_accuracy(results):
    """
    Plot accuracy results for different compressors
    """
    compressors = list(results.keys())
    accuracy = [results[c]["accuracy"] for c in compressors]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.bar(compressors, accuracy)
    ax.set_xlabel('Compressor')
    ax.set_ylabel('Accuracy')
    ax.set_title('Music identification accuracy by compressor')
    ax.set_ylim(0, 1)
    
    # Add accuracy values as text on top of bars
    for i, v in enumerate(accuracy):
        ax.text(i, v + 0.01, f"{v:.2%}", ha='center')
    
    plt.tight_layout()
    plt.savefig('compressor_accuracy.png')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare different compressors")
    parser.add_argument("--test-dir", required=True, help="Directory with test segments")
    parser.add_argument("--compressors", nargs="+", default=["gzip", "bzip2", "xz", "zstd"], 
                        help="Compressors to evaluate")
    
    args = parser.parse_args()
    
    # Evaluate compressor performance
    results = evaluate_compressor_performance(args.test_dir, args.compressors)
    
    # Plot results
    plot_compressor_accuracy(results)
    
    print(f"Results saved to compressor_accuracy.png")

if __name__ == "__main__":
    main() 