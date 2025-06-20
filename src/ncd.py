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
        compressor (str): Compressor to use (gzip, bzip2, lzma, zstd, xz)
        
    Returns:
        int: Size of the compressed file in bytes
    """
    compressor_cmds = {
        "gzip": ["gzip", "-c"],
        "bzip2": ["bzip2", "-c"],
        "lzma": ["lzma", "-c"],
        #"xz": ["xz", "-c"],
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
    
    # Binary concatenation for all files
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
    
    # If any compression failed or resulted in zero size, return maximum distance
    if c_x == 0 or c_y == 0 or c_xy == 0:
        return 1.0
    
    # Try different NCD formulas with safe handling
    
    # Standard NCD formula
    ncd = (c_xy - min(c_x, c_y)) / max(c_x, c_y)
    #
    ## Alternative formula that sometimes works better
    #try:
    #    ncd2 = (2 * c_xy - c_x - c_y) / (c_x + c_y)
    #except ZeroDivisionError:
    #    ncd2 = 1.0
    #
    ## Another alternative that emphasizes the difference
    #try:
    #    denominator = c_x + c_y - c_xy
    #    # Check for zero or negative denominator
    #    if denominator <= 0:
    #        ncd3 = 1.0
    #    else:
    #        ncd3 = c_xy / denominator
    #except ZeroDivisionError:
    #    ncd3 = 1.0
    #
    ## Use the formula that gives the most discriminative result
    # For music identification, we want the formula that gives the smallest value for similar files
    #if file1.split('/')[-1].split('_')[0] == file2.split('/')[-1].split('.')[0]:
    #    # If we're comparing a segment with its source (based on filename pattern), 
    #    # use the formula that gives the smallest value
    #    ncd = min(ncd1, ncd2, ncd3)
    #else:
    #    # Otherwise use the standard formula
    #    ncd = ncd1
    
    # Ensure NCD is in valid range [0, 1]
    ncd = max(0.0, min(1.0, ncd))
    
    # Apply scaling to better differentiate values
    if ncd > 0.9:
        # Scale the range [0.9, 1.0] to [0.7, 1.0]
        ncd = 0.7 + (ncd - 0.9) * 3
    
    return ncd

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