# GEC S-box Optimization Package

A comprehensive Python package for optimizing S-box implementations using Gate Equivalent Circuit (GEC) minimization with STP solver.

## Overview

This package refactors and enhances the original `newge.py` script into a modular, well-structured Python package that provides:

- **Modular Design**: Separated concerns into distinct modules
- **Comprehensive Logging**: Debug and trace optimization process
- **Multiple Search Strategies**: From quick optimization to exhaustive analysis
- **Flexible API**: Easy to use for different S-box optimization scenarios
- **Command Line Interface**: Ready-to-use CLI tool with advanced options
- **Extensible Architecture**: Easy to add new gate types and technologies

## Package Structure

```
gec_solver/
├── __init__.py              # Package initialization
├── utils.py                 # Utility functions and logging setup
├── gate_library.py          # Gate definitions and cost models
├── sbox_converter.py        # S-box bit decomposition and validation
├── cvc_generator.py         # CVC constraint file generation
├── stp_solver.py           # STP solver interface and result parsing
└── gec_optimizer.py        # Main optimization orchestrator
```

## Features

### 🔧 **Modular Components**

- **SboxConverter**: Handles S-box validation and bit decomposition
- **GateLibrary**: Manages gate types and technology cost models
- **CVCGenerator**: Creates constraint satisfaction problems in CVC format
- **STPSolver**: Interfaces with STP solver and parses results
- **GECOptimizer**: Orchestrates the complete optimization process

### 📊 **Technology Support**

- UMC 180nm process
- SMIC 130nm process
- Extensible for additional technologies

### 🔒 **Gate Types**

Basic gates: XOR, XNOR, AND, NAND, OR, NOR, NOT
Complex gates: XOR3, XNOR3, AND3, NAND3, OR3, NOR3, MAOI1, MOAI1

### 📝 **Comprehensive Logging**

- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- File and console output
- Detailed execution tracking
- Performance metrics

### 📈 **Multiple Search Strategies**

- **First Solution**: Fast optimization that stops on first valid result
- **Exhaustive Search**: Find all possible solutions within constraints
- **Exact Gate Analysis**: Explore all structures for specific gate count
- **Structure Exploration**: Test all depth structures systematically

## Installation

### Prerequisites

1. **STP Solver**: Install STP constraint solver

   ```bash
   # Ubuntu/Debian
   sudo apt-get install stp

   # Or build from source
   git clone https://github.com/stp/stp.git
   cd stp
   mkdir build && cd build
   cmake ..
   make
   sudo make install
   ```

2. **Python 3.7+** with standard library

### Setup

1. Clone or download the package
2. Ensure STP is in your PATH or note its location
3. The package is ready to use!

## Usage

### Command Line Interface

The easiest way to use the package is through the CLI:

```bash
# Basic usage (stops on first solution)
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6

# Find all solutions, not just the first one
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6 --find-all

# Find all solutions for exactly 4 gates
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --exact-gates 4

# Explore all structures for each gate count
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --explore-all-structures

# With specific constraints
python gec_cli.py --sbox "[0,1,3,6,7,4,5,2]" --bit-num 3 --technology 1 --gates "XOR,AND,OR" --max-gec 30

# Load from file
python gec_cli.py --sbox-file sbox.json --bit-num 3 --output-dir ./results --name my_sbox

# JSON output
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --json-output --quiet
```

#### CLI Options

```
Required:
  --sbox SBOX          S-box values as comma-separated or JSON array
  --sbox-file FILE     File containing S-box values (JSON format)
  --bit-num N          Number of input/output bits

Optimization:
  --max-gates N        Maximum number of gates (default: 6)
  --max-gec N          Maximum GEC value (default: 40)
  --technology {0,1}   Technology: 0=UMC 180nm, 1=SMIC 130nm (default: 0)
  --gates GATES        Comma-separated list of allowed gates

Search Strategy:
  --find-all           Find all solutions, not just the first one
  --explore-all-structures  Test all depth structures for each gate count
  --exact-gates N      Find all solutions for exactly N gates

Output:
  --output-dir DIR     Output directory (default: ./output_gec)
  --name NAME          Name for output files (default: sbox)
  --json-output        Output results in JSON format
  --quiet              Suppress progress output

Solver:
  --stp-path PATH      Path to STP executable (default: stp)
  --timeout SECONDS    Solver timeout (default: 300)
  --threads NUM        Number of threads for STP solver (default: 20)

Logging:
  --log-level LEVEL    DEBUG, INFO, WARNING, ERROR (default: INFO)
  --log-file FILE      Log file path (default: console only)
```

