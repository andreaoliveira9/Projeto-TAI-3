#!/usr/bin/env python3
import argparse
import os
from audio_processing import extract_random_segment, add_noise
from feature_extraction import convert_to_frequencies
from ncd import calculate_ncd_with_database
from music_identification import identify_music


def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs("segments", exist_ok=True)
    os.makedirs("database", exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Music identification using NCD")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Extract segment command
    extract_parser = subparsers.add_parser(
        "extract", help="Extract random segment from music"
    )
    extract_parser.add_argument("music_file", help="Path to the music file")
    extract_parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=10.0,
        help="Duration of segment in seconds (default: 10)",
    )
    extract_parser.add_argument(
        "-o", "--output", help="Output filename (default: auto-generated)"
    )

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert audio file to frequency representation"
    )
    convert_parser.add_argument("audio_file", help="Path to the audio file")
    convert_parser.add_argument(
        "-o",
        "--output",
        help="Output filename (default: same as input with .freq extension)",
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare segment with database"
    )
    compare_parser.add_argument(
        "segment_file",
        help="Path to the segment file (audio or frequency representation)",
    )
    compare_parser.add_argument(
        "-c",
        "--compressor",
        default="gzip",
        choices=["gzip", "bzip2", "lzma", "zstd"],
        help="Compressor to use",
    )
    compare_parser.add_argument(
        "-n",
        "--num-results",
        type=int,
        default=5,
        help="Number of top candidates to display",
    )

    # Add noise command
    noise_parser = subparsers.add_parser("noise", help="Add noise to audio file")
    noise_parser.add_argument("audio_file", help="Path to the audio file")
    noise_parser.add_argument(
        "-l",
        "--level",
        type=float,
        default=0.1,
        help="Noise level (0.0-1.0) (default: 0.1), To use the other effects without any noise please put this to 0.0",
    )
    noise_parser.add_argument(
        "-o", "--output", help="Output filename (default: input_noisy.wav)"
    )
    noise_parser.add_argument(
        "--sox", action="store_true", help="Use SoX instead of librosa to add noise"
    )
    noise_parser.add_argument(
        "--type",
        choices=["whitenoise", "pinknoise"],
        default="whitenoise",
        help="Type of noise to add (default: whitenoise)",
    )
    noise_parser.add_argument("--reverb", action="store_true", help="Add reverb")
    noise_parser.add_argument("--eq", action="store_true", help="Apply EQ filter")
    noise_parser.add_argument(
        "--speed", type=float, help="Apply speed change (e.g., 1.1)"
    )
    noise_parser.add_argument(
        "--pitch", type=int, help="Apply pitch shift in cents (e.g., -200)"
    )

    # Process database command
    db_parser = subparsers.add_parser(
        "process_db", help="Process all music files in a directory to database"
    )
    db_parser.add_argument("directory", help="Directory containing music files")

    args = parser.parse_args()
    ensure_directories()

    if args.command == "extract":
        output = (
            args.output
            if args.output
            else f"segments/{os.path.basename(args.music_file).split('.')[0]}_{args.duration}s.wav"
        )
        extract_random_segment(args.music_file, output, args.duration)
        print(f"Extracted {args.duration}s segment to {output}")

    elif args.command == "convert":
        output = (
            args.output
            if args.output
            else f"{os.path.splitext(args.audio_file)[0]}.freq"
        )
        convert_to_frequencies(args.audio_file, output)
        print(f"Converted {args.audio_file} to frequency representation at {output}")

    elif args.command == "compare":
        # Check if the segment file is an audio file or already a frequency representation
        if not args.segment_file.endswith(".freq"):
            print(f"Converting {args.segment_file} to frequency representation...")
            temp_file = f"{os.path.splitext(args.segment_file)[0]}.freq"
            segment_file = convert_to_frequencies(args.segment_file, temp_file)
        else:
            segment_file = args.segment_file

        results = calculate_ncd_with_database(segment_file, args.compressor)
        top_candidates = identify_music(results, args.num_results)

        print(f"\nTop {args.num_results} candidates:")
        for i, (name, distance) in enumerate(top_candidates, 1):
            print(f"{i}. {name} - NCD: {distance:.4f}")

    elif args.command == "noise":
        output = (
            args.output
            if args.output
            else f"{os.path.splitext(args.audio_file)[0]}_noisy.wav"
        )
        add_noise(
            args.audio_file,
            output,
            noise_level=args.level,
            use_sox=args.sox,
            noise_type=args.type,
            add_reverb=args.reverb,
            apply_eq=args.eq,
            speed=args.speed,
            pitch=args.pitch,
        )
        print(
            f"Added {args.type} (level {args.level}) to {args.audio_file} using {'SoX' if args.sox else 'librosa'}, saved as {output}"
        )

    elif args.command == "process_db":
        from feature_extraction import process_directory

        process_directory(args.directory)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
