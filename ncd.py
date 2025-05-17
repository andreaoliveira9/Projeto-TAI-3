#!/usr/bin/env python3
import os
import subprocess
import glob
from collections import defaultdict

def compress_file(filename, compressor="gzip"):
    """
    Compress a file and return the size of the compressed file.
    
    Args:
        filename (str): Path to the file to compress
        compressor (str): Compressor to use (gzip, bzip2, lzma, zstd)
        
    Returns:
        int: Size of the compressed file in bytes
    """
    compressor_cmds = {
        "gzip": ["gzip", "-c"],
        "bzip2": ["bzip2", "-c"],
        "lzma": ["xz", "--lzma", "-c"],
        "zstd": ["zstd", "-c"]
    }
    
    if compressor not in compressor_cmds:
        raise ValueError(f"Unsupported compressor: {compressor}")
    
    try:
        with open(os.devnull, 'wb') as devnull:
            result = subprocess.run(
                compressor_cmds[compressor] + [filename],
                stdout=subprocess.PIPE,
                stderr=devnull,
                check=True
            )
        return len(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error compressing file: {e}")
        return 0

def concatenate_files(file1, file2):
    """
    Concatenate two files and return the path to the concatenated file.
    
    Args:
        file1 (str): Path to the first file
        file2 (str): Path to the second file
        
    Returns:
        str: Path to the temporary concatenated file
    """
    import tempfile
    
    temp_file = tempfile.mktemp()
    
    with open(temp_file, 'wb') as outfile:
        for filename in [file1, file2]:
            with open(filename, 'rb') as infile:
                outfile.write(infile.read())
    
    return temp_file

def calculate_ncd(file1, file2, compressor="gzip"):
    """
    Calculate Normalized Compression Distance between two files.
    
    Args:
        file1 (str): Path to the first file
        file2 (str): Path to the second file
        compressor (str): Compressor to use (gzip, bzip2, lzma, zstd)
        
    Returns:
        float: NCD value between 0 and 1
    """
    # Compress individual files
    c_x = compress_file(file1, compressor)
    c_y = compress_file(file2, compressor)
    
    # Concatenate and compress
    concat_file = concatenate_files(file1, file2)
    c_xy = compress_file(concat_file, compressor)
    
    # Clean up
    os.unlink(concat_file)
    
    # Calculate NCD
    if min(c_x, c_y) == 0:
        return 1.0
    
    ncd = (c_xy - min(c_x, c_y)) / max(c_x, c_y)
    
    # Clamp to valid range [0, 1]
    return max(0.0, min(1.0, ncd))

def calculate_ncd_with_database(query_file, compressor="gzip"):
    """
    Calculate NCD between a query file and all files in the database.
    
    Args:
        query_file (str): Path to the query frequency file
        compressor (str): Compressor to use
        
    Returns:
        dict: Dictionary mapping database file names to NCD values
    """
    results = {}
    database_dir = "database"
    
    # Find all frequency files in the database directory
    database_files = glob.glob(os.path.join(database_dir, "*.freq"))
    
    if not database_files:
        print(f"No frequency files found in {database_dir}")
        return {}
    
    print(f"Comparing {query_file} with {len(database_files)} database files using {compressor}...")
    
    # Calculate NCD for each database file
    for db_file in database_files:
        name = os.path.splitext(os.path.basename(db_file))[0]
        ncd = calculate_ncd(query_file, db_file, compressor)
        results[name] = ncd
        print(f"  {name}: {ncd:.4f}")
    
    return results

def compare_compressors(file1, file2, compressors=None):
    """
    Compare NCD values using different compressors.
    
    Args:
        file1 (str): Path to the first file
        file2 (str): Path to the second file
        compressors (list): List of compressors to use
        
    Returns:
        dict: Dictionary mapping compressor names to NCD values
    """
    if compressors is None:
        compressors = ["gzip", "bzip2", "lzma", "zstd"]
    
    results = {}
    
    for compressor in compressors:
        try:
            ncd = calculate_ncd(file1, file2, compressor)
            results[compressor] = ncd
        except Exception as e:
            print(f"Error with compressor {compressor}: {e}")
    
    return results 