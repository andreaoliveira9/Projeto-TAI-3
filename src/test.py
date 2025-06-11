#!/usr/bin/env python3
import os
import argparse
import random
import shutil
import json
import traceback
from datetime import datetime
from audio_processing import extract_random_segment, add_noise
from feature_extraction import convert_to_frequencies
from ncd import calculate_ncd_with_database
from music_identification import identify_music, evaluate_compressor_performance

NF_VALUES = [3, 4, 10, 20, 40]
WS_VALUES = [1024, 2048, 4096, 8192, 16384]


def setup_test_environment(
    music_dir,
    num_segments=3,
    duration=10,
    noise_levels=[0.1, 0.4, 0.8],
    noise_types=["whitenoise"],
    use_sox=False,
    add_reverb=False,
    apply_eq=False,
    speed=None,
    pitch=None,
):
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
        "genres": {},  # Track genres for music files
    }

    # Find music files
    music_files = []
    for root, dirs, files in os.walk(music_dir):
        for filename in files:
            if filename.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
                full_path = os.path.join(root, filename)
                music_files.append(full_path)

                # Extract genre from directory structure
                genre = os.path.basename(os.path.dirname(full_path))
                base_name = os.path.splitext(filename)[0]
                test_files["music_files"].append(filename)
                test_files["genres"][base_name] = genre

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

            # Noise-only variants
            for noise_level in noise_levels:
                for noise_type in noise_types:
                    suffix = f"{noise_type}_{noise_level}"
                    noisy_file = os.path.join(
                        "segments", f"{base_name}_segment_{i}_{suffix}.wav"
                    )
                    print(
                        f"  Adding {noise_type} noise level {noise_level} to segment {i}..."
                    )
                    add_noise(
                        segment_file,
                        noisy_file,
                        noise_level=noise_level,
                        noise_type=noise_type,
                        use_sox=use_sox,
                    )

                    test_files["noisy_segments"].setdefault(suffix, []).append(
                        noisy_file
                    )

                    freq_file = os.path.join(
                        "test", f"{base_name}_segment_{i}_{suffix}.freq"
                    )
                    convert_to_frequencies(noisy_file, freq_file)
                    test_files["freq_files"].append(freq_file)

            # Pitch-only variant (clean, no noise)
            for pitch_shift in pitch:
                suffix = f"pitch_{pitch_shift}"
                pitch_file = os.path.join(
                    "segments", f"{base_name}_segment_{i}_{suffix}.wav"
                )
                print(
                    f"  Adding pitch shift {pitch_shift} to segment {i} (no noise)..."
                )
                add_noise(
                    segment_file,
                    pitch_file,
                    noise_level=0,
                    pitch=pitch_shift,
                    use_sox=use_sox,
                )

                test_files["noisy_segments"].setdefault(suffix, []).append(pitch_file)

                freq_file = os.path.join(
                    "test", f"{base_name}_segment_{i}_{suffix}.freq"
                )
                convert_to_frequencies(pitch_file, freq_file)
                test_files["freq_files"].append(freq_file)

            if add_reverb:
                # Reverb variant (clean, no noise)
                suffix = "reverb"
                reverb_file = os.path.join(
                    "segments", f"{base_name}_segment_{i}_{suffix}.wav"
                )
                print(f"  Adding reverb to segment {i} (no noise)...")
                add_noise(
                    segment_file,
                    reverb_file,
                    noise_level=0,
                    add_reverb=True,
                    use_sox=use_sox,
                )

                test_files["noisy_segments"].setdefault(suffix, []).append(reverb_file)

                freq_file = os.path.join(
                    "test", f"{base_name}_segment_{i}_{suffix}.freq"
                )
                convert_to_frequencies(reverb_file, freq_file)
                test_files["freq_files"].append(freq_file)

            if apply_eq:
                # EQ variant (clean, no noise)
                suffix = "eq"
                eq_file = os.path.join(
                    "segments", f"{base_name}_segment_{i}_{suffix}.wav"
                )
                print(f"  Adding EQ to segment {i} (no noise)...")
                add_noise(
                    segment_file, eq_file, noise_level=0, apply_eq=True, use_sox=use_sox
                )

                test_files["noisy_segments"].setdefault(suffix, []).append(eq_file)

                freq_file = os.path.join(
                    "test", f"{base_name}_segment_{i}_{suffix}.freq"
                )
                convert_to_frequencies(eq_file, freq_file)
                test_files["freq_files"].append(freq_file)

            for speed_val in speed:
                # Speed variant (clean, no noise)
                suffix = f"speed_{speed_val}"
                speed_file = os.path.join(
                    "segments", f"{base_name}_segment_{i}_{suffix}.wav"
                )
                print(f"  Adding speed change {speed_val} to segment {i} (no noise)...")
                add_noise(
                    segment_file,
                    speed_file,
                    noise_level=0,
                    speed=speed_val,
                    use_sox=use_sox,
                )

                test_files["noisy_segments"].setdefault(suffix, []).append(speed_file)

                freq_file = os.path.join(
                    "test", f"{base_name}_segment_{i}_{suffix}.freq"
                )
                convert_to_frequencies(speed_file, freq_file)
                test_files["freq_files"].append(freq_file)

            # Noise + pitch + speed combo
            suffix = "noise_0.4_pitch_speed"
            combo_file = os.path.join(
                "segments", f"{base_name}_segment_{i}_{suffix}.wav"
            )
            print(f"  Adding noise + pitch + speed to segment {i}...")
            add_noise(
                segment_file,
                combo_file,
                noise_level=0.4,
                pitch=-100,
                speed=1.1,
                use_sox=use_sox,
            )

            test_files["noisy_segments"].setdefault(suffix, []).append(combo_file)

            freq_file = os.path.join("test", f"{base_name}_segment_{i}_{suffix}.freq")
            convert_to_frequencies(combo_file, freq_file)
            test_files["freq_files"].append(freq_file)

            # Convert segment to frequency representation (default)
            freq_file = os.path.join("test", f"{base_name}_segment_{i}.freq")
            print(f"  Converting segment {i+1} to frequency representation...")
            convert_to_frequencies(segment_file, freq_file)
            test_files["freq_files"].append(freq_file)

            # Test different NF values (with default WS)
            for nf in NF_VALUES:
                freq_file_nf = os.path.join(
                    "test", f"{base_name}_segment_{i}_nf{nf}.freq"
                )
                print(f"    Converting segment {i+1} with NF={nf}...")
                convert_to_frequencies(segment_file, freq_file_nf, num_freqs=nf)
                test_files["freq_files"].append(freq_file_nf)

            # Test different WS values (with default NF)
            for ws in WS_VALUES:
                freq_file_ws = os.path.join(
                    "test", f"{base_name}_segment_{i}_ws{ws}.freq"
                )
                print(f"    Converting segment {i+1} with WS={ws}...")
                convert_to_frequencies(segment_file, freq_file_ws, frame_length=ws)
                test_files["freq_files"].append(freq_file_ws)

    return test_files


