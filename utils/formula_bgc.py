#!/usr/bin/env python3
"""
BGC Formula generator for STP solver output.

This script parses STP solver output from BGC optimization and generates 
readable Boolean formulas with gate count analysis.
"""

import re
import argparse
import os
import sys
from typing import Dict, List, Optional, Any

# Add parent directory to path to import solver modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class BGCFormulaGenerator:
    """Generator for Boolean formulas from BGC STP solver output."""

    def __init__(self):
        """Initialize the BGC formula generator."""
        
        # BGC gate type mapping based on BGC encoding
        # BGC uses 3-bit encoding as specified: B[2:0]
        self.bgc_gate_types = {
            "0": "ZERO",      # 000 - Zero function
            "1": "NOT_Q0",    # 001 - ~Q_0 (NOT of first input)
            "2": "XOR",       # 010 - Q_0 XOR Q_1 
            "3": "NOT_Q1",    # 011 - ~Q_1 (NOT of second input)
            "4": "AND",       # 100 - Q_0 AND Q_1
            "5": "UNKNOWN_5", # 101 - Not defined in specification
            "6": "OR",        # 110 - Q_0 OR Q_1
            "7": "UNKNOWN_7", # 111 - Not defined in specification
        }

        # LaTeX operators for BGC gates
        self.latex_ops = {
            "AND": "\\land",
            "OR": "\\lor", 
            "XOR": "\\oplus",
            "NOT": "\\sim",
            "NOT_Q0": "\\sim",
            "NOT_Q1": "\\sim",
        }

    def parse_stp_output(self, file_path: str) -> Dict[str, Any]:
        """Parse STP solver output file."""
        result_dict = {}
        metadata = {}

        try:
            with open(file_path, "r") as file:
                text = file.read()

            # Extract execution time
            time_match = re.search(r"Execution time:\s*([\d.]+)s", text)
            if time_match:
                metadata["execution_time"] = float(time_match.group(1))

            # Extract satisfiable status
            if "Satisfiable: True" in text:
                metadata["satisfiable"] = True
            elif "Satisfiable: False" in text:
                metadata["satisfiable"] = False

            # Extract success status
            if "Success: True" in text:
                metadata["success"] = True
            elif "Success: False" in text:
                metadata["success"] = False

            # Extract timestamp if available
            timestamp_match = re.search(r"Timestamp:\s*(.+)", text)
            if timestamp_match:
                metadata["timestamp"] = timestamp_match.group(1).strip()

            # Extract ASSERT statements
            matches = re.findall(
                r"ASSERT\(\s*([^=]+)\s*=\s*(0x[0-9A-Fa-f]+|0bin[01]+)\s*\);", text
            )

            for var_name, value in matches:
                var_name = var_name.strip()
                
                # Convert binary values to hex for consistency
                if value.startswith("0bin"):
                    binary_str = value[4:]  # Remove '0bin'
                    hex_value = f"{int(binary_str, 2):02X}"
                else:
                    hex_value = value[2:].upper()  # Remove '0x'
                    
                result_dict[var_name] = hex_value

            # Add metadata to result
            result_dict["_metadata"] = metadata

        except Exception as e:
            print(f"Error parsing file: {e}")

        return result_dict

    def organize_variables(self, result_dict: Dict[str, Any]) -> Dict[str, List[str]]:
        """Organize variables by type."""
        arrays = {}

        for var_name, value in result_dict.items():
            # Skip metadata
            if var_name == "_metadata":
                continue
                
            # Extract variable type and index
            if "_" in var_name:
                var_type, index_str = var_name.split("_", 1)
                try:
                    index = int(index_str)

                    if var_type not in arrays:
                        arrays[var_type] = {}

                    arrays[var_type][index] = value
                except ValueError:
                    continue

        # Sort arrays by index
        for var_type in arrays:
            arrays[var_type] = [item[1] for item in sorted(arrays[var_type].items())]

        return arrays

    def analyze_bgc_structure(self, arrays: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Analyze BGC circuit structure and gate count.
        
        Args:
            arrays: Organized variables from STP output
            
        Returns:
            Dictionary containing BGC analysis results
        """
        if "B" not in arrays:
            return {"error": "No gate type information (B array) found"}

        gate_analysis = []
        total_gates = len(arrays["B"])
        gate_count = {}
        
        try:
            for i, gate_type_hex in enumerate(arrays["B"]):
                # Convert hex to BGC gate type
                gate_type = self._decode_bgc_gate(gate_type_hex)
                
                gate_analysis.append({
                    "index": i,
                    "gate_type": gate_type,
                    "hex_value": gate_type_hex,
                    "binary_encoding": self._hex_to_binary(gate_type_hex)
                })
                
                gate_count[gate_type] = gate_count.get(gate_type, 0) + 1

        except Exception as e:
            return {"error": f"Error analyzing BGC structure: {e}"}

        # Calculate circuit depth if structure information is available
        circuit_depth = self._estimate_circuit_depth(arrays)

        return {
            "total_gates": total_gates,
            "gate_analysis": gate_analysis,
            "gate_count": gate_count,
            "circuit_depth": circuit_depth,
            "optimization_method": "BGC (Boolean Gate Count)",
        }

    def _decode_bgc_gate(self, hex_value: str) -> str:
        """Decode BGC gate type from hex value using correct BGC encoding."""
        try:
            int_val = int(hex_value, 16)
            # Use only the lower 3 bits for BGC encoding B[2:0]
            bgc_bits = int_val & 0x07
            key = str(bgc_bits)
            
            return self.bgc_gate_types.get(key, f"UNKNOWN_{hex_value}")
                
        except ValueError:
            return f"UNKNOWN_{hex_value}"

    def _hex_to_binary(self, hex_value: str) -> str:
        """Convert hex value to binary representation."""
        try:
            int_val = int(hex_value, 16)
            return f"0bin{int_val:03b}"
        except ValueError:
            return f"INVALID_{hex_value}"

    def _estimate_circuit_depth(self, arrays: Dict[str, List[str]]) -> Optional[int]:
        """Estimate circuit depth from variable dependencies."""
        # This is a simplified estimation - actual depth would require 
        # analyzing the Q (input selection) variables
        if "T" in arrays and "Q" in arrays:
            # For BGC, depth is typically the number of gate levels
            return len(arrays["T"])
        return None

    def generate_formulas(
        self, arrays: Dict[str, List[str]], output_format: str = "human"
    ) -> List[str]:
        """Generate Boolean formulas from organized variables."""
        required_keys = ["X", "Y", "B", "T", "Q"]
        if not all(key in arrays for key in required_keys):
            missing = [key for key in required_keys if key not in arrays]
            print(f"Warning: Missing variable types: {missing}")
            return []

        X, Y, B, T, Q = arrays["X"], arrays["Y"], arrays["B"], arrays["T"], arrays["Q"]
        formulas = []

        # Generate intermediate variable formulas (T_i)
        for i, gate_type_hex in enumerate(B):
            if i * 2 + 1 >= len(Q):
                break

            # BGC uses 2 Q variables per gate
            q1_idx = i * 2
            q2_idx = i * 2 + 1
            
            if q1_idx < len(Q) and q2_idx < len(Q):
                q1, q2 = Q[q1_idx], Q[q2_idx]

                # Find variable names
                q1_name = self._find_variable_name(q1, X, T, i)
                q2_name = self._find_variable_name(q2, X, T, i)

                # Get gate type
                gate_type = self._decode_bgc_gate(gate_type_hex)

                # Generate formula
                formula = self._generate_bgc_gate_formula(
                    i, gate_type, q1_name, q2_name, output_format
                )
                if formula:
                    formulas.append(formula)

        # Generate output variable formulas (Y_i)
        for i, y_value in enumerate(Y):
            if y_value in T:
                t_index = T.index(y_value)
                if output_format == "latex":
                    formulas.append(f"Y_{{{i}}} = T_{{{t_index}}}")
                else:
                    formulas.append(f"Y{i} = T{t_index}")
            elif y_value in X:
                x_index = X.index(y_value)
                if output_format == "latex":
                    formulas.append(f"Y_{{{i}}} = X_{{{x_index}}}")
                else:
                    formulas.append(f"Y{i} = X{x_index}")

        return formulas

    def _find_variable_name(
        self, value: str, X: List[str], T: List[str], current_t_index: int
    ) -> str:
        """Find the variable name for a given value."""
        if value in X:
            return f"X_{X.index(value)}"
        elif value in T:
            index = T.index(value)
            if index < current_t_index:
                return f"T_{index}"
        return f"VAR_{value}"

    def _generate_bgc_gate_formula(
        self,
        index: int,
        gate_type: str,
        q1_name: str,
        q2_name: str,
        output_format: str,
    ) -> str:
        """Generate formula for a specific BGC gate."""
        if output_format == "latex":
            t_var = f"T_{{{index}}}"
            q1_var = q1_name.replace("_", "_{") + "}" if "_" in q1_name else q1_name
            q2_var = q2_name.replace("_", "_{") + "}" if "_" in q2_name else q2_name
        else:
            t_var = f"T{index}"
            q1_var = q1_name
            q2_var = q2_name

        # Handle specific BGC gate types based on encoding
        if gate_type == "NOT_Q0":  # 001: ~Q_0
            op = "\\sim" if output_format == "latex" else "NOT"
            return f"{t_var} = {op} {q1_var}"
        elif gate_type == "NOT_Q1":  # 011: ~Q_1  
            op = "\\sim" if output_format == "latex" else "NOT"
            return f"{t_var} = {op} {q2_var}"
        elif gate_type == "XOR":  # 010: Q_0 XOR Q_1
            if output_format == "latex":
                op = self.latex_ops.get("XOR", "XOR")
                return f"{t_var} = {q1_var} {op} {q2_var}"
            else:
                return f"{t_var} = {q1_var} XOR {q2_var}"
        elif gate_type == "AND":  # 100: Q_0 AND Q_1
            if output_format == "latex":
                op = self.latex_ops.get("AND", "AND")
                return f"{t_var} = {q1_var} {op} {q2_var}"
            else:
                return f"{t_var} = {q1_var} AND {q2_var}"
        elif gate_type == "OR":  # 110: Q_0 OR Q_1
            if output_format == "latex":
                op = self.latex_ops.get("OR", "OR")
                return f"{t_var} = {q1_var} {op} {q2_var}"
            else:
                return f"{t_var} = {q1_var} OR {q2_var}"
        elif gate_type == "ZERO":  # 000: Zero function
            return f"{t_var} = 0"
        else:
            return f"{t_var} = {gate_type}({q1_var}, {q2_var})"

    def format_output(
        self,
        file_path: str,
        output_format: str = "human",
        show_variables: bool = False,
        show_analysis: bool = True,
    ) -> str:
        """Format STP output file into readable BGC formulas."""
        result_dict = self.parse_stp_output(file_path)
        if not result_dict:
            return "Error: No variables found in output"

        metadata = result_dict.get("_metadata", {})
        arrays = self.organize_variables(result_dict)
        formulas = self.generate_formulas(arrays, output_format)

        lines = [
            "=== BGC Boolean Circuit Formula ===",
            f"Source: {os.path.basename(file_path)}",
            f"Format: {output_format}",
        ]

        # Add execution metadata
        if metadata:
            lines.append("")
            lines.append("=== Execution Information ===")
            
            if "execution_time" in metadata:
                lines.append(f"Execution Time: {metadata['execution_time']:.3f}s")
                
            if "satisfiable" in metadata:
                status = "SAT" if metadata["satisfiable"] else "UNSAT"
                lines.append(f"Result: {status}")
                
            if "success" in metadata:
                lines.append(f"Success: {metadata['success']}")
                
            if "timestamp" in metadata:
                lines.append(f"Timestamp: {metadata['timestamp']}")

        lines.append("")

        # Add BGC analysis
        if show_analysis:
            bgc_info = self.analyze_bgc_structure(arrays)
            if "error" in bgc_info:
                lines.append(f"BGC Analysis Error: {bgc_info['error']}")
            else:
                lines.extend([
                    "=== BGC Gate Count Analysis ===",
                    f"Optimization Method: {bgc_info['optimization_method']}",
                    f"Total Gates: {bgc_info['total_gates']}",
                ])
                
                if bgc_info['circuit_depth']:
                    lines.append(f"Estimated Circuit Depth: {bgc_info['circuit_depth']}")
                
                lines.extend([
                    "",
                    "Gate Count by Type:",
                ])

                for gate_type, count in sorted(bgc_info["gate_count"].items()):
                    lines.append(f"  {gate_type}: {count}")

                lines.append("")

                if show_variables:
                    lines.append("Detailed Gate Analysis:")
                    for gate_info in bgc_info["gate_analysis"]:
                        lines.append(
                            f"  Gate {gate_info['index']}: {gate_info['gate_type']} "
                            f"(0x{gate_info['hex_value']}, {gate_info['binary_encoding']})"
                        )
                    lines.append("")

        if show_variables:
            lines.append("Variable Assignments:")
            for var_type, values in arrays.items():
                lines.append(f"  {var_type}: {values}")
            lines.append("")

        if formulas:
            lines.append("BGC Circuit Formulas:")
            for formula in formulas:
                lines.append(f"  {formula}")
        else:
            lines.append("No formulas could be generated")

        return "\n".join(lines)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate BGC Boolean formulas from STP solver output"
    )
    parser.add_argument("input_file", help="STP solver output file")
    parser.add_argument(
        "--format", choices=["human", "latex"], default="human", help="Output format"
    )
    parser.add_argument(
        "--show-variables", action="store_true", help="Show variable assignments"
    )
    parser.add_argument(
        "--no-analysis", action="store_true", help="Disable BGC gate analysis"
    )
    parser.add_argument("--output", "-o", help="Output file (default: print to stdout)")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    generator = BGCFormulaGenerator()
    output = generator.format_output(
        args.input_file,
        args.format,
        args.show_variables,
        not args.no_analysis,
    )

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"BGC formulas written to: {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            return 1
    else:
        print(output)

    return 0


if __name__ == "__main__":
    exit(main())