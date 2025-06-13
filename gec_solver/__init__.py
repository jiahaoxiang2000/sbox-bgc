"""
GEC Solver Package for S-box Gate Equivalent Circuit optimization.

This package provides tools for:
- Converting S-boxes to CVC format
- Solving optimization problems using STP solver
- Analyzing gate equivalent circuits
"""

from .sbox_converter import SboxConverter
from .cvc_generator import CVCGenerator
from .stp_solver import STPSolver, SolverResult
from .gate_library import GateLibrary
from .gec_optimizer import GECOptimizer
from .utils import setup_logging, tobits

__version__ = "1.0.0"
__all__ = [
    "SboxConverter",
    "CVCGenerator",
    "STPSolver",
    "SolverResult",
    "GateLibrary",
    "GECOptimizer",
    "setup_logging",
    "tobits",
]
