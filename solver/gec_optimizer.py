"""
Main orchestrator for GEC S-box optimization.
"""

import logging
import os
from typing import List, Optional, Tuple, Dict, Any
from itertools import combinations
from .sbox_converter import SboxConverter
from .gate_library import GateLibrary
from .cvc_generator import CVCGenerator
from .stp_solver import STPSolver, SolverResult
from .utils import setup_logging, ensure_directory


class GECOptimizer:
    """
    Main class for S-box GEC optimization.
    """

    def __init__(
        self,
        bit_num: int,
        stp_path: str = "stp",
        log_level: str = "INFO",
        threads: int = 20,
    ):
        """
        Initialize GEC optimizer.

        Args:
            bit_num: Number of bits for S-box
            stp_path: Path to STP executable
            log_level: Logging level
            threads: Number of threads for STP solver
        """
        self.bit_num = bit_num
        self.threads = threads
        self.logger = setup_logging(log_level)

        # Initialize components
        self.sbox_converter = SboxConverter(bit_num)
        self.gate_library = GateLibrary()
        self.cvc_generator = CVCGenerator(self.sbox_converter, self.gate_library)
        self.stp_solver = STPSolver(stp_path)

        self.logger.info(
            f"Initialized GEC optimizer for {bit_num}-bit S-boxes (threads: {threads})"
        )

    def generate_depth_combinations(
        self, gate_num: int, max_depth: int
    ) -> List[List[int]]:
        """
        Generate valid depth structure combinations.

        Args:
            gate_num: Total number of gates
            max_depth: Maximum circuit depth

        Returns:
            List of valid depth structures
        """
        self.logger.debug(
            f"Generating depth combinations for {gate_num} gates, max depth {max_depth}"
        )

        filter_list = list(range(1, gate_num + 1))
        valid_structures = []

        for depth in range(1, min(max_depth + 1, gate_num + 1)):
            structures = []
            self._combination_impl(filter_list, gate_num, [], depth, structures)

            # Filter valid structures
            for structure in structures:
                if self._is_valid_structure(structure):
                    valid_structures.append(structure)

        self.logger.info(f"Generated {len(valid_structures)} valid depth structures")
        return valid_structures

    def _combination_impl(
        self,
        options: List[int],
        target: int,
        current: List[int],
        max_length: int,
        results: List[List[int]],
    ) -> None:
        """
        Recursive combination generation.

        Args:
            options: Available options
            target: Target sum
            current: Current combination
            max_length: Maximum combination length
            results: Results accumulator
        """
        if target == 0:
            if len(current) == max_length:
                results.append(current.copy())
            return

        if len(current) >= max_length:
            return

        for option in options:
            if option <= target:
                current.append(option)
                self._combination_impl(
                    options, target - option, current, max_length, results
                )
                current.pop()

    def _is_valid_structure(self, structure: List[int]) -> bool:
        """
        Check if depth structure is valid.

        Args:
            structure: Depth structure to validate

        Returns:
            True if valid
        """
        gates_so_far = self.bit_num
        gates_used = 0

        for level_gates in reversed(structure):
            if level_gates > gates_so_far + gates_used:
                return False
            gates_used = gates_so_far + gates_used - level_gates
            gates_so_far = 2 * level_gates

        return True

    def optimize_sbox(
        self,
        sbox: List[int],
        max_gates: int,
        max_gec: int,
        technology: int = 0,
        gate_list: Optional[List[str]] = None,
        output_dir: str = "./gec",
        cipher_name: str = "sbox",
    ) -> Dict[str, Any]:
        """
        Optimize S-box for minimum GEC.

        Args:
            sbox: S-box values
            max_gates: Maximum number of gates to try
            max_gec: Maximum GEC value
            technology: Technology index (0: UMC 180nm, 1: SMIC 130nm)
            gate_list: Optional list of allowed gate types
            output_dir: Output directory
            cipher_name: Name for output files

        Returns:
            Optimization results
        """
        if not self.sbox_converter.validate_sbox(sbox):
            raise ValueError("Invalid S-box provided")

        self.logger.info(f"Starting S-box optimization: {cipher_name}")
        self.logger.info(f"S-box: {sbox}")
        self.logger.info(f"Max gates: {max_gates}, Max GEC: {max_gec}")
        self.logger.info(
            f"Technology: {self.gate_library.get_technology_name(technology)}"
        )

        if gate_list:
            self.logger.info(f"Allowed gates: {gate_list}")

        ensure_directory(output_dir)

        best_result = None
        optimization_results = {
            "sbox": sbox,
            "cipher_name": cipher_name,
            "technology": technology,
            "max_gates": max_gates,
            "max_gec": max_gec,
            "gate_list": gate_list,
            "results": [],
            "best_solution": None,
        }

        # Try different numbers of gates
        for gate_num in range(max_gates, 0, -1):
            self.logger.info(f"Trying with {gate_num} gates")

            # Generate depth structures
            depth_structures = self.generate_depth_combinations(gate_num, gate_num)

            if not depth_structures:
                self.logger.warning(f"No valid depth structures for {gate_num} gates")
                continue

            self.logger.info(f"Testing {len(depth_structures)} depth structures")

            for structure in depth_structures:
                result = self._solve_structure(
                    sbox,
                    gate_num,
                    max_gec,
                    len(structure),
                    structure,
                    technology,
                    gate_list,
                    output_dir,
                    cipher_name,
                )

                optimization_results["results"].append(result)

                if result["satisfiable"]:
                    self.logger.info(
                        f"Found solution with {gate_num} gates, structure {structure}"
                    )
                    if best_result is None or gate_num < best_result["gate_num"]:
                        best_result = result
                        optimization_results["best_solution"] = result

                    # If we found a solution, we can stop (we're trying gate numbers in decreasing order)
                    break

            if best_result:
                break

        if best_result:
            self.logger.info(
                f"Optimization completed. Best solution: {best_result['gate_num']} gates"
            )
        else:
            self.logger.warning("No solution found within constraints")

        return optimization_results

    def _solve_structure(
        self,
        sbox: List[int],
        gate_num: int,
        max_gec: int,
        depth: int,
        structure: List[int],
        technology: int,
        gate_list: Optional[List[str]],
        output_dir: str,
        cipher_name: str,
    ) -> Dict[str, Any]:
        """
        Solve for a specific gate structure.

        Args:
            sbox: S-box values
            gate_num: Number of gates
            max_gec: Maximum GEC
            depth: Circuit depth
            structure: Depth structure
            technology: Technology index
            gate_list: Allowed gate types
            output_dir: Output directory
            cipher_name: Cipher name

        Returns:
            Solution result
        """
        structure_str = "_".join(map(str, structure))

        # Create output directory structure
        cipher_dir = os.path.join(output_dir, cipher_name)
        ensure_directory(cipher_dir)

        # Generate filename
        filename_base = f"{cipher_name}_d_{depth}_{structure_str}"
        cvc_file = os.path.join(cipher_dir, f"{filename_base}.cvc")

        self.logger.debug(f"Generating CVC file: {cvc_file}")

        # Generate CVC file
        self.cvc_generator.generate_cvc_file(
            cvc_file, sbox, gate_num, max_gec, depth, structure, technology, gate_list
        )

        # Solve with STP
        self.logger.debug(f"Solving structure: {structure}")
        solver_result = self.stp_solver.solve_with_script(
            cvc_file,
            additional_args=["--cryptominisat", "--threads", str(self.threads)],
        )

        # Save detailed result
        result_file = os.path.join(cipher_dir, f"{filename_base}.txt")
        self.stp_solver.save_result(solver_result, result_file)

        result = {
            "gate_num": gate_num,
            "depth": depth,
            "structure": structure,
            "cvc_file": cvc_file,
            "result_file": result_file,
            "satisfiable": solver_result.satisfiable,
            "execution_time": solver_result.execution_time,
            "success": solver_result.success,
            "error_message": solver_result.error_message,
            "counterexample": solver_result.counterexample,
        }

        if solver_result.satisfiable:
            self.logger.info(
                f"✓ Structure {structure}: SAT ({solver_result.execution_time:.3f}s)"
            )
        else:
            self.logger.debug(
                f"✗ Structure {structure}: UNSAT ({solver_result.execution_time:.3f}s)"
            )

        return result

    def analyze_results(self, results: Dict[str, Any]) -> None:
        """
        Analyze and print optimization results.

        Args:
            results: Optimization results dictionary
        """
        self.logger.info("=== Optimization Results Analysis ===")

        total_attempts = len(results["results"])
        satisfiable_count = sum(1 for r in results["results"] if r["satisfiable"])

        self.logger.info(f"Total attempts: {total_attempts}")
        self.logger.info(f"Satisfiable solutions: {satisfiable_count}")

        if results["best_solution"]:
            best = results["best_solution"]
            self.logger.info(f"Best solution:")
            self.logger.info(f"  Gates: {best['gate_num']}")
            self.logger.info(f"  Depth: {best['depth']}")
            self.logger.info(f"  Structure: {best['structure']}")
            self.logger.info(f"  Execution time: {best['execution_time']:.3f}s")
            self.logger.info(f"  CVC file: {best['cvc_file']}")
            self.logger.info(f"  Result file: {best['result_file']}")
        else:
            self.logger.info("No solution found")

        # Show execution time statistics
        times = [r["execution_time"] for r in results["results"]]
        if times:
            self.logger.info(f"Execution time stats:")
            self.logger.info(f"  Min: {min(times):.3f}s")
            self.logger.info(f"  Max: {max(times):.3f}s")
            self.logger.info(f"  Avg: {sum(times)/len(times):.3f}s")
            self.logger.info(f"  Total: {sum(times):.3f}s")

    def optimize_sbox_exhaustive(
        self,
        sbox: List[int],
        max_gates: int,
        max_gec: int,
        technology: int = 0,
        gate_list: Optional[List[str]] = None,
        output_dir: str = "./gec",
        cipher_name: str = "sbox",
        stop_on_first: bool = True,
        explore_all_structures: bool = False,
    ) -> Dict[str, Any]:
        """
        Optimize S-box for minimum GEC with more control over search strategy.

        Args:
            sbox: S-box values
            max_gates: Maximum number of gates to try
            max_gec: Maximum GEC value
            technology: Technology index (0: UMC 180nm, 1: SMIC 130nm)
            gate_list: Optional list of allowed gate types
            output_dir: Output directory
            cipher_name: Name for output files
            stop_on_first: Stop when first solution is found (default: True)
            explore_all_structures: Test all structures for each gate count (default: False)

        Returns:
            Optimization results with potentially multiple solutions
        """
        if not self.sbox_converter.validate_sbox(sbox):
            raise ValueError("Invalid S-box provided")

        self.logger.info(f"Starting exhaustive S-box optimization: {cipher_name}")
        self.logger.info(
            f"Stop on first: {stop_on_first}, Explore all structures: {explore_all_structures}"
        )
        self.logger.info(f"S-box: {sbox}")
        self.logger.info(f"Max gates: {max_gates}, Max GEC: {max_gec}")
        self.logger.info(
            f"Technology: {self.gate_library.get_technology_name(technology)}"
        )

        if gate_list:
            self.logger.info(f"Allowed gates: {gate_list}")

        ensure_directory(output_dir)

        all_solutions = []
        best_result = None
        optimization_results = {
            "sbox": sbox,
            "cipher_name": cipher_name,
            "technology": technology,
            "max_gates": max_gates,
            "max_gec": max_gec,
            "gate_list": gate_list,
            "results": [],
            "all_solutions": [],
            "best_solution": None,
            "search_strategy": {
                "stop_on_first": stop_on_first,
                "explore_all_structures": explore_all_structures,
            },
        }

        # Try different numbers of gates
        for gate_num in range(max_gates, 0, -1):
            self.logger.info(f"Trying with {gate_num} gates")

            # Generate depth structures
            depth_structures = self.generate_depth_combinations(gate_num, gate_num)

            if not depth_structures:
                self.logger.warning(f"No valid depth structures for {gate_num} gates")
                continue

            self.logger.info(f"Testing {len(depth_structures)} depth structures")

            gate_solutions = []

            for structure in depth_structures:
                result = self._solve_structure(
                    sbox,
                    gate_num,
                    max_gec,
                    len(structure),
                    structure,
                    technology,
                    gate_list,
                    output_dir,
                    cipher_name,
                )

                optimization_results["results"].append(result)

                if result["satisfiable"]:
                    gate_solutions.append(result)
                    all_solutions.append(result)

                    self.logger.info(
                        f"Found solution with {gate_num} gates, structure {structure}"
                    )

                    if best_result is None or gate_num < best_result["gate_num"]:
                        best_result = result
                        optimization_results["best_solution"] = result

                # Stop on first solution for this gate count if not exploring all structures
                if not explore_all_structures and gate_solutions:
                    break

            # If we found solutions and stop_on_first is True, stop here
            if gate_solutions and stop_on_first:
                self.logger.info(
                    f"Found {len(gate_solutions)} solution(s) with {gate_num} gates - stopping search"
                )
                break

        optimization_results["all_solutions"] = all_solutions

        if best_result:
            self.logger.info(
                f"Optimization completed. Best solution: {best_result['gate_num']} gates"
            )
            self.logger.info(f"Total solutions found: {len(all_solutions)}")
        else:
            self.logger.warning("No solution found within constraints")

        return optimization_results

    def find_all_solutions_for_gates(
        self,
        sbox: List[int],
        gate_num: int,
        max_gec: int,
        technology: int = 0,
        gate_list: Optional[List[str]] = None,
        output_dir: str = "./gec",
        cipher_name: str = "sbox",
    ) -> Dict[str, Any]:
        """
        Find all possible solutions for a specific number of gates.

        Args:
            sbox: S-box values
            gate_num: Exact number of gates to use
            max_gec: Maximum GEC value
            technology: Technology index
            gate_list: Optional list of allowed gate types
            output_dir: Output directory
            cipher_name: Name for output files

        Returns:
            All solutions for the specified gate count
        """
        if not self.sbox_converter.validate_sbox(sbox):
            raise ValueError("Invalid S-box provided")

        self.logger.info(f"Finding all solutions for {gate_num} gates: {cipher_name}")
        self.logger.info(f"S-box: {sbox}")
        self.logger.info(f"Max GEC: {max_gec}")
        self.logger.info(
            f"Technology: {self.gate_library.get_technology_name(technology)}"
        )

        ensure_directory(output_dir)

        # Generate depth structures
        depth_structures = self.generate_depth_combinations(gate_num, gate_num)

        if not depth_structures:
            self.logger.warning(f"No valid depth structures for {gate_num} gates")
            return {
                "gate_num": gate_num,
                "solutions": [],
                "total_structures_tested": 0,
                "satisfiable_solutions": 0,
            }

        self.logger.info(f"Testing {len(depth_structures)} depth structures")

        solutions = []
        all_results = []

        for i, structure in enumerate(depth_structures):
            self.logger.debug(
                f"Testing structure {i+1}/{len(depth_structures)}: {structure}"
            )

            result = self._solve_structure(
                sbox,
                gate_num,
                max_gec,
                len(structure),
                structure,
                technology,
                gate_list,
                output_dir,
                cipher_name,
            )

            all_results.append(result)

            if result["satisfiable"]:
                solutions.append(result)
                self.logger.info(
                    f"✓ Solution {len(solutions)}: structure {structure}, time: {result['execution_time']:.3f}s"
                )
            else:
                self.logger.debug(f"✗ Structure {structure}: UNSAT")

        results = {
            "gate_num": gate_num,
            "solutions": solutions,
            "all_results": all_results,
            "total_structures_tested": len(depth_structures),
            "satisfiable_solutions": len(solutions),
            "sbox": sbox,
            "cipher_name": cipher_name,
            "technology": technology,
            "max_gec": max_gec,
            "gate_list": gate_list,
        }

        self.logger.info(
            f"Found {len(solutions)} solution(s) out of {len(depth_structures)} structures tested"
        )

        return results
