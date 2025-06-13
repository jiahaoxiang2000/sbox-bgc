"""
CVC file generator for creating constraint satisfaction problems.
"""

import logging
import os
from typing import List, Optional, TextIO
from .sbox_converter import SboxConverter
from .gate_library import GateLibrary
from .utils import tobits, ensure_directory


class CVCGenerator:
    """
    Generates CVC constraint files for S-box optimization problems.
    """

    def __init__(self, sbox_converter: SboxConverter, gate_library: GateLibrary):
        """
        Initialize CVC generator.

        Args:
            sbox_converter: S-box converter instance
            gate_library: Gate library instance
        """
        self.sbox_converter = sbox_converter
        self.gate_library = gate_library
        self.logger = logging.getLogger("gec_solver.cvc_generator")

        self.bit_num = sbox_converter.bit_num
        self.size = sbox_converter.size

        self.logger.info("Initialized CVC generator")

    def generate_state_variables(
        self, fout: TextIO, gate_num: int, q_num: int, technology: int
    ) -> None:
        """
        Generate state variable declarations.

        Args:
            fout: Output file handle
            gate_num: Number of gates
            q_num: Number of Q variables
            technology: Technology index for cost model
        """
        self.logger.debug("Generating state variables")

        # Input variables X
        for i in range(self.bit_num):
            fout.write(f"X_{i}")
            if i == self.bit_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Output variables Y
        for i in range(self.bit_num):
            fout.write(f"Y_{i}")
            if i == self.bit_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Intermediate variables T
        for t in range(gate_num):
            fout.write(f"T_{t}")
            if t == gate_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Selection variables Q
        for i in range(q_num):
            fout.write(f"Q_{i}")
            if i == q_num - 1:
                fout.write(f" : BITVECTOR( {self.size} );\n")
            else:
                fout.write(" , ")

        # Gate type variables B
        for i in range(gate_num):
            fout.write(f"B_{i}")
            if i == gate_num - 1:
                fout.write(" : BITVECTOR( 8 );\n")
            else:
                fout.write(" , ")

        # Cost variables C
        for i in range(gate_num):
            fout.write(f"C_{i}")
            if i == gate_num - 1:
                fout.write(" : BITVECTOR( 8 );\n")
            else:
                fout.write(" , ")

        # Cost lookup table
        fout.write("Cost : ARRAY BITVECTOR(8) OF BITVECTOR(8);\n")

        # Total cost variable
        fout.write("GEC : BITVECTOR( 8 );\n")

        self._generate_cost_constraints(fout, technology)

    def _generate_cost_constraints(self, fout: TextIO, technology: int) -> None:
        """
        Generate cost lookup table constraints.

        Args:
            fout: Output file handle
            technology: Technology index
        """
        self.logger.debug(f"Generating cost constraints for technology {technology}")

        # Zero cost for invalid/unused gates
        fout.write("ASSERT( Cost[0bin00000000] = 0bin00000000 );\n")
        fout.write("ASSERT( Cost[0bin00000001] = 0bin00000000 );\n")
        fout.write("ASSERT( Cost[0bin00001000] = 0bin00000000 );\n")
        fout.write("ASSERT( Cost[0bin00001010] = 0bin00000000 );\n")
        fout.write("ASSERT( Cost[0bin00010000] = 0bin00000000 );\n")

        # Gate costs
        cost_matrix = self.gate_library.get_cost_matrix(technology)
        gate_values = self.gate_library.gate_values

        for i, (gate_val, cost) in enumerate(zip(gate_values, cost_matrix)):
            fout.write(f"ASSERT( Cost[{gate_val}] = {cost} );\n")

    def generate_trivial_constraints(
        self,
        fout: TextIO,
        sbox: List[int],
        gate_num: int,
        gate_list: Optional[List[str]] = None,
    ) -> None:
        """
        Generate trivial constraints for input/output and gate types.

        Args:
            fout: Output file handle
            sbox: S-box values
            gate_num: Number of gates
            gate_list: Optional list of allowed gate types
        """
        self.logger.debug("Generating trivial constraints")

        # Input constraints X
        input_bits = self.sbox_converter.decompose_input()
        for i in range(self.bit_num):
            fout.write(
                f"ASSERT( X_{i} = {self.sbox_converter.format_bit_vector(input_bits[i])} );\n"
            )

        # Output constraints Y
        output_bits = self.sbox_converter.decompose_output(sbox)
        for i in range(self.bit_num):
            fout.write(
                f"ASSERT( Y_{i} = {self.sbox_converter.format_bit_vector(output_bits[i])} );\n"
            )

        # Gate type constraints - apply to all gates
        if gate_list and len(gate_list) > 0 and len(gate_list) < 17:
            if not self.gate_library.validate_gate_list(gate_list):
                raise ValueError("Invalid gate types in gate_list")

            for i in range(gate_num):  # Apply to all gates
                fout.write("ASSERT(")
                for j, gate_type in enumerate(gate_list):
                    gate_val = self.gate_library.get_gate_value(gate_type)
                    fout.write(f"( B_{i}={gate_val})")
                    if j < len(gate_list) - 1:
                        fout.write(" OR ")
                fout.write(");\n")
        else:
            # Default gate type constraints - apply to all gates
            for i in range(gate_num):
                fout.write(
                    f"ASSERT( (B_{i}[7:3] = 0bin00000) OR (B_{i}[7:2] = 0bin000010) OR "
                    f"(B_{i}[7:2] = 0bin000100) OR (B_{i}[7:1] = 0bin0111011) OR "
                    f"(B_{i}[7:1] = 0bin0010000) OR (B_{i}[7:1] = 0bin1011000) );\n"
                )

    def generate_logic_constraints(
        self,
        fout: TextIO,
        gate_num: int,
        min_gec: int,
        depth: int,
        depth_structure: List[int],
    ) -> None:
        """
        Generate logic operation constraints.

        Args:
            fout: Output file handle
            gate_num: Total number of gates
            min_gec: Minimum GEC constraint
            depth: Circuit depth
            depth_structure: Gates per depth level
        """
        self.logger.debug(
            f"Generating logic constraints for depth {depth}, structure {depth_structure}"
        )

        count_q = 0
        count_t = 0
        count_b = 0

        for d in range(depth):
            self._generate_logic_sub_constraints(
                fout, depth_structure[d], count_q, count_t, d, count_b
            )
            count_q += 4 * depth_structure[d]
            count_t += depth_structure[d]
            count_b += depth_structure[d]

        # Output selection constraints
        for y in range(self.bit_num):
            fout.write("ASSERT( ")
            for i in range(gate_num):
                fout.write(f"( Y_{y} = T_{i}")
                if i == gate_num - 1:
                    fout.write("));\n")
                else:
                    fout.write(" ) OR ")

        # Cost calculation
        for i in range(gate_num):
            fout.write(f"ASSERT( C_{i} = Cost[ B_{i}] );\n")

        # Total cost constraint
        fout.write("ASSERT( GEC = BVPLUS( 8 , ")
        for i in range(gate_num):
            fout.write(f"C_{i}")
            if i == gate_num - 1:
                fout.write(" ) );\n")
            else:
                fout.write(" , ")

        # Optimization constraint
        fout.write(f"ASSERT( BVLT(GEC , 0bin{tobits(min_gec, 8)}) );\n")

    def _generate_logic_sub_constraints(
        self,
        fout: TextIO,
        gates_in_level: int,
        count_q: int,
        count_t: int,
        depth_level: int,
        count_b: int,
    ) -> None:
        """
        Generate logic constraints for a specific depth level.

        Args:
            fout: Output file handle
            gates_in_level: Number of gates in this level
            count_q: Current Q variable count
            count_t: Current T variable count
            depth_level: Current depth level
            count_b: Current B variable count
        """
        current_q = count_q
        current_t = count_t
        current_b = count_b

        for k in range(gates_in_level):
            # Generate Q variable constraints (4 inputs per gate)
            for q in range(4):
                fout.write("ASSERT( ")

                # First depth level or specific Q indices can use input variables
                if depth_level == 0 or q == 0 or q == 2:
                    for i in range(self.bit_num):
                        fout.write(f"( Q_{current_q} = X_{i})")
                        if depth_level == 0 and count_t == 0 and i == self.bit_num - 1:
                            fout.write(" );\n")
                        else:
                            fout.write(" OR ")

                    # Can also use intermediate variables
                    if not (depth_level == 0 and count_t == 0):
                        for i in range(count_t):
                            fout.write(f"( Q_{current_q} = T_{i})")
                            if i == count_t - 1:
                                fout.write(" );\n")
                            else:
                                fout.write(" OR ")
                else:
                    # Can only use intermediate variables
                    for i in range(count_t):
                        fout.write(f"( Q_{current_q} = T_{i})")
                        if i == count_t - 1:
                            fout.write(" );\n")
                        else:
                            fout.write(" OR ")

                current_q += 1

            # Generate gate operation constraint
            self._generate_gate_operation(fout, current_t, current_b, current_q - 4)
            current_t += 1
            current_b += 1

    def _generate_gate_operation(
        self, fout: TextIO, t_index: int, b_index: int, q_base: int
    ) -> None:
        """
        Generate gate operation encoding.

        Args:
            fout: Output file handle
            t_index: T variable index
            b_index: B variable index
            q_base: Base Q variable index for this gate's inputs
        """
        # Create zero and one bit vectors
        zeros = "0bin" + "0" * self.size
        ones = "0bin" + "1" * self.size

        # Complex gate operation encoding (from original code)
        fout.write(f"ASSERT( T_{t_index} = BVXOR(")
        fout.write(
            f"(IF B_{b_index}[7:7] = 0bin1 THEN ~(Q_{q_base}&Q_{q_base+1})& ~Q_{q_base+2}& Q_{q_base+3} ELSE {zeros} ENDIF ), "
        )
        fout.write(
            f"BVXOR((IF B_{b_index}[6:6] = 0bin1 THEN Q_{q_base+2} & BVXOR(Q_{q_base}, Q_{q_base+1}) ELSE {zeros} ENDIF), "
        )
        fout.write(
            f"BVXOR((IF B_{b_index}[5:5] = 0bin1 THEN Q_{q_base} & Q_{q_base+1} & Q_{q_base+2} ELSE {zeros} ENDIF), "
        )
        fout.write(
            f"BVXOR((IF B_{b_index}[4:4] = 0bin1 THEN Q_{q_base+2} ELSE {zeros} ENDIF), "
        )
        fout.write(
            f"BVXOR((IF B_{b_index}[3:3] = 0bin1 THEN Q_{q_base+1} ELSE {zeros} ENDIF), "
        )
        fout.write(
            f"BVXOR((IF B_{b_index}[2:2] = 0bin1 THEN Q_{q_base}& Q_{q_base+1} ELSE {zeros} ENDIF), "
        )
        fout.write(
            f"BVXOR((IF B_{b_index}[1:1] = 0bin1 THEN BVXOR(Q_{q_base},Q_{q_base+1}) ELSE {zeros} ENDIF), "
        )
        fout.write(f"(IF B_{b_index}[0:0] = 0bin1 THEN {ones} ELSE {zeros} ENDIF)")
        fout.write("))))))));\n")

    def generate_objective(self, fout: TextIO) -> None:
        """
        Generate objective function.

        Args:
            fout: Output file handle
        """
        fout.write("QUERY(FALSE);\nCOUNTEREXAMPLE;\n")

    def generate_cvc_file(
        self,
        filename: str,
        sbox: List[int],
        gate_num: int,
        min_gec: int,
        depth: int,
        depth_structure: List[int],
        technology: int = 0,
        gate_list: Optional[List[str]] = None,
    ) -> str:
        """
        Generate complete CVC file.

        Args:
            filename: Output filename
            sbox: S-box values
            gate_num: Number of gates
            min_gec: Minimum GEC constraint
            depth: Circuit depth
            depth_structure: Gates per depth level
            technology: Technology index
            gate_list: Optional allowed gate types

        Returns:
            Path to generated file
        """
        ensure_directory(os.path.dirname(filename))

        self.logger.info(f"Generating CVC file: {filename}")
        self.logger.debug(
            f"Parameters: gates={gate_num}, min_gec={min_gec}, depth={depth}, structure={depth_structure}"
        )

        q_num = 4 * gate_num

        with open(filename, "w") as fout:
            self.generate_state_variables(fout, gate_num, q_num, technology)
            self.generate_trivial_constraints(fout, sbox, gate_num, gate_list)
            self.generate_logic_constraints(
                fout, gate_num, min_gec, depth, depth_structure
            )
            self.generate_objective(fout)

        self.logger.info(f"CVC file generated successfully: {filename}")
        return filename
