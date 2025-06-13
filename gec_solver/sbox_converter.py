"""
S-box converter module for handling S-box transformations and bit decomposition.
"""

import logging
from typing import List, Tuple
from .utils import validate_sbox


class SboxConverter:
    """
    Handles S-box conversions and bit decomposition operations.
    """

    def __init__(self, bit_num: int):
        """
        Initialize S-box converter.

        Args:
            bit_num: Number of bits for the S-box
        """
        self.bit_num = bit_num
        self.size = 2**bit_num
        self.logger = logging.getLogger("gec_solver.sbox_converter")

        # Matrix for bit decomposition [bit_index][value_index]
        self.decomposition_matrix = [
            [0 for _ in range(self.size)] for _ in range(bit_num)
        ]

        self.logger.info(
            f"Initialized S-box converter for {bit_num}-bit S-box (size: {self.size})"
        )

    def validate_sbox(self, sbox: List[int]) -> bool:
        """
        Validate S-box structure and values.

        Args:
            sbox: S-box values

        Returns:
            True if valid, False otherwise
        """
        is_valid = validate_sbox(sbox, self.bit_num)
        if is_valid:
            self.logger.info("S-box validation passed")
        else:
            self.logger.error("S-box validation failed")
        return is_valid

    def decompose_input(self) -> List[List[int]]:
        """
        Decompose input values (0, 1, 2, ..., size-1) into bit representation.

        Returns:
            Matrix of input bit decomposition
        """
        self.logger.debug("Decomposing input values")

        for i in range(self.size):
            temp = i
            for j in range(self.bit_num - 1, -1, -1):
                self.decomposition_matrix[j][i] = temp % 2
                temp //= 2

        self.logger.debug(f"Input decomposition completed: {self.decomposition_matrix}")
        return [row.copy() for row in self.decomposition_matrix]

    def decompose_output(self, sbox: List[int]) -> List[List[int]]:
        """
        Decompose S-box output values into bit representation.

        Args:
            sbox: S-box values

        Returns:
            Matrix of output bit decomposition
        """
        if not self.validate_sbox(sbox):
            raise ValueError("Invalid S-box provided")

        self.logger.debug("Decomposing S-box output values")

        output_matrix = [[0 for _ in range(self.size)] for _ in range(self.bit_num)]

        for i in range(self.size):
            temp = sbox[i]
            for j in range(self.bit_num - 1, -1, -1):
                output_matrix[j][i] = temp % 2
                temp //= 2

        self.logger.debug(f"Output decomposition completed: {output_matrix}")
        return output_matrix

    def get_input_bits(self, bit_index: int) -> List[int]:
        """
        Get input bits for a specific bit position.

        Args:
            bit_index: Bit position index

        Returns:
            List of bits for the specified position
        """
        if bit_index < 0 or bit_index >= self.bit_num:
            raise ValueError(f"Invalid bit index: {bit_index}")

        # Ensure input decomposition is done
        self.decompose_input()
        return self.decomposition_matrix[bit_index].copy()

    def get_output_bits(self, sbox: List[int], bit_index: int) -> List[int]:
        """
        Get output bits for a specific bit position.

        Args:
            sbox: S-box values
            bit_index: Bit position index

        Returns:
            List of bits for the specified position
        """
        if bit_index < 0 or bit_index >= self.bit_num:
            raise ValueError(f"Invalid bit index: {bit_index}")

        output_matrix = self.decompose_output(sbox)
        return output_matrix[bit_index]

    def format_bit_vector(self, bits: List[int]) -> str:
        """
        Format bit list as CVC bit vector string.

        Args:
            bits: List of bits

        Returns:
            Formatted bit vector string
        """
        return "0bin" + "".join(str(bit) for bit in bits)

    def analyze_sbox(self, sbox: List[int]) -> dict:
        """
        Analyze S-box properties.

        Args:
            sbox: S-box values

        Returns:
            Dictionary with analysis results
        """
        if not self.validate_sbox(sbox):
            raise ValueError("Invalid S-box provided")

        analysis = {
            "size": len(sbox),
            "bit_width": self.bit_num,
            "is_permutation": len(set(sbox)) == len(sbox),
            "min_value": min(sbox),
            "max_value": max(sbox),
            "values": sbox.copy(),
        }

        # Calculate differential uniformity
        diff_table = {}
        for a in range(self.size):
            for b in range(1, self.size):  # b != 0
                diff = sbox[a] ^ sbox[a ^ b]
                key = (b, diff)
                diff_table[key] = diff_table.get(key, 0) + 1

        analysis["differential_uniformity"] = (
            max(diff_table.values()) if diff_table else 0
        )

        self.logger.info(f"S-box analysis completed: {analysis}")
        return analysis
