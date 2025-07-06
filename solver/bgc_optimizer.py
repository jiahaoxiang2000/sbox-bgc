"""
BGC (Boolean Gate Count) optimizer for S-box implementations.

This module provides BGC-based optimization for S-box circuits, focusing on
minimizing the number of Boolean gates required for implementation.
"""

import os
import time
import threading
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .sbox_converter import SboxConverter
from .stp_solver import STPSolver, SolverResult


@dataclass
class BGCResult:
    """Result of BGC optimization."""

    gate_count: int
    depth: int
    structure: List[int]
    satisfiable: bool
    execution_time: float
    circuit_file: str
    result_file: str
    gate_assignments: Optional[Dict[str, Any]] = None


class BGCConstraintGenerator:
    """Generates CVC constraints for BGC optimization."""

    def __init__(self, bit_num: int, logger: Optional[logging.Logger] = None):
        self.bit_num = bit_num
        self.size = 2**bit_num
        self.logger = logger or logging.getLogger(__name__)

    def generate_variables(self, fout, gate_num: int, q_num: int, b_num: int) -> None:
        """Generate variable declarations for CVC file."""
        # Input variables X_i
        for i in range(self.bit_num):
            fout.write(f"X_{i}")
            if i == self.bit_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Output variables Y_i
        for i in range(self.bit_num):
            fout.write(f"Y_{i}")
            if i == self.bit_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Gate output variables T_i
        for t in range(gate_num):
            fout.write(f"T_{t}")
            if t == gate_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Gate input selection variables Q_i
        for i in range(q_num):
            fout.write(f"Q_{i}")
            if i == q_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Gate type encoding variables B_i
        for i in range(b_num):
            fout.write(f"B_{i}")
            if i == b_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

    def decompose_sbox(self, flag: int, sbox: List[int]) -> List[List[int]]:
        """Decompose S-box into bit vectors."""
        A = [[0 for _ in range(self.size)] for _ in range(self.bit_num)]

        for i in range(self.size):
            value = i if flag == 0 else sbox[i]
            for j in range(self.bit_num - 1, -1, -1):
                A[j][i] = value % 2
                value //= 2
        return A

    def generate_sbox_constraints(
        self, fout, sbox: List[int], gate_num: int, q_num: int, b_num: int
    ) -> None:
        """Generate S-box mapping constraints."""
        # Input constraints (X variables)
        A_input = self.decompose_sbox(0, sbox)
        for i in range(self.bit_num):
            fout.write(f"ASSERT( X_{i} = 0bin")
            for j in range(self.size):
                fout.write(str(A_input[i][j]))
            fout.write(" );\n")

        # Output constraints (Y variables)
        A_output = self.decompose_sbox(1, sbox)
        for i in range(self.bit_num):
            fout.write(f"ASSERT( Y_{i} = 0bin")
            for j in range(self.size):
                fout.write(str(A_output[i][j]))
            fout.write(" );\n")

        # Gate type constraints (B variables)
        for i in range(b_num):
            x0 = "0bin0"
            fout.write(f"ASSERT( B_{i}[2:2] & B_{i}[0:0] = {x0} );\n")

    def generate_gate_constraints(
        self,
        fout,
        gate_num: int,
        depth: int,
        structure: List[int],
        parallel: bool = False,
    ) -> None:
        """Generate gate logic constraints."""
        count_q = 0
        count_t = 0

        for d in range(depth):
            gates_at_depth = structure[d]
            self._generate_depth_constraints(
                fout, gates_at_depth, count_q, count_t, d, parallel
            )
            count_q += 2 * gates_at_depth
            count_t += gates_at_depth

        # Output selection constraints
        for y in range(self.bit_num):
            fout.write("ASSERT( ")
            for i in range(gate_num):
                fout.write(f"( Y_{y} = T_{i} )")
                if i == gate_num - 1:
                    fout.write(" );\n")
                else:
                    fout.write(" OR ")

    def _generate_depth_constraints(
        self,
        fout,
        gates_at_depth: int,
        count_q: int,
        count_t: int,
        depth: int,
        parallel: bool,
    ) -> None:
        """Generate constraints for a specific depth level."""
        current_q = count_q
        current_t = count_t

        for k in range(gates_at_depth):
            # Gate input selection constraints
            for q in range(2):
                if depth == 0 or q == 0 or not parallel:
                    fout.write("ASSERT( ")
                    # Input variables
                    for i in range(self.bit_num):
                        fout.write(f"( Q_{current_q} = X_{i} )")
                        if depth == 0 and i == self.bit_num - 1:
                            fout.write(" );\n")
                        else:
                            fout.write(" OR ")

                    # Intermediate variables
                    for i in range(current_t):
                        fout.write(f"( Q_{current_q} = T_{i} )")
                        if i == current_t - 1:
                            fout.write(" );\n")
                        else:
                            fout.write(" OR ")
                else:
                    fout.write("ASSERT( ")
                    for i in range(current_t):
                        fout.write(f"( Q_{current_q} = T_{i} )")
                        if i == current_t - 1:
                            fout.write(" );\n")
                        else:
                            fout.write(" OR ")
                current_q += 1

            # Gate operation encoding
            xx0 = "0bin" + "0" * self.size
            self._generate_gate_operation(
                fout, current_t, current_q - 2, current_q - 1, xx0
            )
            current_t += 1

    def _generate_gate_operation(
        self, fout, gate_idx: int, input1_idx: int, input2_idx: int, zero_vector: str
    ) -> None:
        """Generate gate operation constraint using BGC encoding."""
        constraint = (
            f"ASSERT( T_{gate_idx} = BVXOR("
            f"(IF B_{gate_idx}[2:2] =0bin1 THEN Q_{input1_idx} & Q_{input2_idx} ELSE {zero_vector} ENDIF), "
            f"BVXOR("
            f"(IF B_{gate_idx}[0:0]=0bin1 THEN ~Q_{input1_idx} ELSE {zero_vector} ENDIF), "
            f"(IF B_{gate_idx}[1:1]=0bin1 THEN BVXOR( Q_{input1_idx}, Q_{input2_idx}) ELSE {zero_vector} ENDIF ) "
            f") ) ); \n"
        )
        fout.write(constraint)

    def generate_objective(self, fout) -> None:
        """Generate satisfiability query."""
        fout.write("QUERY(FALSE);\nCOUNTEREXAMPLE;\n")


