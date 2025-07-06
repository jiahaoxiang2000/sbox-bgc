#!/usr/bin/env python3
"""
Quick test script for BGC optimizer.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from solver import BGCOptimizer


def test_bgc_basic():
    """Test basic BGC functionality."""
    print("Testing BGC Optimizer...")

    # Initialize optimizer for 3-bit S-box
    optimizer = BGCOptimizer(bit_num=3, stp_path="./run_stp.sh", timeout=60)

    # Simple 3-bit S-box
    sbox = [0, 1, 3, 6, 7, 4, 5, 2]

    print(f"Testing with 3-bit S-box: {sbox}")

    try:
        # Run optimization with small constraints for quick test
        results = optimizer.optimize_sbox(
            sbox=sbox,
            max_gates=15,  # Small for quick test
            max_depth=15,
            output_dir="./output_bgc",
            cipher_name="test_3bit_sbox",
            stop_on_first=True,
        )

        print("\n=== Test Results ===")
        print(f"Total attempts: {results['total_attempts']}")
        print(f"Satisfiable solutions: {results['satisfiable_solutions']}")

        if results["best_solution"]:
            best = results["best_solution"]
            print(f"✓ Best solution found:")
            print(f"  Gates: {best.gate_count}")
            print(f"  Depth: {best.depth}")
            print(f"  Structure: {best.structure}")
            print(f"  Execution time: {best.execution_time:.3f}s")
            print(f"  CVC file: {best.circuit_file}")
            return True
        else:
            print("✗ No solution found within constraints")
            return False

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = test_bgc_basic()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
