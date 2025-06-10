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
    }

    # Find music files
    music_files = []
    for filename in os.listdir(music_dir):
        if filename.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
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

            # Noise-only variants
            for noise_level in [0.1, 0.4, 0.8]:
                suffix = f"noise_{noise_level}"
                noisy_file = os.path.join(
                    "segments", f"{base_name}_segment_{i}_{suffix}.wav"
                )
                print(f"  Adding noise level {noise_level} to segment {i}...")
                add_noise(
                    segment_file, noisy_file, noise_level=noise_level, use_sox=use_sox
                )

                test_files["noisy_segments"].setdefault(suffix, []).append(noisy_file)

                freq_file = os.path.join(
                    "test", f"{base_name}_segment_{i}_{suffix}.freq"
                )
                convert_to_frequencies(noisy_file, freq_file)
                test_files["freq_files"].append(freq_file)

            # Pitch-only variant (clean, no noise)
            suffix = "pitch_only"
            pitch_file = os.path.join(
                "segments", f"{base_name}_segment_{i}_{suffix}.wav"
            )
            print(f"  Adding pitch shift to segment {i} (no noise)...")
            add_noise(
                segment_file, pitch_file, noise_level=0, pitch=-100, use_sox=use_sox
            )

            test_files["noisy_segments"].setdefault(suffix, []).append(pitch_file)

            freq_file = os.path.join("test", f"{base_name}_segment_{i}_{suffix}.freq")
            convert_to_frequencies(pitch_file, freq_file)
            test_files["freq_files"].append(freq_file)

            # Speed-only variant (clean, no noise)
            suffix = "speed_only"
            speed_file = os.path.join(
                "segments", f"{base_name}_segment_{i}_{suffix}.wav"
            )
            print(f"  Adding speed change to segment {i} (no noise)...")
            add_noise(
                segment_file, speed_file, noise_level=0, speed=1.1, use_sox=use_sox
            )

            test_files["noisy_segments"].setdefault(suffix, []).append(speed_file)

            freq_file = os.path.join("test", f"{base_name}_segment_{i}_{suffix}.freq")
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


def run_tests(compressors=None):
    """
    Run tests on all frequency files in the test directory.

    Args:
        compressors: List of compressors to use (default: gzip, bzip2, xz, zstd)

    Returns:
        Dictionary with detailed test results
    """
    if compressors is None:
        compressors = ["gzip", "bzip2", "lzma", "zstd"]

    # Find test frequency files
    test_files = [
        os.path.join("test", f) for f in os.listdir("test") if f.endswith(".freq")
    ]

    if not test_files:
        print("No test files found in test directory")
        return {}

    # Results container
    results = {
        "tests": [],
        "summary": {
            "total_tests": 0,
            "correct_identifications": 0,
            "by_compressor": {},
            "by_variant": {},
            "by_duration": {},
            "compression_errors": {},
            "byNF": {},
            "byWS": {},
        },
    }

    # Inicializar os summaries de NF e WS
    for nf in NF_VALUES:
        results["summary"]["byNF"][str(nf)] = {"total": 0, "correct": 0, "errors": 0}
    for ws in WS_VALUES:
        results["summary"]["byWS"][str(ws)] = {"total": 0, "correct": 0, "errors": 0}

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

        # Determine if this is a noisy segment
        variant = "clean"
        duration = 10.0  # Default

        for comp in test_file_components:
            if comp.startswith("segment"):
                try:
                    segment_idx = int(comp.split("_")[-1].replace(".freq", ""))
                except (ValueError, IndexError):
                    segment_idx = 0
            if "noise" in filename or "pitch" in filename or "speed" in filename:
                variant = filename.replace(".freq", "").split("segment_")[-1]
            elif comp.endswith("s.freq"):
                try:
                    duration = float(comp.replace("s.freq", ""))
                except (ValueError, IndexError):
                    pass

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
                "compressor": compressor,
                "variant": variant,
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
                if nf_value is not None and str(nf_value) in results["summary"]["byNF"]:
                    results["summary"]["byNF"][str(nf_value)]["errors"] += 1
                if ws_value is not None and str(ws_value) in results["summary"]["byWS"]:
                    results["summary"]["byWS"][str(ws_value)]["errors"] += 1

            # Add test result to collection
            results["tests"].append(test_result)

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
        "--speed", type=float, help="Speed factor (e.g., 1.1 for 10%% faster)"
    )
    parser.add_argument(
        "--pitch", type=int, help="Pitch shift in cents (e.g., -200 to lower pitch)"
    )

    args = parser.parse_args()

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

        print(f"\nSetup complete:")
        print(f"- {len(test_files['music_files'])} music files processed")
        print(f"- {len(test_files['segments'])} segments extracted")
        print(
            f"- {sum(len(files) for files in test_files['noisy_segments'].values())} noisy segments created"
        )
        print(f"- {len(test_files['freq_files'])} frequency files generated")
        print(f"- {len(test_files['database_files'])} database files created")

    # Run the tests and get detailed results
    detailed_results = run_tests(args.compressors)

    # Evaluate performance for each compressor (original functionality)
    print("\n--- Evaluating compressor performance ---")
    evaluation_results = evaluate_compressor_performance("test", args.compressors)

    # Add evaluation results to the detailed results
    detailed_results["evaluation"] = {}
    for compressor in args.compressors:
        detailed_results["evaluation"][compressor] = {
            "correct": evaluation_results[compressor]["correct"],
            "total": evaluation_results[compressor]["total"],
            "accuracy": evaluation_results[compressor]["accuracy"],
        }

    # Print summary (original functionality)
    print("\nSummary:")
    for compressor in args.compressors:
        correct = evaluation_results[compressor]["correct"]
        total = evaluation_results[compressor]["total"]
        accuracy = evaluation_results[compressor]["accuracy"]
        print(f"{compressor}: {correct}/{total} correct ({accuracy:.2%} accuracy)")

    # Save results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = args.output if args.output else f"test_results_{timestamp}.json"

    # Add test parameters to results
    detailed_results["parameters"] = {
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

    # Print error summary if any errors occurred
    if "compression_errors" in detailed_results["summary"]:
        print("\nCompression Error Summary:")
        for compressor, count in detailed_results["summary"][
            "compression_errors"
        ].items():
            if count > 0:
                print(f"  {compressor}: {count} errors")

    with open(output_file, "w") as f:
        json.dump(detailed_results, f, indent=2)

    print(f"\nDetailed results saved to {output_file}")


if __name__ == "__main__":
    main()