def initialize_results_file(output_file, parameters):
    """
    Initialize the JSON results file with the basic structure and test parameters.

    Args:
        output_file: Path to the output JSON file
        parameters: Dictionary with test parameters

    Returns:
        Dictionary with the initialized results structure
    """
    results = {
        "tests": [],
        "summary": {
            "total_tests": 0,
            "correct_identifications": 0,
            "by_compressor": {},
            "by_variant": {},
            "by_duration": {},
            "by_genre": {},  # Add genre summary
            "by_modification_type": {
                "noise": {},
                "pitch": {},
                "speed": {},
                "reverb": {},
                "eq": {},
                "clean": {"total": 0, "correct": 0, "errors": 0},
            },
            "compression_errors": {},
            "byNF": {},
            "byWS": {},
        },
        "parameters": parameters,
    }

    # Initialize compressor summaries
    for compressor in parameters["compressors"]:
        results["summary"]["by_compressor"][compressor] = {
            "total": 0,
            "correct": 0,
            "errors": 0,
        }
        results["summary"]["compression_errors"][compressor] = 0

    # Initialize NF and WS summaries
    for nf in NF_VALUES:
        results["summary"]["byNF"][str(nf)] = {"total": 0, "correct": 0, "errors": 0}
    for ws in WS_VALUES:
        results["summary"]["byWS"][str(ws)] = {"total": 0, "correct": 0, "errors": 0}

    # Write the initial structure to file
    with open(output_file, "w") as f:
        json.dump(results, f)

    return results


