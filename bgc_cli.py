#!/usr/bin/env python3
"""
Command-line interface for BGC (Boolean Gate Count) S-box optimization.

This script provides a user-friendly interface to the BGC optimizer,
allowing optimization of S-box implementations with minimal Boolean gate count.
"""

import argparse
import json
import sys
import os
from typing import List, Dict, Any

from solver import BGCOptimizer, setup_logging


def parse_sbox_input(sbox_str: str) -> List[int]:
    """Parse S-box input from string."""
    try:
        # Try JSON format first
        if sbox_str.startswith("[") and sbox_str.endswith("]"):
            return json.loads(sbox_str)

        # Try comma-separated format
        return [int(x.strip()) for x in sbox_str.split(",")]
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid S-box format: {e}")


def load_sbox_from_file(file_path: str) -> tuple:
    """Load S-box from JSON file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        sbox = data.get("sbox", data.get("s_box", data.get("values")))
        if not sbox:
            raise ValueError("No S-box data found in file")

        bit_num = data.get("bit_num", data.get("bit_width", data.get("bits")))
        name = data.get("name", os.path.splitext(os.path.basename(file_path))[0])

        return sbox, bit_num, name
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Error loading S-box file: {e}")


def format_results_json(results: Dict[str, Any]) -> str:
    """Format results as JSON."""
    formatted_results = {
        "summary": {
            "total_attempts": results["total_attempts"],
            "satisfiable_solutions": results["satisfiable_solutions"],
            "success": results["best_solution"] is not None,
        }
    }

    if results["best_solution"]:
        best = results["best_solution"]
        formatted_results["best_solution"] = {
            "gate_count": best.gate_count,
            "depth": best.depth,
            "structure": best.structure,
            "execution_time": best.execution_time,
            "circuit_file": best.circuit_file,
        }

    if results["all_solutions"]:
        formatted_results["all_solutions"] = []
        for sol in results["all_solutions"]:
            if sol.satisfiable:
                formatted_results["all_solutions"].append(
                    {
                        "gate_count": sol.gate_count,
                        "depth": sol.depth,
                        "structure": sol.structure,
                        "execution_time": sol.execution_time,
                    }
                )

    return json.dumps(formatted_results, indent=2)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="BGC S-box optimization tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python bgc_cli.py --sbox "4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10" --bit-num 4 --max-gates 20

  # Find all solutions
  python bgc_cli.py --sbox "4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10" --bit-num 4 --max-gates 15 --find-all

  # Use serial mode (one gate per depth)
  python bgc_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 10 --serial

  # Load from file
  python bgc_cli.py --sbox-file sbox.json --max-gates 20

  # JSON output
  python bgc_cli.py --sbox "4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10" --bit-num 4 --json-output
        """,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--sbox", type=str, help="S-box values as comma-separated or JSON array"
    )
    input_group.add_argument(
        "--sbox-file", type=str, help="File containing S-box values (JSON format)"
    )

    parser.add_argument(
        "--bit-num",
        type=int,
        help="Number of input/output bits (required if using --sbox)",
    )

    # Optimization parameters
    parser.add_argument(
        "--max-gates",
        type=int,
        default=20,
        help="Maximum number of gates (default: 20)",
    )

    parser.add_argument(
        "--max-depth", type=int, default=5, help="Maximum circuit depth (default: 5)"
    )

    # Search strategy
    parser.add_argument(
        "--find-all",
        action="store_true",
        help="Find all solutions, not just the first one",
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Use parallel circuit structure optimization",
    )

    parser.add_argument(
        "--serial",
        action="store_true",
        help="Use serial mode (one gate per depth level)",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output_bgc",
        help="Output directory (default: ./output_bgc)",
    )

    parser.add_argument(
        "--name", type=str, default="sbox", help="Name for output files (default: sbox)"
    )

    parser.add_argument(
        "--json-output", action="store_true", help="Output results in JSON format"
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    # Solver options
    parser.add_argument(
        "--stp-path",
        type=str,
        default="stp",
        help="Path to STP executable (default: stp)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Solver timeout in seconds (default: 30000)",
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=20,
        help="Number of threads for STP solver (default: 20)",
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-file", type=str, help="Log file path (default: console only)"
    )

    args = parser.parse_args()

    # Setup logging
    if not args.quiet:
        setup_logging(args.log_level, args.log_file)

    try:
        # Parse input
        if args.sbox_file:
            sbox, bit_num, name = load_sbox_from_file(args.sbox_file)
            if not args.name or args.name == "sbox":
                args.name = name
        else:
            if not args.bit_num:
                parser.error("--bit-num is required when using --sbox")
            sbox = parse_sbox_input(args.sbox)
            bit_num = args.bit_num

        # Validate bit number
        expected_size = 2**bit_num
        if len(sbox) != expected_size:
            raise ValueError(
                f"S-box size {len(sbox)} doesn't match {bit_num}-bit S-box (expected {expected_size})"
            )

        # Initialize optimizer
        optimizer = BGCOptimizer(
            bit_num=bit_num,
            stp_path=args.stp_path,
            log_level=args.log_level if not args.quiet else "ERROR",
            threads=args.threads,
            timeout=args.timeout,
        )

        # Run optimization
        if args.serial:
            results = optimizer.optimize_sbox_serial(
                sbox=sbox,
                max_gates=args.max_gates,
                output_dir=args.output_dir,
                cipher_name=args.name,
                stop_on_first=not args.find_all,
            )
        else:
            results = optimizer.optimize_sbox(
                sbox=sbox,
                max_gates=args.max_gates,
                max_depth=args.max_depth,
                output_dir=args.output_dir,
                cipher_name=args.name,
                parallel=args.parallel,
                stop_on_first=not args.find_all,
            )

        # Output results
        if args.json_output:
            print(format_results_json(results))
        else:
            if not args.quiet:
                optimizer.analyze_results(results)

            if results["best_solution"]:
                if args.quiet:
                    best = results["best_solution"]
                    print(
                        f"SUCCESS: {best.gate_count} gates, depth {best.depth}, structure {best.structure}"
                    )
                else:
                    print("✓ Optimization completed successfully!")
            else:
                if args.quiet:
                    print("FAILED: No solution found")
                else:
                    print("✗ No solution found within constraints")
                sys.exit(1)

    except Exception as e:
        if args.json_output:
            error_result = {"error": str(e), "success": False}
            print(json.dumps(error_result, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
