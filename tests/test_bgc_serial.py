#!/usr/bin/env python3
"""
Test script for BGC optimizer serial mode.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solver import BGCOptimizer


def test_bgc_serial():
    """Test BGC serial mode functionality."""
    print("Testing BGC Optimizer Serial Mode...")

    # Initialize optimizer for 3-bit S-box
    optimizer = BGCOptimizer(bit_num=3, stp_path="./run_stp.sh", timeout=60)

    # Simple 3-bit S-box
    sbox = [0, 1, 3, 6, 7, 4, 5, 2]

    print(f"Testing with 3-bit S-box: {sbox}")
    print("Serial mode: one gate per depth level")

    try:
        # Run serial optimization
        results = optimizer.optimize_sbox_serial(
            sbox=sbox,
            max_gates=8,  # Small for quick test
            output_dir="./test_bgc_serial_output",
            cipher_name="test_3bit_serial",
            stop_on_first=True,
        )

        print("\n=== Serial Mode Test Results ===")
        print(f"Total attempts: {results['total_attempts']}")
        print(f"Satisfiable solutions: {results['satisfiable_solutions']}")

        if results["best_solution"]:
            best = results["best_solution"]
            print(f"✓ Best serial solution found:")
            print(f"  Gates: {best.gate_count}")
            print(f"  Depth: {best.depth}")
            print(f"  Structure: {best.structure}")
            print(f"  Serial mode verification: {all(g == 1 for g in best.structure)}")
            print(f"  Execution time: {best.execution_time:.3f}s")
            print(f"  CVC file: {best.circuit_file}")
            return True
        else:
            print("✗ No serial solution found within constraints")
            return False

    except Exception as e:
        print(f"✗ Serial test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = test_bgc_serial()
    print(f"\nSerial Mode Test {'PASSED' if success else 'FAILED'}")