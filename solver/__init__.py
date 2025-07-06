"""
Solver Package for S-box optimization using different methods.

This package provides tools for:
- Gate Equivalent Circuit (GEC) optimization
- Boolean Gate Complexity (BGC) optimization
- Converting S-boxes to various constraint formats
- Solving optimization problems using different solvers
- Analyzing circuit implementations
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