### Python API

#### Basic Optimization (Default - Stops on First Solution)

```python
from solver import GECOptimizer

# Initialize optimizer
optimizer = GECOptimizer(bit_num=3, stp_path="stp", log_level="INFO", threads=20)

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

# Analyze results
optimizer.analyze_results(results)

# Access best solution
if results["best_solution"]:
    best = results["best_solution"]
    print(f"Best solution: {best['gate_num']} gates, depth {best['depth']}")
    print(f"Structure: {best['structure']}")
    print(f"Execution time: {best['execution_time']:.3f}s")
```

#### Exhaustive Search (Find All Solutions)

```python
# Find all solutions (don't stop on first)
results = optimizer.optimize_sbox_exhaustive(
    sbox=sbox,
    max_gates=6,
    max_gec=40,
    technology=0,
    gate_list=["XOR", "AND", "OR", "NOT"],
    output_dir="./results",
    cipher_name="exhaustive_sbox",
    stop_on_first=False,  # Find all solutions
    explore_all_structures=True  # Test all depth structures
)

# Show all solutions found
if results.get("all_solutions"):
    print(f"Found {len(results['all_solutions'])} solutions:")
    for i, sol in enumerate(results['all_solutions'], 1):
        print(f"  {i}. Gates: {sol['gate_num']}, Structure: {sol['structure']}")
```

#### Find All Solutions for Specific Gate Count

```python
# Find all solutions for exactly 4 gates
results = optimizer.find_all_solutions_for_gates(
    sbox=sbox,
    gate_num=4,
    max_gec=40,
    technology=0,
    gate_list=["XOR", "AND", "OR", "NOT"],
    output_dir="./results",
    cipher_name="exact4_sbox"
)

print(f"Found {results['satisfiable_solutions']} solutions for {results['gate_num']} gates")
for sol in results['solutions']:
    print(f"  Structure: {sol['structure']}, Time: {sol['execution_time']:.3f}s")
```

### Advanced Usage

#### Custom Gate Library

```python
from solver import GateLibrary, GECOptimizer

# Extend gate library
gate_lib = GateLibrary()
custom_gates = ["XOR", "AND", "OR", "NOT"]

# Use with optimizer
optimizer = GECOptimizer(bit_num=3)
optimizer.gate_library = gate_lib

results = optimizer.optimize_sbox(
    sbox=[0,1,3,6,7,4,5,2],
    max_gates=5,
    max_gec=30,
    gate_list=custom_gates
)
```

#### Batch Processing with Different Strategies

```python
sboxes = {
    "sbox1": [0,1,3,6,7,4,5,2],
    "sbox2": [0,2,1,3,4,6,5,7],
    "identity": list(range(8))
}

optimizer = GECOptimizer(bit_num=3)

# Strategy 1: Quick optimization (first solution)
for name, sbox in sboxes.items():
    results = optimizer.optimize_sbox(
        sbox=sbox,
        max_gates=5,
        max_gec=30,
        cipher_name=f"{name}_quick"
    )
    print(f"{name} (quick): {'SUCCESS' if results['best_solution'] else 'FAILED'}")

# Strategy 2: Find all solutions for specific gate count
for name, sbox in sboxes.items():
    results = optimizer.find_all_solutions_for_gates(
        sbox=sbox,
        gate_num=4,
        max_gec=30,
        cipher_name=f"{name}_exact4"
    )
    print(f"{name} (4 gates): {results['satisfiable_solutions']} solutions found")

# Strategy 3: Exhaustive search
for name, sbox in sboxes.items():
    results = optimizer.optimize_sbox_exhaustive(
        sbox=sbox,
        max_gates=4,
        max_gec=30,
        cipher_name=f"{name}_exhaustive",
        stop_on_first=False,
        explore_all_structures=True
    )
    total_solutions = len(results.get('all_solutions', []))
    print(f"{name} (exhaustive): {total_solutions} total solutions")
```

## File Formats

### S-box Input File (JSON)

