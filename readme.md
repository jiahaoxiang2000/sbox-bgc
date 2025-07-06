## Introduction

This project utilizes SMT (Satisfiability Modulo Theories) solvers, also known as constraint solvers, to analyze S-boxes, which are fundamental components used in cryptography.

## Setup

For detailed installation instructions for Bitwuzla and STP solvers, see [setup.md](docs/setup.md).

## GEC S-box Optimization

This project includes a comprehensive GEC (Gate Equivalent Circuit) S-box optimization package that provides modular, well-structured tools for optimizing S-box implementations using constraint solvers.

### Key Features

- **Modular Design**: Separated concerns with distinct modules for gate libraries, S-box conversion, constraint generation, and optimization
- **Multiple Search Strategies**: From quick optimization to exhaustive analysis
- **Technology Support**: UMC 180nm and SMIC 130nm process technologies
- **Comprehensive Logging**: Debug and trace the optimization process
- **Flexible API**: Easy-to-use command line interface and Python API

### Usage Examples

#### Basic Optimization (Command Line)

```bash
# Find first solution for a 3-bit S-box
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6

# Find all solutions within constraints
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6 --find-all

# Find all solutions for exactly 4 gates
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --exact-gates 4
```

#### Python API

```python
from gec_solver import GECOptimizer

# Initialize optimizer
optimizer = GECOptimizer(bit_num=3, stp_path="stp", threads=20)

# Define S-box
sbox = [0x0, 0x1, 0x3, 0x6, 0x7, 0x4, 0x5, 0x2]

# Run optimization (stops on first solution)
results = optimizer.optimize_sbox(
    sbox=sbox,
    max_gates=6,
    max_gec=40,
    technology=0,  # UMC 180nm
    gate_list=["XOR", "AND", "OR", "NOT", "NAND", "NOR"],
    output_dir="./results",
    cipher_name="my_sbox"
)

# Access results
if results["best_solution"]:
    best = results["best_solution"]
    print(f"Best solution: {best['gate_num']} gates, depth {best['depth']}")
    print(f"Structure: {best['structure']}")
```

#### Search Strategies

**Default Strategy**: Quick optimization that stops on the first valid solution

- Use when you need fast results for practical implementation
- Best for initial feasibility analysis

**Exhaustive Search**: Find all possible solutions within constraints

- Use for research and complete solution space analysis
- Best for comparing all possible implementations

**Exact Gate Analysis**: Find all solutions for a specific gate count

- Use when you have specific hardware constraints
- Best for comparing different structures with same resource usage

For detailed documentation and advanced usage examples, see [example.md](docs/example.md).
