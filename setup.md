# Setup Instructions

## How to Work with Bitwuzla and STP

> Historically, this project used the [STP](https://github.com/stp/stp) solver. Currently, we use _Bitwuzla_ to construct the SMT problem and _STP_ to solve it, as Bitwuzla provides a more modern and efficient interface for problem construction.

Our workflow: First construct the SMT problem using _Bitwuzla_, then solve it using _STP_.

## Prerequisites

For detailed Bitwuzla usage examples, refer to the [Bitwuzla Documentation](https://bitwuzla.github.io/docs/python/api.html). The Python interface provides comprehensive access to Bitwuzla's SMT solving capabilities.

## Environment Setup

### Bitwuzla Installation

For detailed installation instructions, see the [official installation guide](https://bitwuzla.github.io/docs/install.html).

We use the Python bindings for easier integration:

```bash
# Create and activate virtual environment with uv using Python 3.10
uv venv --python 3.10
source .venv/bin/activate

# Initialize and update git submodules (including Bitwuzla)
git submodule update --init --recursive

# Install system dependencies on Ubuntu 22.04
# GMP (GNU Multi-Precision arithmetic library) is required
sudo apt-get install -y libgmp-dev

# Install Python build dependencies (as specified in install.rst)
uv pip install "cython>=3.0.0"
uv pip install meson-python

# Build and install Bitwuzla Python bindings
cd bitwuzla
uv pip install .
cd ..

# Note: The build system will automatically download and build CaDiCaL and SymFPU
# if they are not found, as mentioned in the installation documentation.
```

### STP Installation

For STP solver installation, follow these steps:

```bash
# Install system dependencies
sudo apt-get install cmake bison flex libboost-all-dev python perl minisat

# Install the MiniSat solver

git clone https://github.com/stp/minisat
cd minisat
mkdir build && cd build
cmake ..
cmake --build .
sudo cmake --install .
command -v ldconfig && sudo ldconfig

# Clone and build STP
git clone https://github.com/stp/stp
cd stp
git submodule init && git submodule update
./scripts/deps/setup-gtest.sh
./scripts/deps/setup-outputcheck.sh
./scripts/deps/setup-minisat.sh
mkdir build
cd build
cmake ..
cmake --build .
sudo cmake --install .
```

**Note:** We use the `run_stp.sh` wrapper script to execute STP, which ensures proper library path configuration and dependency management.