```json
{
  "name": "example_sbox",
  "bit_width": 3,
  "sbox": [0, 1, 3, 6, 7, 4, 5, 2],
  "description": "Example 3-bit S-box"
}
```

### Output Structure

The optimizer creates the following output structure:

```
output_dir/
└── cipher_name/
    ├── cipher_name_d_2_3_3_0.cvc      # CVC constraint file
    ├── cipher_name_d_2_3_3_0.txt      # Solver result
    └── ...                            # Additional depth structures
```

## Logging and Debugging

### Enable Debug Logging

```python
from solver import setup_logging

# Setup detailed logging
logger = setup_logging("DEBUG", "debug.log")

# Use with optimizer
optimizer = GECOptimizer(bit_num=3, log_level="DEBUG")
```

### Log Output Example

```
2023-06-13 10:30:15 - gec_solver.gec_optimizer - INFO - Starting S-box optimization: example_sbox
2023-06-13 10:30:15 - gec_solver.gec_optimizer - INFO - S-box: [0, 1, 3, 6, 7, 4, 5, 2]
2023-06-13 10:30:15 - gec_solver.gec_optimizer - INFO - Max gates: 6, Max GEC: 40
2023-06-13 10:30:15 - gec_solver.gec_optimizer - INFO - Technology: UMC 180nm
2023-06-13 10:30:15 - gec_solver.cvc_generator - INFO - Generating CVC file: ./results/example_sbox/example_sbox_d_2_3_3_0.cvc
2023-06-13 10:30:15 - gec_solver.stp_solver - INFO - Solving CVC file: ./results/example_sbox/example_sbox_d_2_3_3_0.cvc
2023-06-13 10:30:16 - gec_solver.stp_solver - INFO - Solver result: satisfiable=True, time=0.823s
2023-06-13 10:30:16 - gec_solver.gec_optimizer - INFO - ✓ Structure [3, 3]: SAT (0.823s)
```

## Performance

### Optimization Strategies

1. **Gate Number Ordering**: Tests gate counts in decreasing order (fewer gates = better)
2. **Multiple Search Modes**:
   - **First Solution**: Stops when first solution is found (fastest)
   - **Exhaustive Search**: Finds all possible solutions (most complete)
   - **Exact Gate Analysis**: Explores all structures for specific gate count
   - **Structure Exploration**: Tests all depth structures before trying fewer gates
3. **Structure Filtering**: Validates depth structures before solving
4. **Parallel Solving**: Uses STP's multi-threading capabilities

### STP Thread Configuration

The solver uses STP's built-in multi-threading support to improve performance. You can control the number of threads used:

#### Command Line Interface

```bash
# Use 8 threads for STP solver
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --threads 8

# Use 1 thread (sequential execution)
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --threads 1

# Use maximum available threads (default: 20)
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --threads 32
```

#### Python API

```python
# Initialize with custom thread count
optimizer = GECOptimizer(bit_num=3, threads=8)

# Initialize with sequential execution
optimizer = GECOptimizer(bit_num=3, threads=1)

# Access thread count
print(f"Using {optimizer.threads} threads")
```

#### Performance Guidelines

- **Default (20 threads)**: Good balance for most systems
- **High CPU count systems**: Use more threads (32, 64)
- **Low-memory systems**: Use fewer threads (4, 8)
- **Sequential debugging**: Use 1 thread for reproducible results
- **STP arguments**: Threads are passed as `--threads N` to STP solver

### Typical Performance

- **3-bit S-boxes**: < 1 minute
- **4-bit S-boxes**: 1-10 minutes
- **Complex constraints**: May require longer timeouts

## Troubleshooting

### Common Issues

1. **STP Not Found**

   ```
   RuntimeError: STP solver not found at: stp
   ```

   Solution: Install STP or specify correct path with `--stp-path`

2. **Invalid S-box**

   ```
   ValueError: Invalid S-box provided
   ```

   Solution: Ensure S-box is a valid permutation of correct size

3. **No Solution Found**

   - Increase `--max-gates` or `--max-gec`
   - Relax gate constraints with more gate types
   - Try different technology (`--technology 1`)
   - Use exhaustive search (`--find-all`) to verify no solutions exist
   - Try exact gate analysis (`--exact-gates N`) for specific counts

