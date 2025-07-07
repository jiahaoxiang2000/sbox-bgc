# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **BGC (Boolean Gate Count) optimization framework** - Complete implementation with serial mode
- **ANF (Algebraic Normal Form) gate model** - 4-bit gate encoding with support for NOT, XOR, AND, OR operations
- **Gate model selection** - CLI option `--gate-model` to choose between BGC (3-bit) and ANF (4-bit) encodings
- **Dual constraint generation** - Support for both BGC and ANF gate operation formulas
- **Formula generation tools** - BGC and GEC formula generators with LaTeX support and auto-detection
- **Documentation** - Comprehensive usage examples and CLI reference for formula generators

## [1.0.0] - 2025-07-06 - Complete S-box Optimization Framework

### Added

- **Comprehensive GEC (Gate Equivalent Circuit) S-box optimization framework**
  - `GECOptimizer`: Main orchestrator for optimization workflows
  - `SboxConverter`: S-box validation and bit-level decomposition
  - `CVCGenerator`: Constraint generation for STP solver
  - `GateLibrary`: Gate definitions and technology cost models
  - `STPSolver`: Interface to STP constraint solver
  - Utility functions for logging and bit manipulation

- **Search Strategies**
  - Default strategy: Quick optimization (stops on first solution)
  - Exhaustive search: Find all possible solutions within constraints
  - Exact gate analysis: Find all solutions for specific gate count
  - Structure exploration: Test all depth structures systematically

- **Technology Support**
  - UMC 180nm process technology
  - SMIC 130nm process technology
  - Extensible architecture for additional technologies

- **Gate Types**
  - Basic gates: XOR, XNOR, AND, NAND, OR, NOR, NOT
  - Complex gates: XOR3, XNOR3, AND3, NAND3, OR3, NOR3, MAOI1, MOAI1

- **CLI Interface**
  - Command-line tool `gec_cli.py` with comprehensive options
  - Support for various input formats and output configurations
  - Configurable solver parameters and optimization strategies

- **Multi-threading support in STP solver for improved performance**
- **Boolean circuit formula generation and analysis tools**
- **Comprehensive documentation with setup instructions and usage examples**
- **Architecture documentation with Mermaid diagrams**
- **Test cases for 3-bit S-boxes (test-s1, test-s2)**
- **Performance benchmarking and result validation**

### Changed

- Renamed package from `gec_solver` to `solver` for broader scope
- Restructured documentation into dedicated `docs/` directory
- Updated import paths throughout codebase to use new module structure
- Improved README with clearer structure and GEC optimization examples

### Removed

- Outdated implementation files from `old/` directory
- STP directory from git tracking (now in .gitignore)

## [v0.1.0] - 2024-01-XX - SMT to Python Conversion

### Added

- SMT-LIB v2 to Python code conversion functionality
- Basic constraint solver integration
- Initial S-box analysis capabilities
- Environment setup and reproduction scripts
- Background execution support for long-running optimizations

## [v0.0.1] - 2024-01-XX - Initial Release

### Added

- Initial project setup
- Basic BGC model testing
- Core constraint satisfaction framework
- Preliminary S-box analysis tools

---

## Development Notes

### Project Evolution

This project has evolved from a basic SMT solver integration to a comprehensive S-box optimization framework. Key milestones include:

1. **Initial SMT Integration**: Basic Bitwuzla and STP solver setup
2. **S-box Analysis**: Implementation of constraint generation for S-box optimization
3. **GEC Framework**: Complete Gate Equivalent Circuit optimization package
4. **Modular Architecture**: Separation of concerns into dedicated components
5. **Documentation**: Comprehensive documentation and usage examples

### Architecture Highlights

- **Modular Design**: Clear separation between input processing, constraint generation, solving, and analysis
- **Extensible Framework**: Easy to add new gate types, technologies, and optimization strategies
- **Comprehensive Testing**: Extensive test cases and validation for different S-box types

### Future Roadmap

- **BGC Integration**: Addition of Boolean Gate Complexity (BGC) optimization methods
- **Enhanced Solvers**: Support for additional constraint solvers
- **Advanced Analysis**: More sophisticated circuit analysis and optimization techniques
- **Performance Improvements**: Further optimization of constraint generation and solving
