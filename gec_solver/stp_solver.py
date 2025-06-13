"""
STP solver interface for solving CVC constraint problems.
"""

import logging
import os
import subprocess
import time
import threading
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from .utils import get_timestamp


@dataclass
class SolverResult:
    """Result from STP solver execution."""

    success: bool
    satisfiable: bool
    output: str
    execution_time: float
    error_message: Optional[str] = None
    counterexample: Optional[Dict[str, Any]] = None


class STPSolver:
    """
    Interface for STP solver execution and result parsing.
    """

    def __init__(self, stp_path: str = "stp", timeout: int = 300):
        """
        Initialize STP solver.

        Args:
            stp_path: Path to STP executable
            timeout: Solver timeout in seconds
        """
        self.stp_path = stp_path
        self.timeout = timeout
        self.logger = logging.getLogger("gec_solver.stp_solver")

        # Verify STP is available
        if not self._check_stp_availability():
            raise RuntimeError(f"STP solver not found at: {stp_path}")

        self.logger.info(
            f"Initialized STP solver (path: {stp_path}, timeout: {timeout}s)"
        )

    def _check_stp_availability(self) -> bool:
        """
        Check if STP solver is available.

        Returns:
            True if STP is available
        """
        try:
            result = subprocess.run(
                [self.stp_path, "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ):
            return False

    def solve_file(
        self, cvc_file: str, additional_args: Optional[List[str]] = None
    ) -> SolverResult:
        """
        Solve a CVC file using STP.

        Args:
            cvc_file: Path to CVC file
            additional_args: Additional STP arguments

        Returns:
            Solver result
        """
        if not os.path.exists(cvc_file):
            raise FileNotFoundError(f"CVC file not found: {cvc_file}")

        self.logger.info(f"Solving CVC file: {cvc_file}")

        # Build command
        cmd = [self.stp_path]
        if additional_args:
            cmd.extend(additional_args)
        cmd.append(cvc_file)

        self.logger.debug(f"STP command: {' '.join(cmd)}")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )

            end_time = time.time()
            execution_time = end_time - start_time

            self.logger.debug(f"STP execution completed in {execution_time:.3f}s")

            return self._parse_result(result, execution_time)

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.warning(f"STP solver timeout after {execution_time:.3f}s")
            return SolverResult(
                success=False,
                satisfiable=False,
                output="",
                execution_time=execution_time,
                error_message="Solver timeout",
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"STP execution failed: {str(e)}")
            return SolverResult(
                success=False,
                satisfiable=False,
                output="",
                execution_time=execution_time,
                error_message=str(e),
            )

    def solve_with_script(
        self,
        cvc_file: str,
        script_path: str = "./run_stp.sh",
        additional_args: Optional[List[str]] = None,
    ) -> SolverResult:
        """
        Solve using a shell script (like run_stp.sh).

        Args:
            cvc_file: Path to CVC file
            script_path: Path to shell script
            additional_args: Additional arguments

        Returns:
            Solver result
        """
        if not os.path.exists(script_path):
            self.logger.warning(
                f"Script not found: {script_path}, falling back to direct STP call"
            )
            return self.solve_file(cvc_file, additional_args)

        self.logger.info(f"Solving with script: {script_path}")

        # Build command
        cmd = [script_path, "-p", cvc_file]
        if additional_args:
            cmd.extend(additional_args)

        self.logger.debug(f"Script command: {' '.join(cmd)}")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout, shell=False
            )

            end_time = time.time()
            execution_time = end_time - start_time

            return self._parse_result(result, execution_time)

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.warning(f"Script timeout after {execution_time:.3f}s")
            return SolverResult(
                success=False,
                satisfiable=False,
                output="",
                execution_time=execution_time,
                error_message="Script timeout",
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Script execution failed: {str(e)}")
            return SolverResult(
                success=False,
                satisfiable=False,
                output="",
                execution_time=execution_time,
                error_message=str(e),
            )

    def _parse_result(
        self, result: subprocess.CompletedProcess, execution_time: float
    ) -> SolverResult:
        """
        Parse STP solver result.

        Args:
            result: Subprocess result
            execution_time: Execution time in seconds

        Returns:
            Parsed solver result
        """
        output = result.stdout
        error_output = result.stderr

        # Check for satisfiability
        is_satisfiable = False
        is_invalid = False

        if "Invalid." in output:
            is_invalid = True
            is_satisfiable = True  # Invalid means satisfiable (counterexample found)
            self.logger.info("Problem is satisfiable (Invalid result)")
        elif "Valid." in output:
            is_satisfiable = False
            self.logger.info("Problem is unsatisfiable (Valid result)")
        elif "Timed out" in output or "timeout" in output.lower():
            self.logger.warning("Solver timed out")
            return SolverResult(
                success=False,
                satisfiable=False,
                output=output,
                execution_time=execution_time,
                error_message="Solver timeout",
            )

        # Parse counterexample if available
        counterexample = None
        if is_satisfiable and "COUNTEREXAMPLE" in output:
            counterexample = self._parse_counterexample(output)

        success = result.returncode == 0 or is_invalid

        solver_result = SolverResult(
            success=success,
            satisfiable=is_satisfiable,
            output=output,
            execution_time=execution_time,
            error_message=error_output if error_output and not success else None,
            counterexample=counterexample,
        )

        self.logger.info(
            f"Solver result: satisfiable={is_satisfiable}, time={execution_time:.3f}s"
        )
        return solver_result

    def _parse_counterexample(self, output: str) -> Dict[str, Any]:
        """
        Parse counterexample from STP output.

        Args:
            output: STP output string

        Returns:
            Dictionary containing counterexample values
        """
        counterexample = {}

        # Find COUNTEREXAMPLE section
        lines = output.split("\n")
        in_counterexample = False

        for line in lines:
            line = line.strip()

            if "COUNTEREXAMPLE:" in line:
                in_counterexample = True
                continue

            if in_counterexample and line:
                if "ASSERT" in line:
                    # Parse assignment: ASSERT( var = value );
                    if "=" in line:
                        parts = line.split("=")
                        if len(parts) == 2:
                            var_part = parts[0].strip()
                            val_part = parts[1].strip()

                            # Extract variable name
                            var_name = var_part.replace("ASSERT(", "").strip()

                            # Extract value
                            value = val_part.replace(");", "").replace(")", "").strip()

                            counterexample[var_name] = value
                elif line == "" or "%" in line:
                    # End of counterexample
                    break

        self.logger.debug(f"Parsed counterexample with {len(counterexample)} variables")
        return counterexample

    def save_result(self, result: SolverResult, output_file: str) -> None:
        """
        Save solver result to file.

        Args:
            result: Solver result
            output_file: Output file path
        """
        with open(output_file, "w") as f:
            f.write(f"Timestamp: {get_timestamp()}\n")
            f.write(f"Success: {result.success}\n")
            f.write(f"Satisfiable: {result.satisfiable}\n")
            f.write(f"Execution time: {result.execution_time:.3f}s\n")

            if result.error_message:
                f.write(f"Error: {result.error_message}\n")

            f.write("\n--- STP Output ---\n")
            f.write(result.output)

            if result.counterexample:
                f.write("\n--- Counterexample ---\n")
                for var, value in result.counterexample.items():
                    f.write(f"{var} = {value}\n")

        self.logger.info(f"Result saved to: {output_file}")

    def solve_batch(
        self,
        cvc_files: List[str],
        output_dir: str,
        use_script: bool = True,
        additional_args: Optional[List[str]] = None,
    ) -> List[Tuple[str, SolverResult]]:
        """
        Solve multiple CVC files.

        Args:
            cvc_files: List of CVC file paths
            output_dir: Output directory for results
            use_script: Whether to use run_stp.sh script
            additional_args: Additional solver arguments

        Returns:
            List of (filename, result) tuples
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []

        self.logger.info(f"Starting batch solve of {len(cvc_files)} files")

        for i, cvc_file in enumerate(cvc_files):
            self.logger.info(f"Solving file {i+1}/{len(cvc_files)}: {cvc_file}")

            if use_script:
                result = self.solve_with_script(
                    cvc_file, additional_args=additional_args
                )
            else:
                result = self.solve_file(cvc_file, additional_args=additional_args)

            # Save result
            base_name = os.path.splitext(os.path.basename(cvc_file))[0]
            result_file = os.path.join(output_dir, f"{base_name}_result.txt")
            self.save_result(result, result_file)

            results.append((cvc_file, result))

        self.logger.info(f"Batch solve completed: {len(results)} files processed")
        return results
