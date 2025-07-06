## Introduction

This project utilizes SMT (Satisfiability Modulo Theories) solvers, also known as constraint solvers, to analyze S-boxes, which are fundamental components used in cryptography.

## Setup

For detailed installation instructions for Bitwuzla and STP solvers, see [setup.md](docs/setup.md).

## S-box Optimization Framework

This project includes a comprehensive S-box optimization framework supporting multiple optimization methods:

### **GEC (Gate Equivalent Circuit) Optimization**
- Focus on minimizing gate equivalent cost using technology-specific models
- Support for UMC 180nm and SMIC 130nm process technologies
- Complex gate types (XOR3, MAOI1, MOAI1) for advanced optimization

### **BGC (Boolean Gate Count) Optimization** 
- Focus on minimizing the number of Boolean gates
- Direct gate count optimization for hardware implementations
- Simpler gate model with AND, NOT, XOR operations

### Key Features

- **Modular Design**: Separated concerns with distinct modules for gate libraries, S-box conversion, constraint generation, and optimization
- **Multiple Search Strategies**: From quick optimization to exhaustive analysis  
- **Dual Optimization Methods**: Both GEC and BGC approaches available
- **Multi-threading Support**: Parallel solver execution for improved performance
- **Comprehensive Logging**: Debug and trace the optimization process
- **Flexible API**: Easy-to-use command line interface and Python API

### Usage Examples

#### GEC Optimization (Command Line)

```bash
# Find first solution for a 3-bit S-box
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6

# Find all solutions within constraints
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --max-gates 6 --find-all

# Find all solutions for exactly 4 gates
python gec_cli.py --sbox "0,1,3,6,7,4,5,2" --bit-num 3 --exact-gates 4
```

#### BGC Optimization (Command Line)

```bash
# Find minimal gate count for a 4-bit S-box (QARMAv2)
python bgc_cli.py --sbox "4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10" --bit-num 4 --max-gates 20

# Find all solutions within constraints
python bgc_cli.py --sbox "4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10" --bit-num 4 --max-gates 15 --find-all

# Use parallel optimization
python bgc_cli.py --sbox "4,7,9,11,12,6,14,15,0,5,1,13,8,3,2,10" --bit-num 4 --max-gates 20 --parallel
```

#### Python API

```python
# GEC Optimization
from solver import GECOptimizer

gec_optimizer = GECOptimizer(bit_num=3, stp_path="stp", threads=20)
gec_results = gec_optimizer.optimize_sbox(
    sbox=[0x0, 0x1, 0x3, 0x6, 0x7, 0x4, 0x5, 0x2],
    max_gates=6,
    max_gec=40,
    technology=0,  # UMC 180nm
    gate_list=["XOR", "AND", "OR", "NOT", "NAND", "NOR"],
    output_dir="./gec_results",
    cipher_name="my_sbox"
)

# BGC Optimization  
from solver import BGCOptimizer

bgc_optimizer = BGCOptimizer(bit_num=4, stp_path="stp", threads=20)
bgc_results = bgc_optimizer.optimize_sbox(
    sbox=[4, 7, 9, 11, 12, 6, 14, 15, 0, 5, 1, 13, 8, 3, 2, 10],
    max_gates=20,
    max_depth=5,
    output_dir="./bgc_results", 
    cipher_name="qarmav2",
    stop_on_first=True
)

# Access results
if bgc_results["best_solution"]:
    best = bgc_results["best_solution"]
    print(f"BGC solution: {best.gate_count} gates, depth {best.depth}")
    print(f"Structure: {best.structure}")
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

### **Formula Generation and Analysis**

After optimization, you can generate readable Boolean formulas from the STP solver output using the included formula generators:

#### GEC Formula Generation

```bash
# Generate human-readable formulas with cost analysis
python utils/formula_gec.py gec_output/my_sbox/my_sbox_d_3_2_1.txt

# Generate LaTeX format for academic papers
python utils/formula_gec.py gec_output/my_sbox/my_sbox_d_3_2_1.txt --format latex

# Show detailed variable assignments and gate costs
python utils/formula_gec.py gec_output/my_sbox/my_sbox_d_3_2_1.txt --show-variables

# Save to file and specify technology
python utils/formula_gec.py gec_output/my_sbox/my_sbox_d_3_2_1.txt -o formulas.txt --technology 1
```

#### BGC Formula Generation

```bash
# Generate Boolean formulas with gate count analysis
python utils/formula_bgc.py output_bgc/qarmav2/bgc_6_111111_0.txt

# Generate LaTeX format with detailed analysis
python utils/formula_bgc.py output_bgc/qarmav2/bgc_6_111111_0.txt --format latex --show-variables

# Save analysis to file
python utils/formula_bgc.py output_bgc/qarmav2/bgc_6_111111_0.txt -o bgc_analysis.txt
```

#### Formula Output Features

Both formula generators provide:

- **Execution Information**: Solver execution time, satisfiability status, timestamps
- **Gate Analysis**: Gate count breakdown by type, circuit structure analysis
- **Boolean Formulas**: Human-readable circuit equations (e.g., `T0 = X_0 XOR X_1`)
- **LaTeX Support**: Mathematical notation for academic publications
- **Cost Analysis**: Gate equivalent costs (GEC) or gate counts (BGC)

#### Example Output

```
=== BGC Boolean Circuit Formula ===
Source: bgc_6_111111_0.txt
Format: human

=== Execution Information ===
Execution Time: 0.045s
Result: SAT
Success: True

=== BGC Gate Count Analysis ===
Optimization Method: BGC (Boolean Gate Count)
Total Gates: 6

Gate Count by Type:
  XOR: 3
  AND: 2
  OR: 1

BGC Circuit Formulas:
  T0 = X_0 XOR X_1
  T1 = X_2 AND T0
  T2 = T1 OR X_3
  Y0 = T2
  Y1 = T0
```

For detailed documentation and advanced usage examples, see [example.md](docs/example.md).
