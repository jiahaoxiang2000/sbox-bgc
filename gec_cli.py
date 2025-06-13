#!/usr/bin/env python3
"""
Command-line interface for GEC S-box optimization.
"""

import argparse
import json
import sys
import os
from typing import List, Optional

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gec_solver import GECOptimizer, setup_logging


def parse_sbox(sbox_str: str) -> List[int]:
    """
    Parse S-box from string representation.

    Args:
        sbox_str: S-box as comma-separated values or JSON array

    Returns:
        List of S-box values
    """
    try:
        # Try JSON format first
        return json.loads(sbox_str)
    except json.JSONDecodeError:
        # Try comma-separated format
        try:
            return [int(x.strip(), 0) for x in sbox_str.split(",")]
        except ValueError:
            raise ValueError(f"Invalid S-box format: {sbox_str}")


def parse_gate_list(gate_str: str) -> List[str]:
    """
    Parse gate list from string.

    Args:
        gate_str: Comma-separated gate names

    Returns:
        List of gate names
    """
    return [gate.strip().upper() for gate in gate_str.split(",")]


def main():
    """Main CLI function."""

    parser = argparse.ArgumentParser(
        description="GEC S-box Optimization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize a simple 3-bit S-box (stops on first solution)
  python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6

  # Find all solutions, not just the first one
  python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6 --find-all

  # Find all solutions for exactly 4 gates
  python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --exact-gates 4

  # Explore all structures for each gate count
  python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --explore-all-structures

  # Use specific technology and gates
  python gec_cli.py --sbox "[0,1,3,6,7,4,5,2]" --bit-num 3 --technology 1 --gates "XOR,AND,OR"

  # Load S-box from file
  python gec_cli.py --sbox-file sbox.json --bit-num 3 --max-gec 50

Supported gates: XOR, XNOR, AND, NAND, OR, NOR, NOT, XOR3, XNOR3, AND3, NAND3, OR3, NOR3, MAOI1, MOAI1
Technologies: 0=UMC 180nm, 1=SMIC 130nm
        """,
    )

    # S-box input
    sbox_group = parser.add_mutually_exclusive_group(required=True)
    sbox_group.add_argument(
        "--sbox", type=str, help="S-box values as comma-separated or JSON array"
    )
    sbox_group.add_argument(
        "--sbox-file", type=str, help="File containing S-box values (JSON format)"
    )

    # S-box parameters
    parser.add_argument(
        "--bit-num", type=int, required=True, help="Number of input/output bits"
    )

    # Optimization parameters
    parser.add_argument(
        "--max-gates", type=int, default=6, help="Maximum number of gates (default: 6)"
    )
    parser.add_argument(
        "--max-gec", type=int, default=40, help="Maximum GEC value (default: 40)"
    )
    parser.add_argument(
        "--technology",
        type=int,
        choices=[0, 1],
        default=0,
        help="Technology: 0=UMC 180nm, 1=SMIC 130nm (default: 0)",
    )
    parser.add_argument(
        "--gates", type=str, help="Comma-separated list of allowed gates"
    )

    # Search strategy options
    parser.add_argument(
        "--find-all",
        action="store_true",
        help="Find all solutions, not just the first one",
    )
    parser.add_argument(
        "--explore-all-structures",
        action="store_true",
        help="Test all depth structures for each gate count",
    )
    parser.add_argument(
        "--exact-gates", type=int, help="Find all solutions for exactly this many gates"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./gec_output",
        help="Output directory (default: ./gec_output)",
    )
    parser.add_argument(
        "--name", type=str, default="sbox", help="Name for output files (default: sbox)"
    )

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
        default=300,
        help="Solver timeout in seconds (default: 300)",
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file", type=str, help="Log file path (default: console only)"
    )

    # Output format
    parser.add_argument(
        "--json-output", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    # Setup logging
    if args.quiet:
        log_level = "WARNING"
    else:
        log_level = args.log_level

    logger = setup_logging(log_level, args.log_file)

    try:
        # Parse S-box
        if args.sbox:
            sbox = parse_sbox(args.sbox)
        else:
            with open(args.sbox_file, "r") as f:
                sbox_data = json.load(f)
                if isinstance(sbox_data, list):
                    sbox = sbox_data
                else:
                    sbox = sbox_data.get("sbox", sbox_data.get("values"))
                    if sbox is None:
                        raise ValueError("Could not find S-box values in file")

        logger.info(f"Loaded S-box: {sbox}")

        # Validate bit number
        expected_size = 2**args.bit_num
        if len(sbox) != expected_size:
            logger.error(
                f"S-box size {len(sbox)} doesn't match bit number {args.bit_num} (expected {expected_size})"
            )
            return 1

        # Parse gate list
        gate_list = None
        if args.gates:
            gate_list = parse_gate_list(args.gates)
            logger.info(f"Using gates: {gate_list}")

        # Initialize optimizer
        optimizer = GECOptimizer(
            bit_num=args.bit_num, stp_path=args.stp_path, log_level=log_level
        )
        optimizer.stp_solver.timeout = args.timeout

        # Run optimization
        logger.info("Starting optimization...")

        if args.exact_gates:
            # Find all solutions for exact gate count
            logger.info(f"Finding all solutions for exactly {args.exact_gates} gates")
            results = optimizer.find_all_solutions_for_gates(
                sbox=sbox,
                gate_num=args.exact_gates,
                max_gec=args.max_gec,
                technology=args.technology,
                gate_list=gate_list,
                output_dir=args.output_dir,
                cipher_name=args.name,
            )
        elif args.find_all or args.explore_all_structures:
            # Use exhaustive search
            results = optimizer.optimize_sbox_exhaustive(
                sbox=sbox,
                max_gates=args.max_gates,
                max_gec=args.max_gec,
                technology=args.technology,
                gate_list=gate_list,
                output_dir=args.output_dir,
                cipher_name=args.name,
                stop_on_first=not args.find_all,
                explore_all_structures=args.explore_all_structures,
            )
        else:
            # Use standard optimization (stops on first solution)
            results = optimizer.optimize_sbox(
                sbox=sbox,
                max_gates=args.max_gates,
                max_gec=args.max_gec,
                technology=args.technology,
                gate_list=gate_list,
                output_dir=args.output_dir,
                cipher_name=args.name,
            )

        # Output results
        if args.json_output:
            # Convert non-serializable objects
            if args.exact_gates:
                # Results from find_all_solutions_for_gates
                json_results = {
                    "gate_num": results["gate_num"],
                    "sbox": results["sbox"],
                    "cipher_name": results["cipher_name"],
                    "technology": results["technology"],
                    "max_gec": results["max_gec"],
                    "gate_list": results["gate_list"],
                    "total_structures_tested": results["total_structures_tested"],
                    "satisfiable_solutions": results["satisfiable_solutions"],
                    "solutions": results["solutions"],
                }
            else:
                # Results from optimize_sbox or optimize_sbox_exhaustive
                json_results = {
                    "sbox": results["sbox"],
                    "cipher_name": results["cipher_name"],
                    "technology": results["technology"],
                    "max_gates": results.get("max_gates"),
                    "max_gec": results.get("max_gec"),
                    "gate_list": results["gate_list"],
                    "total_attempts": len(results["results"]),
                    "satisfiable_solutions": sum(
                        1 for r in results["results"] if r["satisfiable"]
                    ),
                    "best_solution": results["best_solution"],
                    "search_strategy": results.get("search_strategy"),
                    "all_solutions": results.get("all_solutions", []),
                }
            print(json.dumps(json_results, indent=2))
        else:
            if args.exact_gates:
                # Display results for exact gate count
                print(f"\n=== Results for {results['gate_num']} Gates ===")
                print(f"Structures tested: {results['total_structures_tested']}")
                print(f"Solutions found: {results['satisfiable_solutions']}")

                if results["solutions"]:
                    print("\nSolutions:")
                    for i, sol in enumerate(results["solutions"], 1):
                        print(
                            f"  {i}. Structure: {sol['structure']}, Time: {sol['execution_time']:.3f}s"
                        )
                        print(f"     File: {sol['cvc_file']}")
                else:
                    print("No solutions found.")
            else:
                # Use existing analysis method
                optimizer.analyze_results(results)

                # Show additional info for exhaustive search
                if results.get("all_solutions"):
                    print(f"\nAll solutions found ({len(results['all_solutions'])}):")
                    for i, sol in enumerate(results["all_solutions"], 1):
                        print(
                            f"  {i}. Gates: {sol['gate_num']}, Structure: {sol['structure']}, Time: {sol['execution_time']:.3f}s"
                        )

        # Return appropriate exit code
        if results["best_solution"]:
            return 0
        else:
            return 1

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.log_level == "DEBUG":
            import traceback

            logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