class BGCCircuitStructure:
    """Handles circuit structure generation and validation."""

    def __init__(self, bit_num: int, logger: Optional[logging.Logger] = None):
        self.bit_num = bit_num
        self.logger = logger or logging.getLogger(__name__)

    def generate_depth_combinations(
        self, gate_count: int, max_depth: int
    ) -> List[List[int]]:
        """Generate valid gate distribution combinations across depths."""
        valid_structures = []

        for depth in range(max_depth, 0, -1):
            structures = []
            self._combination_impl(
                list(range(1, gate_count + 1)), gate_count, [], depth, structures
            )

            # Filter valid structures
            for structure in structures:
                if self._validate_structure(structure):
                    valid_structures.append(structure)

        return valid_structures

    def generate_serial_structure(self, gate_count: int) -> List[int]:
        """Generate serial structure where each depth has only one gate."""
        return [1] * gate_count

    def _combination_impl(
        self,
        available: List[int],
        remaining: int,
        current: List[int],
        target_depth: int,
        results: List[List[int]],
    ) -> None:
        """Recursive combination generation."""
        if remaining == 0:
            if len(current) == target_depth:
                results.append(current.copy())
            return

        for i, val in enumerate(available):
            if val <= remaining:
                current.append(val)
                self._combination_impl(
                    available, remaining - val, current, target_depth, results
                )
                current.pop()
            else:
                break

    def _validate_structure(self, structure: List[int]) -> bool:
        """Validate if a circuit structure is feasible."""
        available_inputs = self.bit_num
        used_outputs = 0

        for gates_at_depth in reversed(structure):
            if gates_at_depth > available_inputs + used_outputs:
                return False
            used_outputs += available_inputs - gates_at_depth
            available_inputs = 2 * gates_at_depth

        return True