def update_results_file(output_file, results):
    """
    Update the JSON results file with the current results.

    Args:
        output_file: Path to the output JSON file
        results: Dictionary with current results
    """
    with open(output_file, "w") as f:
        json.dump(results, f)


def run_tests(compressors=None, output_file=None, genres_map=None):
    """
    Run tests on all frequency files in the test directory.

    Args:
        compressors: List of compressors to use (default: gzip, bzip2, xz, zstd)
        output_file: Path to the output JSON file for incremental writing
        genres_map: Dictionary mapping music names to their genres

    Returns:
        Dictionary with detailed test results
    """
    if compressors is None:
        compressors = ["gzip", "bzip2", "lzma", "zstd"]

    if genres_map is None:
        genres_map = {}

    # Find test frequency files
    test_files = [
        os.path.join("test", f) for f in os.listdir("test") if f.endswith(".freq")
    ]

    if not test_files:
        print("No test files found in test directory")
        return {}

    # Load existing results if output_file exists, otherwise create new results structure
    if output_file and os.path.exists(output_file):
        with open(output_file, "r") as f:
            results = json.load(f)
    else:
        # Results container
        results = {
            "tests": [],
            "summary": {
                "total_tests": 0,
                "correct_identifications": 0,
                "by_compressor": {},
                "by_variant": {},
                "by_duration": {},
                "by_genre": {},  # Add genre summary
                "by_modification_type": {
                    "noise": {},
                    "pitch": {},
                    "speed": {},
                    "reverb": {},
                    "eq": {},
                    "clean": {"total": 0, "correct": 0, "errors": 0},
                },
                "compression_errors": {},
                "byNF": {},
                "byWS": {},
            },
        }

        # Inicializar os summaries de NF e WS
        for nf in NF_VALUES:
            results["summary"]["byNF"][str(nf)] = {
                "total": 0,
                "correct": 0,
                "errors": 0,
            }
        for ws in WS_VALUES:
            results["summary"]["byWS"][str(ws)] = {
                "total": 0,
                "correct": 0,
                "errors": 0,
            }

        # Initialize summary counters
        for compressor in compressors:
            results["summary"]["by_compressor"][compressor] = {
                "total": 0,
                "correct": 0,
                "errors": 0,
            }
            results["summary"]["compression_errors"][compressor] = 0

    # Test each frequency file with each compressor
    for test_file in test_files:
        filename = os.path.basename(test_file)
        print(f"\nTesting {filename}:")

        # Extract metadata from filename
        test_file_components = filename.split("_")
        music_name = test_file_components[0]

        # Get genre for this music file
        genre = genres_map.get(music_name, "unknown")

        # Initialize genre in summary if not already there
        if genre not in results["summary"]["by_genre"]:
            results["summary"]["by_genre"][genre] = {
                "total": 0,
                "correct": 0,
                "errors": 0,
            }

        # Detect NF and WS from filename
        nf_value = None
        ws_value = None
        if "_nf" in filename:
            try:
                nf_value = int(filename.split("_nf")[-1].replace(".freq", ""))
            except Exception:
                nf_value = None
        if "_ws" in filename:
            try:
                ws_value = int(filename.split("_ws")[-1].replace(".freq", ""))
            except Exception:
                ws_value = None

        # Determine if this is a modified segment and what kind of modification
        variant = "clean"
        modification_type = "clean"
        modification_value = None
        duration = 10.0  # Default

        for comp in test_file_components:
            if comp.startswith("segment"):
                try:
                    segment_idx = int(comp.split("_")[-1].replace(".freq", ""))
                except (ValueError, IndexError):
                    segment_idx = 0

            # Check for different types of modifications
            if (
                "noise" in filename
                or "pitch" in filename
                or "speed" in filename
                or "reverb" in filename
                or "eq" in filename
            ):
                variant = filename.replace(".freq", "").split("segment_")[-1]

                # Determine the modification type and value
                if "noise" in variant:
                    modification_type = "noise"
                    try:
                        # Extract noise level if present (e.g., noise_0.4)
                        if "noise_" in filename:
                            noise_val = variant.split("noise_")[1].split("_")[0]
                            modification_value = float(noise_val)
                    except (ValueError, IndexError):
                        modification_value = None
                elif "pitch" in variant:
                    modification_type = "pitch"
                    try:
                        # Extract pitch value if present (e.g., pitch_-100)
                        if "pitch_" in variant:
                            pitch_val = variant.split("pitch_")[1].split("_")[0]
                            modification_value = float(pitch_val)
                    except (ValueError, IndexError):
                        modification_value = None
                elif "speed" in variant:
                    modification_type = "speed"
                    try:
                        # Extract speed value if present (e.g., speed_1.1)
                        if "speed_" in variant:
                            speed_val = variant.split("speed_")[1].split("_")[0]
                            modification_value = float(speed_val)
                    except (ValueError, IndexError):
                        modification_value = None
                elif "reverb" in variant:
                    modification_type = "reverb"
                elif "eq" in variant:
                    modification_type = "eq"
            elif comp.endswith("s.freq"):
                try:
                    duration = float(comp.replace("s.freq", ""))
                except (ValueError, IndexError):
                    pass

        # Initialize the modification type counter if needed
        if modification_type != "clean":
            mod_value_key = (
                str(modification_value) if modification_value is not None else "default"
            )
            if (
                mod_value_key
                not in results["summary"]["by_modification_type"][modification_type]
            ):
                results["summary"]["by_modification_type"][modification_type][
                    mod_value_key
                ] = {
                    "total": 0,
                    "correct": 0,
                    "errors": 0,
                }

        if variant not in results["summary"]["by_variant"]:
            results["summary"]["by_variant"][variant] = {
                "total": 0,
                "correct": 0,
                "errors": 0,
            }

        # Update duration counters if needed
        if str(duration) not in results["summary"]["by_duration"]:
            results["summary"]["by_duration"][str(duration)] = {
                "total": 0,
                "correct": 0,
                "errors": 0,
            }

        for compressor in compressors:
            print(f"\nUsing compressor: {compressor}")

            # Store detailed test result structure
            test_result = {
                "file": filename,
                "actual_name": music_name,
                "genre": genre,
                "compressor": compressor,
                "variant": variant,
                "modification_type": modification_type,
                "modification_value": modification_value,
                "duration": duration,
                "top_matches": [],
                "correct": False,
                "error": None,
            }

            try:
                ncd_results = calculate_ncd_with_database(test_file, compressor)

                # Get top matches
                top_matches = identify_music(ncd_results, 3)

                print(f"Top 3 matches:")
                for i, (name, distance) in enumerate(top_matches, 1):
                    print(f"  {i}. {name} - NCD: {distance:.4f}")

                # Update test result
                test_result["top_matches"] = [
                    {"name": name, "distance": distance}
                    for name, distance in top_matches
                ]

                # Check if correct
                actual_name = music_name
                predicted_name = top_matches[0][0] if top_matches else None
                is_correct = actual_name == predicted_name
                test_result["correct"] = is_correct

                if is_correct:
                    print(f"✓ Correct identification!")
                else:
                    print(
                        f"✗ Incorrect identification. Expected: {actual_name}, Got: {predicted_name}"
                    )

                # Update summary counters
                results["summary"]["total_tests"] += 1
                results["summary"]["by_compressor"][compressor]["total"] += 1
                results["summary"]["by_variant"][variant]["total"] += 1
                results["summary"]["by_duration"][str(duration)]["total"] += 1
                results["summary"]["by_genre"][genre]["total"] += 1

                # Update modification type counter
                if modification_type == "clean":
                    results["summary"]["by_modification_type"]["clean"]["total"] += 1
                else:
                    mod_value_key = (
                        str(modification_value)
                        if modification_value is not None
                        else "default"
                    )
                    results["summary"]["by_modification_type"][modification_type][
                        mod_value_key
                    ]["total"] += 1

                # Atualizar byNF/byWS
                if nf_value is not None and str(nf_value) in results["summary"]["byNF"]:
                    results["summary"]["byNF"][str(nf_value)]["total"] += 1
                if ws_value is not None and str(ws_value) in results["summary"]["byWS"]:
                    results["summary"]["byWS"][str(ws_value)]["total"] += 1

                if is_correct:
                    results["summary"]["correct_identifications"] += 1
                    results["summary"]["by_compressor"][compressor]["correct"] += 1
                    results["summary"]["by_variant"][variant]["correct"] += 1
                    results["summary"]["by_duration"][str(duration)]["correct"] += 1
                    results["summary"]["by_genre"][genre]["correct"] += 1

                    # Update modification type counter for correct identifications
                    if modification_type == "clean":
                        results["summary"]["by_modification_type"]["clean"][
                            "correct"
                        ] += 1
                    else:
                        mod_value_key = (
                            str(modification_value)
                            if modification_value is not None
                            else "default"
                        )
                        results["summary"]["by_modification_type"][modification_type][
                            mod_value_key
                        ]["correct"] += 1

                    if (
                        nf_value is not None
                        and str(nf_value) in results["summary"]["byNF"]
                    ):
                        results["summary"]["byNF"][str(nf_value)]["correct"] += 1
                    if (
                        ws_value is not None
                        and str(ws_value) in results["summary"]["byWS"]
                    ):
                        results["summary"]["byWS"][str(ws_value)]["correct"] += 1

            except Exception as e:
                # Handle errors during testing
                error_msg = str(e)
                traceback_str = traceback.format_exc()
                print(f"Error during testing with {compressor}: {error_msg}")

                # Update test result with error information
                test_result["error"] = {
                    "message": error_msg,
                    "traceback": traceback_str,
                }

                # Update error counters
                results["summary"]["compression_errors"][compressor] += 1
                results["summary"]["by_compressor"][compressor]["errors"] += 1
                results["summary"]["by_variant"][variant]["errors"] += 1
                results["summary"]["by_duration"][str(duration)]["errors"] += 1
                results["summary"]["by_genre"][genre]["errors"] += 1

                # Update modification type error counter
                if modification_type == "clean":
                    results["summary"]["by_modification_type"]["clean"]["errors"] += 1
                else:
                    mod_value_key = (
                        str(modification_value)
                        if modification_value is not None
                        else "default"
                    )
                    results["summary"]["by_modification_type"][modification_type][
                        mod_value_key
                    ]["errors"] += 1

                if nf_value is not None and str(nf_value) in results["summary"]["byNF"]:
                    results["summary"]["byNF"][str(nf_value)]["errors"] += 1
                if ws_value is not None and str(ws_value) in results["summary"]["byWS"]:
                    results["summary"]["byWS"][str(ws_value)]["errors"] += 1

            # Add test result to collection
            results["tests"].append(test_result)

            # Write results incrementally to file
            if output_file:
                update_results_file(output_file, results)

    # Calculate percentages for summary
    if results["summary"]["total_tests"] > 0:
        results["summary"]["accuracy"] = (
            results["summary"]["correct_identifications"]
            / results["summary"]["total_tests"]
        )
    else:
        results["summary"]["accuracy"] = 0

    for compressor in compressors:
        comp_data = results["summary"]["by_compressor"][compressor]
        if comp_data["total"] > 0:
            comp_data["accuracy"] = comp_data["correct"] / comp_data["total"]
        else:
            comp_data["accuracy"] = 0

    for variant in results["summary"]["by_variant"]:
        var_data = results["summary"]["by_variant"][variant]
        var_data["accuracy"] = (
            var_data["correct"] / var_data["total"] if var_data["total"] > 0 else 0
        )

    for duration in results["summary"]["by_duration"]:
        duration_data = results["summary"]["by_duration"][duration]
        if duration_data["total"] > 0:
            duration_data["accuracy"] = (
                duration_data["correct"] / duration_data["total"]
            )
        else:
            duration_data["accuracy"] = 0

    # Calculate accuracy for genre statistics
    for genre in results["summary"]["by_genre"]:
        genre_data = results["summary"]["by_genre"][genre]
        if genre_data["total"] > 0:
            genre_data["accuracy"] = genre_data["correct"] / genre_data["total"]
        else:
            genre_data["accuracy"] = 0

    # Calculate accuracy for modification type statistics
    for mod_type, values in results["summary"]["by_modification_type"].items():
        if mod_type == "clean":
            if values["total"] > 0:
                values["accuracy"] = values["correct"] / values["total"]
            else:
                values["accuracy"] = 0
        else:
            for mod_value, data in values.items():
                if data["total"] > 0:
                    data["accuracy"] = data["correct"] / data["total"]
                else:
                    data["accuracy"] = 0

    # Calcular accuracy para byNF e byWS
    for nf in results["summary"]["byNF"]:
        nf_data = results["summary"]["byNF"][nf]
        if nf_data["total"] > 0:
            nf_data["accuracy"] = nf_data["correct"] / nf_data["total"]
        else:
            nf_data["accuracy"] = 0
    for ws in results["summary"]["byWS"]:
        ws_data = results["summary"]["byWS"][ws]
        if ws_data["total"] > 0:
            ws_data["accuracy"] = ws_data["correct"] / ws_data["total"]
        else:
            ws_data["accuracy"] = 0

    # Write final results to file
    if output_file:
        update_results_file(output_file, results)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run a complete test of the music identification system"
    )
    parser.add_argument("music_dir", help="Directory containing music files")
    parser.add_argument(
        "--segments",
        type=int,
        default=3,
        help="Number of segments to extract per file (default: 3)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Duration of segments in seconds (default: 10)",
    )
    parser.add_argument(
        "--noise-levels",
        type=float,
        nargs="+",
        default=[0.0, 0.1, 0.2],
        help="Noise levels to test (default: 0.0 0.1 0.2)",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip setup and use existing test files",
    )
    parser.add_argument(
        "--compressors",
        nargs="+",
        default=["gzip", "bzip2", "lzma", "zstd"],
        help="Compressors to test (default: gzip bzip2 xz zstd)",
    )
    parser.add_argument(
        "--output",
        help="JSON file to save results (default: test_results_TIMESTAMP.json)",
    )
    parser.add_argument(
        "--sox", action="store_true", help="Use SoX instead of librosa to add noise"
    )
    parser.add_argument(
        "--noise-types",
        choices=["whitenoise", "pinknoise"],
        nargs="+",
        default=["whitenoise"],
        help="Noise types to test (e.g., whitenoise or/and pinknoise)",
    )
    parser.add_argument("--reverb", action="store_true", help="Apply reverb in SoX")
    parser.add_argument("--eq", action="store_true", help="Apply EQ filter in SoX")
    parser.add_argument(
        "--speed",
        type=float,
        nargs="+",
        default=[],
        help="Speed change factors (e.g., 0.9 for 10% slower, 1.1 for 10% faster, default: no speed change)",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        nargs="+",
        default=[-100],
        help="Pitch shift in cents (e.g., -100 for 1 semitone down, default: -100)",
    )

    args = parser.parse_args()

    # Create output filename if not provided
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output if args.output else f"test_results_{timestamp}.json"

    # Create test parameters dictionary
    test_parameters = {
        "music_dir": args.music_dir,
        "segments_per_file": args.segments,
        "duration": args.duration,
        "noise_levels": args.noise_levels,
        "compressors": args.compressors,
        "sox_used": args.sox,
        "noise_types": args.noise_types,
        "reverb": args.reverb,
        "eq": args.eq,
        "speed": args.speed,
        "pitch": args.pitch,
        "timestamp": timestamp,
    }

    # Initialize results file
    initialize_results_file(output_file, test_parameters)

    genres_map = {}  # To store mapping of music names to genres

    if not args.skip_setup:
        test_files = setup_test_environment(
            args.music_dir,
            num_segments=args.segments,
            duration=args.duration,
            noise_levels=args.noise_levels,
            use_sox=args.sox,
            noise_types=args.noise_types,
            add_reverb=args.reverb,
            apply_eq=args.eq,
            speed=args.speed,
            pitch=args.pitch,
        )

        # Store the genres mapping for use in run_tests
        genres_map = test_files.get("genres", {})

        print(f"\nSetup complete:")
        print(f"- {len(test_files['music_files'])} music files processed")
        print(f"- {len(test_files['segments'])} segments extracted")
        print(
            f"- {sum(len(files) for files in test_files['noisy_segments'].values())} noisy segments created"
        )
        print(f"- {len(test_files['freq_files'])} frequency files generated")
        print(f"- {len(test_files['database_files'])} database files created")
    else:
        # If skipping setup, try to extract genre information from the directory structure
        music_dir = args.music_dir
        for genre_dir in os.listdir(music_dir):
            genre_path = os.path.join(music_dir, genre_dir)
            if os.path.isdir(genre_path):
                for filename in os.listdir(genre_path):
                    if filename.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
                        base_name = os.path.splitext(filename)[0]
                        genres_map[base_name] = genre_dir

    # Run the tests and get detailed results - pass the output file for incremental writing
    detailed_results = run_tests(args.compressors, output_file, genres_map)

    print(f"\nDetailed results saved to {output_file}")


if __name__ == "__main__":
    main()
