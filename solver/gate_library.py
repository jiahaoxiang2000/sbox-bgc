"""
Gate library definitions and cost models for different process technologies.
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class GateDefinition:
    """Gate definition with name, binary value, and cost per technology."""

    name: str
    binary_value: str
    costs: List[str]  # Cost for different technologies


class GateLibrary:
    """
    Gate library containing gate definitions and cost models.
    """

    def __init__(self):
        self.logger = logging.getLogger("solver.gate_library")

        # Gate types and their binary encodings
        self.gate_types = [
            "XOR",
            "XNOR",
            "AND",
            "NAND",
            "OR",
            "NOR",
            "NOT",
            "NOT",
            "NOT",
            "XOR3",
            "XNOR3",
            "AND3",
            "NAND3",
            "OR3",
            "NOR3",
            "MAOI1",
            "MOAI1",
        ]

        # Binary values for gate encodings
        self.gate_values = [
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

        # Cost matrices for different process technologies
        # 0: UMC 180nm, 1: SMIC 130nm
        self.cost_matrix = [
            [  # UMC 180nm
                "0bin00001000",
                "0bin00000110",
                "0bin00000100",
                "0bin00000011",
                "0bin00000100",
                "0bin00000011",
                "0bin00000010",
                "0bin00000010",
                "0bin00000010",
                "0bin00001110",
                "0bin00001110",
                "0bin00000110",
                "0bin00000100",
                "0bin00000110",
                "0bin00000100",
                "0bin00001000",
                "0bin00000110",
            ],
            [  # SMIC 130nm
                "0bin00001000",
                "0bin00001000",
                "0bin00000101",
                "0bin00000011",
                "0bin00000101",
                "0bin00000011",
                "0bin00000011",
                "0bin00000011",
                "0bin00000011",
                "0bin00010010",
                "0bin00010011",
                "0bin00000110",
                "0bin00000110",
                "0bin00000110",
                "0bin00000110",
                "0bin00001000",
                "0bin00001000",
            ],
        ]

        self.logger.info(
            f"Initialized gate library with {len(self.gate_types)} gate types"
        )

    def get_gate_cost(self, gate_type: str, technology: int) -> str:
        """
        Get cost for a specific gate type and technology.

        Args:
            gate_type: Gate type name
            technology: Technology index (0: UMC 180nm, 1: SMIC 130nm)

        Returns:
            Binary cost string
        """
        if gate_type not in self.gate_types:
            raise ValueError(f"Unknown gate type: {gate_type}")

        if technology < 0 or technology >= len(self.cost_matrix):
            raise ValueError(f"Invalid technology index: {technology}")

        gate_index = self.gate_types.index(gate_type)
        return self.cost_matrix[technology][gate_index]

    def get_gate_value(self, gate_type: str) -> str:
        """
        Get binary value for a gate type.

        Args:
            gate_type: Gate type name

        Returns:
            Binary value string
        """
        if gate_type not in self.gate_types:
            raise ValueError(f"Unknown gate type: {gate_type}")

        gate_index = self.gate_types.index(gate_type)
        return self.gate_values[gate_index]

    def get_cost_matrix(self, technology: int) -> List[str]:
        """
        Get complete cost matrix for a technology.

        Args:
            technology: Technology index

        Returns:
            List of cost strings
        """
        if technology < 0 or technology >= len(self.cost_matrix):
            raise ValueError(f"Invalid technology index: {technology}")

        return self.cost_matrix[technology].copy()

    def validate_gate_list(self, gate_list: List[str]) -> bool:
        """
        Validate a list of gate types.

        Args:
            gate_list: List of gate type names

        Returns:
            True if all gates are valid
        """
        for gate in gate_list:
            if gate not in self.gate_types:
                self.logger.error(f"Invalid gate type: {gate}")
                return False
        return True

    def get_technology_name(self, technology: int) -> str:
        """
        Get technology name for given index.

        Args:
            technology: Technology index

        Returns:
            Technology name
        """
        tech_names = {0: "UMC 180nm", 1: "SMIC 130nm"}
        return tech_names.get(technology, f"Unknown technology {technology}")

    def get_supported_gates(self) -> List[str]:
        """
        Get list of all supported gate types.

        Returns:
            List of gate type names
        """
        return self.gate_types.copy()