class BGCOptimizer:
    """Main BGC optimizer for S-box implementations."""

    def __init__(
        self,
        bit_num: int,
        stp_path: str = "stp",
        log_level: str = "INFO",
        threads: int = 20,
        timeout: int = 300,
    ):
        """
        Initialize BGC optimizer.

        Args:
            bit_num: Number of S-box input/output bits
            stp_path: Path to STP solver executable
            log_level: Logging level
            threads: Number of threads for parallel solving
            timeout: Solver timeout in seconds
        """
        self.bit_num = bit_num
        self.stp_path = stp_path
        self.threads = threads
        self.timeout = timeout

        # Setup logging
        self.logger = logging.getLogger(f"solver.bgc_optimizer")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Initialize components
        self.sbox_converter = SboxConverter(bit_num)
        self.constraint_generator = BGCConstraintGenerator(bit_num, self.logger)
        self.circuit_structure = BGCCircuitStructure(bit_num, self.logger)
        self.stp_solver = STPSolver(stp_path, timeout)

        # Results storage
        self.results = []
        self._thread_result = None

    def optimize_sbox(
        self,
        sbox: List[int],
        max_gates: int = 20,
        max_depth: int = 5,
        output_dir: str = "./output_bgc",
        cipher_name: str = "sbox",
        parallel: bool = False,
        stop_on_first: bool = True,
    ) -> Dict[str, Any]:
        """
        Optimize S-box using BGC method.

        Args:
            sbox: S-box definition as list of integers
            max_gates: Maximum number of gates to try
            max_depth: Maximum circuit depth
            output_dir: Output directory for results
            cipher_name: Name for output files
            parallel: Use parallel circuit structure
            stop_on_first: Stop on first solution found

        Returns:
            Dictionary with optimization results
        """
        self.logger.info(f"Starting BGC optimization: {cipher_name}")
        self.logger.info(f"S-box: {sbox}")
        self.logger.info(f"Max gates: {max_gates}, Max depth: {max_depth}")

        # Validate S-box
        if not self.sbox_converter.validate_sbox(sbox):
            raise ValueError("Invalid S-box provided")

        # Setup output directory
        os.makedirs(f"{output_dir}/{cipher_name}", exist_ok=True)

        best_result = None
        all_results = []

        # Try different gate counts (decreasing order for minimal solutions)
        for gate_count in range(max_gates, 0, -1):
            self.logger.info(f"Trying {gate_count} gates")

            # Generate circuit structures
            structures = self.circuit_structure.generate_depth_combinations(
                gate_count, max_depth
            )

            for i, structure in enumerate(structures):
                self.logger.debug(f"Testing structure {i}: {structure}")

                result = self._solve_structure(
                    sbox, gate_count, structure, output_dir, cipher_name, parallel, i
                )

                if result:
                    all_results.append(result)
                    if result.satisfiable:
                        self.logger.info(
                            f"✓ Found solution: {gate_count} gates, structure {structure}"
                        )
                        if (
                            not best_result
                            or result.gate_count < best_result.gate_count
                        ):
                            best_result = result

                        if stop_on_first:
                            break

            if best_result and stop_on_first:
                break

        # Save optimization summary
        self._save_optimization_summary(
            output_dir, cipher_name, all_results, best_result, sbox
        )

        return {
            "best_solution": best_result,
            "all_solutions": all_results,
            "total_attempts": len(all_results),
            "satisfiable_solutions": len([r for r in all_results if r.satisfiable]),
        }

    def optimize_sbox_serial(
        self,
        sbox: List[int],
        max_gates: int = 20,
        output_dir: str = "./output_bgc",
        cipher_name: str = "sbox",
        stop_on_first: bool = True,
    ) -> Dict[str, Any]:
        """
        Optimize S-box using BGC method with serial structure (one gate per depth).

        Args:
            sbox: S-box definition as list of integers
            max_gates: Maximum number of gates to try
            output_dir: Output directory for results
            cipher_name: Name for output files
            stop_on_first: Stop on first solution found

        Returns:
            Dictionary with optimization results
        """
        self.logger.info(f"Starting BGC serial optimization: {cipher_name}")
        self.logger.info(f"S-box: {sbox}")
        self.logger.info(f"Max gates: {max_gates} (serial mode: one gate per depth)")

        # Validate S-box
        if not self.sbox_converter.validate_sbox(sbox):
            raise ValueError("Invalid S-box provided")

        # Setup output directory
        os.makedirs(f"{output_dir}/{cipher_name}", exist_ok=True)

        best_result = None
        all_results = []

        # Try different gate counts (decreasing order for minimal solutions)
        for gate_count in range(max_gates, 0, -1):
            self.logger.info(f"Trying {gate_count} gates (serial structure)")

            # Generate serial structure: one gate per depth
            structure = self.circuit_structure.generate_serial_structure(gate_count)
            self.logger.debug(f"Testing serial structure: {structure}")

            result = self._solve_structure(
                sbox, gate_count, structure, output_dir, cipher_name, False, 0
            )

            if result:
                all_results.append(result)
                if result.satisfiable:
                    self.logger.info(
                        f"✓ Found serial solution: {gate_count} gates, depth {len(structure)}"
                    )
                    if not best_result or result.gate_count < best_result.gate_count:
                        best_result = result

                    if stop_on_first:
                        break

        # Save optimization summary
        self._save_optimization_summary(
            output_dir, cipher_name, all_results, best_result, sbox
        )

        return {
            "best_solution": best_result,
            "all_solutions": all_results,
            "total_attempts": len(all_results),
            "satisfiable_solutions": len([r for r in all_results if r.satisfiable]),
        }

    def _solve_structure(
        self,
        sbox: List[int],
        gate_count: int,
        structure: List[int],
        output_dir: str,
        cipher_name: str,
        parallel: bool,
        structure_idx: int,
    ) -> Optional[BGCResult]:
        """Solve a specific circuit structure."""
        depth = len(structure)
        q_num = 2 * gate_count
        b_num = gate_count

        # Generate file names
        structure_str = "".join(map(str, structure))
        base_filename = f"{output_dir}/{cipher_name}/bgc_{gate_count}_{structure_str}_{structure_idx}"
        cvc_file = f"{base_filename}.cvc"

        try:
            # Generate CVC file
            with open(cvc_file, "w") as fout:
                self.constraint_generator.generate_variables(
                    fout, gate_count, q_num, b_num
                )
                self.constraint_generator.generate_sbox_constraints(
                    fout, sbox, gate_count, q_num, b_num
                )
                self.constraint_generator.generate_gate_constraints(
                    fout, gate_count, depth, structure, parallel
                )
                self.constraint_generator.generate_objective(fout)

            # Solve with STP
            start_time = time.time()
            solver_result = self._execute_solver_threaded(cvc_file, structure_idx)
            end_time = time.time()

            execution_time = end_time - start_time
            result_file = f"{base_filename}.txt"

            # Save detailed result to file (like GEC optimizer does)
            if solver_result:
                # Use STP solver's save_result method for consistency with GEC optimizer
                self.stp_solver.save_result(solver_result, result_file)
                # Also save BGC-specific information
                self._append_bgc_info(result_file, gate_count, structure)
            else:
                self._save_timeout_result(
                    result_file, gate_count, structure, execution_time
                )

            return BGCResult(
                gate_count=gate_count,
                depth=depth,
                structure=structure,
                satisfiable=solver_result.satisfiable if solver_result else False,
                execution_time=execution_time,
                circuit_file=cvc_file,
                result_file=result_file,
            )

        except Exception as e:
            self.logger.error(f"Error solving structure {structure}: {e}")
            return None

    def _execute_solver_threaded(
        self, cvc_file: str, structure_idx: int
    ) -> Optional[SolverResult]:
        """Execute STP solver in a thread."""
        self._thread_result = None

        def solver_thread():
            try:
                self._thread_result = self.stp_solver.solve_file(cvc_file)
            except Exception as e:
                self.logger.error(f"Solver thread error: {e}")

        thread = threading.Thread(target=solver_thread)
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            self.logger.warning(f"Solver timeout for structure {structure_idx}")
            return None

        return self._thread_result

    def _append_bgc_info(
        self, result_file: str, gate_count: int, structure: List[int]
    ) -> None:
        """Append BGC-specific information to the result file."""
        try:
            with open(result_file, "a") as f:
                f.write("\n--- BGC Specific Information ---\n")
                f.write(f"Gate Count: {gate_count}\n")
                f.write(f"Circuit Depth: {len(structure)}\n")
                f.write(f"Structure: {structure}\n")
                
        except Exception as e:
            self.logger.error(f"Error appending BGC info to {result_file}: {e}")

    def _save_timeout_result(
        self,
        result_file: str,
        gate_count: int,
        structure: List[int],
        execution_time: float,
    ) -> None:
        """Save timeout result to file."""
        try:
            with open(result_file, "w") as f:
                f.write("=== BGC Optimization Result ===\n")
                f.write(f"Gate Count: {gate_count}\n")
                f.write(f"Circuit Depth: {len(structure)}\n")
                f.write(f"Structure: {structure}\n")
                f.write(f"Satisfiable: UNKNOWN (Timeout)\n")
                f.write(f"Execution Time: {execution_time:.3f}s\n")
                f.write(f"Success: False\n")
                f.write(f"Error: Solver timeout\n")
                f.write("\n=== Timeout Result ===\n")
                f.write("Solver exceeded the timeout limit.\n")

        except Exception as e:
            self.logger.error(f"Error saving timeout result to {result_file}: {e}")

    def _save_optimization_summary(
        self,
        output_dir: str,
        cipher_name: str,
        all_results: List[BGCResult],
        best_result: Optional[BGCResult],
        sbox: List[int],
    ) -> None:
        """Save optimization summary to file."""
        try:
            summary_file = os.path.join(
                output_dir, cipher_name, f"{cipher_name}_bgc_summary.txt"
            )

            with open(summary_file, "w") as f:
                f.write("=== BGC Optimization Summary ===\n")
                f.write(f"Cipher: {cipher_name}\n")
                f.write(f"S-box: {sbox}\n")
                f.write(f"Total attempts: {len(all_results)}\n")

                satisfiable_solutions = [r for r in all_results if r.satisfiable]
                f.write(f"Satisfiable solutions: {len(satisfiable_solutions)}\n")

                if best_result:
                    f.write(f"\n=== Best Solution ===\n")
                    f.write(f"Gate Count: {best_result.gate_count}\n")
                    f.write(f"Circuit Depth: {best_result.depth}\n")
                    f.write(f"Structure: {best_result.structure}\n")
                    f.write(f"Execution Time: {best_result.execution_time:.3f}s\n")
                    f.write(f"CVC File: {best_result.circuit_file}\n")
                    f.write(f"Result File: {best_result.result_file}\n")
                else:
                    f.write(f"\n=== No Solution Found ===\n")
                    f.write(
                        "No satisfiable solution found within the given constraints.\n"
                    )

                if satisfiable_solutions:
                    f.write(f"\n=== All Solutions ===\n")
                    for i, result in enumerate(satisfiable_solutions, 1):
                        f.write(f"Solution {i}:\n")
                        f.write(
                            f"  Gates: {result.gate_count}, Depth: {result.depth}\n"
                        )
                        f.write(f"  Structure: {result.structure}\n")
                        f.write(f"  Time: {result.execution_time:.3f}s\n")
                        f.write(
                            f"  Files: {result.circuit_file}, {result.result_file}\n"
                        )
                        f.write("\n")

                # Execution time statistics
                if all_results:
                    times = [r.execution_time for r in all_results]
                    f.write(f"=== Execution Time Statistics ===\n")
                    f.write(f"Min: {min(times):.3f}s\n")
                    f.write(f"Max: {max(times):.3f}s\n")
                    f.write(f"Average: {sum(times)/len(times):.3f}s\n")
                    f.write(f"Total: {sum(times):.3f}s\n")

        except Exception as e:
            self.logger.error(f"Error saving optimization summary: {e}")

    def analyze_results(self, results: Dict[str, Any]) -> None:
        """Analyze and display optimization results."""
        self.logger.info("=== BGC Optimization Results ===")
        self.logger.info(f"Total attempts: {results['total_attempts']}")
        self.logger.info(f"Satisfiable solutions: {results['satisfiable_solutions']}")

        if results["best_solution"]:
            best = results["best_solution"]
            self.logger.info("Best solution:")
            self.logger.info(f"  Gates: {best.gate_count}")
            self.logger.info(f"  Depth: {best.depth}")
            self.logger.info(f"  Structure: {best.structure}")
            self.logger.info(f"  Execution time: {best.execution_time:.3f}s")
            self.logger.info(f"  CVC file: {best.circuit_file}")
        else:
            self.logger.info("No solution found within constraints")
