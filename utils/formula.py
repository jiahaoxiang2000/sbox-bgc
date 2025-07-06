#!/usr/bin/env python3
"""
Formula generator for STP solver output.

This script parses STP solver output and generates readable Boolean formulas.
"""

import re
import argparse
import os
import sys
from typing import Dict, List, Optional, Any

# Add parent directory to path to import gate_library
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from solver.gate_library import GateLibrary


class FormulaGenerator:
    """Generator for Boolean formulas from STP solver output."""

    def __init__(self):
        """Initialize the formula generator."""
        # Initialize gate library for cost calculations
        self.gate_library = GateLibrary()

        # Gate type mapping based on gate_library.py
        # Convert binary values to hex for mapping
        gate_types_list = [
            "XOR",  # 0bin00000010 -> 02
            "XNOR",  # 0bin00000011 -> 03
            "AND",  # 0bin00000100 -> 04
            "NAND",  # 0bin00000101 -> 05
            "OR",  # 0bin00000110 -> 06
            "NOR",  # 0bin00000111 -> 07
            "NOT",  # 0bin00001001 -> 09
            "NOT",  # 0bin00001011 -> 0B
            "NOT",  # 0bin00010001 -> 11
            "XOR3",  # 0bin00010010 -> 12
            "XNOR3",  # 0bin00010011 -> 13
            "AND3",  # 0bin00100000 -> 20
            "NAND3",  # 0bin00100001 -> 21
            "OR3",  # 0bin01110110 -> 76
            "NOR3",  # 0bin01110111 -> 77
            "MAOI1",  # 0bin10110000 -> B0
            "MOAI1",  # 0bin10110001 -> B1
        ]

        gate_binary_values = [
            "0bin00000010",
            "0bin00000011",
            "0bin00000100",
            "0bin00000101",
            "0bin00000110",
            "0bin00000111",
            "0bin00001001",
            "0bin00001011",
            "0bin00010001",
            "0bin00010010",
            "0bin00010011",
            "0bin00100000",
            "0bin00100001",
            "0bin01110110",
            "0bin01110111",
            "0bin10110000",
            "0bin10110001",
        ]

        # Create mapping from hex values to gate types
        self.gate_types = {}
        for i, (gate_type, binary_val) in enumerate(
            zip(gate_types_list, gate_binary_values)
        ):
            # Convert binary string to integer, then to hex
            binary_int = int(binary_val.replace("0bin", ""), 2)
            hex_val = f"{binary_int:02X}"
            self.gate_types[hex_val] = gate_type

        # Add common hex values that might appear in output
        self.gate_types.update(
            {
                "02": "XOR",
                "03": "XNOR",
                "04": "AND",
                "05": "NAND",
                "06": "OR",
                "07": "NOR",
                "09": "NOT",
                "0B": "NOT",
                "11": "NOT",
            }
        )

        # LaTeX operators
        self.latex_ops = {
            "AND": "\\land",
            "NAND": "\\overline{\\land}",
            "OR": "\\lor",
            "NOR": "\\overline{\\lor}",
            "XOR": "\\oplus",
            "XNOR": "\\overline{\\oplus}",
            "NOT": "\\sim",
            "AND3": "\\land",
            "NAND3": "\\overline{\\land}",
            "OR3": "\\lor",
            "NOR3": "\\overline{\\lor}",
            "XOR3": "\\oplus",
            "XNOR3": "\\overline{\\oplus}",
        }

    def parse_stp_output(self, file_path: str) -> Dict[str, str]:
        """Parse STP solver output file."""
        result_dict = {}

        try:
            with open(file_path, "r") as file:
                text = file.read()

            # Extract ASSERT statements
            matches = re.findall(
                r"ASSERT\(\s*([^=]+)\s*=\s*(0x[0-9A-Fa-f]+)\s*\);", text
            )

            for var_name, value in matches:
                var_name = var_name.strip()
                hex_value = value[2:].upper()
                result_dict[var_name] = hex_value

        except Exception as e:
            print(f"Error parsing file: {e}")

        return result_dict

    def organize_variables(self, result_dict: Dict[str, str]) -> Dict[str, List[str]]:
        """Organize variables by type."""
        arrays = {}

        for var_name, value in result_dict.items():
            # Skip Cost variables and GEC
            if var_name.startswith("Cost[") or var_name == "GEC":
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

    def calculate_total_cost(
        self, arrays: Dict[str, List[str]], technology: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate total GE cost for the circuit.

        Args:
            arrays: Organized variables from STP output
            technology: Technology index (0: UMC 180nm, 1: SMIC 130nm)

        Returns:
            Dictionary containing cost breakdown and total
        """
        if "B" not in arrays:
            return {"error": "No gate type information (B array) found"}

        gate_costs = []
        total_cost = 0
        gate_count = {}

        try:
            for i, gate_type_hex in enumerate(arrays["B"]):
                # Get gate type from hex value
                gate_type = self.gate_types.get(gate_type_hex.upper(), None)

                if gate_type and gate_type in self.gate_library.gate_types:
                    # Get cost from gate library
                    cost_binary = self.gate_library.get_gate_cost(gate_type, technology)
                    # Convert binary cost to integer
                    cost_value = int(cost_binary.replace("0bin", ""), 2)
                    if technology == 0:
                        cost_value = cost_value / 3  # Adjust for UMC 180nm technology

                    gate_costs.append(
                        {
                            "index": i,
                            "gate_type": gate_type,
                            "hex_value": gate_type_hex,
                            "cost": cost_value,
                        }
                    )

                    total_cost += cost_value
                    gate_count[gate_type] = gate_count.get(gate_type, 0) + 1
                else:
                    # Unknown gate type
                    gate_costs.append(
                        {
                            "index": i,
                            "gate_type": f"UNKNOWN_{gate_type_hex}",
                            "hex_value": gate_type_hex,
                            "cost": 0,
                        }
                    )

        except Exception as e:
            return {"error": f"Error calculating costs: {e}"}

        return {
            "total_cost": total_cost,
            "technology": self.gate_library.get_technology_name(technology),
            "gate_costs": gate_costs,
            "gate_count": gate_count,
            "num_gates": len(arrays["B"]),
        }

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

            q1, q2 = Q[i * 4], Q[i * 4 + 1] if i * 4 + 1 < len(Q) else None

            # Find variable names
            q1_name = self._find_variable_name(q1, X, T, i)
            q2_name = self._find_variable_name(q2, X, T, i) if q2 else None

            # Get gate type
            gate_type = self.gate_types.get(
                gate_type_hex.upper(), f"GATE_{gate_type_hex}"
            )

            # Generate formula
            formula = self._generate_gate_formula(
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

    def _generate_gate_formula(
        self,
        index: int,
        gate_type: str,
        q1_name: str,
        q2_name: Optional[str],
        output_format: str,
    ) -> str:
        """Generate formula for a specific gate."""
        if output_format == "latex":
            t_var = f"T_{{{index}}}"
            q1_var = q1_name.replace("_", "_{") + "}" if "_" in q1_name else q1_name
            q2_var = (
                q2_name.replace("_", "_{") + "}"
                if q2_name and "_" in q2_name
                else q2_name
            )
        else:
            t_var = f"T{index}"
            q1_var = q1_name
            q2_var = q2_name

        if gate_type == "NOT":
            op = "\\sim" if output_format == "latex" else "NOT"
            # For NOT gates, use the first non-zero input
            if q1_name and q1_name != "VAR_0000":
                return f"{t_var} = {op} {q1_var}"
            elif q2_var and q2_var != "VAR_0000":
                return f"{t_var} = {op} {q2_var}"
            else:
                return f"{t_var} = {op} {q1_var}"
        elif (
            gate_type
            in [
                "AND",
                "OR",
                "XOR",
                "NAND",
                "NOR",
                "XNOR",
                "AND3",
                "OR3",
                "XOR3",
                "NAND3",
                "NOR3",
                "XNOR3",
            ]
            and q2_var
        ):
            if output_format == "latex":
                op = self.latex_ops.get(gate_type, gate_type)
                return f"{t_var} = {q1_var} {op} {q2_var}"
            else:
                return f"{t_var} = {q1_var} {gate_type} {q2_var}"
        elif gate_type in ["MAOI1", "MOAI1"]:
            # Complex gates - show as function calls
            return (
                f"{t_var} = {gate_type}({q1_var}"
                + (f", {q2_var}" if q2_var else "")
                + ")"
            )
        else:
            return (
                f"{t_var} = {gate_type}({q1_var}"
                + (f", {q2_var}" if q2_var else "")
                + ")"
            )

    def format_output(
        self,
        file_path: str,
        output_format: str = "human",
        show_variables: bool = False,
        technology: int = 0,
        show_cost: bool = True,
    ) -> str:
        """Format STP output file into readable formulas."""
        result_dict = self.parse_stp_output(file_path)
        if not result_dict:
            return "Error: No variables found in output"

        arrays = self.organize_variables(result_dict)
        formulas = self.generate_formulas(arrays, output_format)

        lines = [
            "=== Boolean Circuit Formula ===",
            f"Source: {os.path.basename(file_path)}",
            f"Format: {output_format}",
            "",
        ]

        # Add cost calculation
        if show_cost:
            cost_info = self.calculate_total_cost(arrays, technology)
            if "error" in cost_info:
                lines.append(f"Cost Calculation Error: {cost_info['error']}")
            else:
                lines.extend(
                    [
                        "=== Gate Equivalent (GE) Cost Analysis ===",
                        f"Technology: {cost_info['technology']}",
                        f"Total Gates: {cost_info['num_gates']}",
                        f"Total GE Cost: {cost_info['total_cost']}",
                        "",
                        "Gate Count by Type:",
                    ]
                )

                for gate_type, count in sorted(cost_info["gate_count"].items()):
                    lines.append(f"  {gate_type}: {count}")

                lines.append("")

                if show_variables:
                    lines.append("Detailed Gate Costs:")
                    for gate_info in cost_info["gate_costs"]:
                        lines.append(
                            f"  Gate {gate_info['index']}: {gate_info['gate_type']} "
                            f"(0x{gate_info['hex_value']}) = {gate_info['cost']} GE"
                        )
                    lines.append("")

        if show_variables:
            lines.append("Variable Assignments:")
            for var_type, values in arrays.items():
                lines.append(f"  {var_type}: {values}")
            lines.append("")

        if formulas:
            lines.append("Circuit Formulas:")
            for formula in formulas:
                lines.append(f"  {formula}")
        else:
            lines.append("No formulas could be generated")

        return "\n".join(lines)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate Boolean formulas from STP solver output"
    )
    parser.add_argument("input_file", help="STP solver output file")
    parser.add_argument(
        "--format", choices=["human", "latex"], default="human", help="Output format"
    )
    parser.add_argument(
        "--show-variables", action="store_true", help="Show variable assignments"
    )
    parser.add_argument(
        "--technology",
        "-t",
        type=int,
        choices=[0, 1],
        default=0,
        help="Technology for cost calculation (0: UMC 180nm, 1: SMIC 130nm)",
    )
    parser.add_argument(
        "--no-cost", action="store_true", help="Disable cost calculation"
    )
    parser.add_argument("--output", "-o", help="Output file (default: print to stdout)")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        return 1

    generator = FormulaGenerator()
    output = generator.format_output(
        args.input_file,
        args.format,
        args.show_variables,
        args.technology,
        not args.no_cost,
    )

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Formulas written to: {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            return 1
    else:
        print(output)

    return 0


if __name__ == "__main__":
    exit(main())