4. **Timeout Issues**
   - Increase `--timeout`
   - Reduce problem complexity (fewer gates, simpler constraints)
   - Use more specific gate constraints
   - Try default strategy first before exhaustive search
   - Use `--exact-gates` for smaller, focused problems

### Debug Mode

```bash
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --log-level DEBUG --log-file debug.log
```

## Contributing

The package is designed for extensibility:

1. **New Technologies**: Add cost matrices to `GateLibrary`
2. **New Gates**: Extend gate definitions and encoding
3. **New Solvers**: Implement solver interface
4. **New Constraints**: Extend `CVCGenerator`

## Example Output

### Basic Optimization (First Solution)

```bash
$ python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6

=== Optimization Results Analysis ===
Total attempts: 5
Satisfiable solutions: 1
Best solution:
  Gates: 4
  Depth: 2
  Structure: [2, 2]
  Execution time: 0.456s
  CVC file: ./output_gec/sbox/sbox_d_2_2_2_0.cvc
  Result file: ./output_gec/sbox/sbox_d_2_2_2_0.txt
Execution time stats:
  Min: 0.123s
  Max: 1.234s
  Avg: 0.567s
  Total: 2.835s
✓ Optimization completed successfully!
```

### Exhaustive Search (All Solutions)

```bash
$ python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 5 --find-all

=== Optimization Results Analysis ===
Total attempts: 12
Satisfiable solutions: 3
Best solution:
  Gates: 4
  Depth: 2
  Structure: [2, 2]
  Execution time: 0.456s

All solutions found (3):
  1. Gates: 4, Structure: [2, 2], Time: 0.456s
  2. Gates: 4, Structure: [1, 3], Time: 0.623s
  3. Gates: 5, Structure: [2, 3], Time: 0.789s
✓ Optimization completed successfully!
```

### Exact Gate Count Analysis

```bash
$ python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --exact-gates 4

=== Results for 4 Gates ===
Structures tested: 5
Solutions found: 2

Solutions:
  1. Structure: [2, 2], Time: 0.456s
     File: ./output_gec/sbox/sbox_d_2_2_2_0.cvc
  2. Structure: [1, 3], Time: 0.623s
     File: ./output_gec/sbox/sbox_d_2_1_3_0.cvc
```

## License

This package is based on the original research code and maintains the same licensing terms.

## Search Strategies

The package now supports multiple search strategies:

### 1. **Default Strategy (First Solution)**

- Stops when the first satisfiable solution is found
- Tests gate counts in decreasing order (fewest gates first)
- Fastest option for finding a minimal solution
- Use: `optimize_sbox()` method or CLI without special flags

### 2. **Exhaustive Search (All Solutions)**

- Finds all possible solutions within constraints
- Can explore all depth structures for each gate count
- Provides comprehensive analysis of solution space
- Use: `optimize_sbox_exhaustive()` method or CLI with `--find-all`

### 3. **Exact Gate Count Analysis**

- Finds all solutions for a specific number of gates
- Useful for comparing different circuit structures
- Provides detailed analysis of structural alternatives
- Use: `find_all_solutions_for_gates()` method or CLI with `--exact-gates N`

### 4. **Structure Exploration**

- Tests all depth structures for each gate count before moving to next
- More thorough than default but faster than full exhaustive search
- Good balance between completeness and performance
- Use: CLI with `--explore-all-structures`

### When to Use Each Strategy

**Use Default Strategy (`optimize_sbox`) when:**

- You need a quick solution for practical implementation
- You only care about finding one minimal solution
- Time is a constraint and you need fast results
- You're doing initial feasibility analysis

**Use Exhaustive Search (`optimize_sbox_exhaustive` with `stop_on_first=False`) when:**

- You're doing research and need to understand the complete solution space
- You want to compare all possible implementations
- You need to verify there are no better solutions
- You're analyzing the complexity of the S-box

**Use Exact Gate Analysis (`find_all_solutions_for_gates`) when:**

- You have a specific hardware constraint (exact gate count)
- You want to compare different structures with the same resource usage
- You're optimizing for a specific area/power target
- You need to validate design alternatives

**Use Structure Exploration (`explore_all_structures=True`) when:**

- You want thorough analysis but with some time constraints
- You need to understand structural diversity at each gate count
- You're balancing completeness with performance
- You want better coverage than default but faster than exhaustive
