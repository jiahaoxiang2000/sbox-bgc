## Introduction

Utilize the SMT, also known as a constraint solver, to decipher the s-box, a component used in cryptography.

## How to Work with Bitwuzla and STP

> For the history of the project, the final solver used the [stp](https://github.com/stp/stp). Here, we use _Bitwuzla_ to construct the SMT problem, then use _STP_ to solve it, as Bitwuzla is a more modern and efficient solver for problem construction.

So we first use _Bitwuzla_ to construct the SMT problem, then use _STP_ to solve it.

## Environment

### Bitwuzla Installation

For Bitwuzla, a detailed installation guide can be found at the [installation page](https://bitwuzla.github.io/docs/install.html).

To make it easier to use, we utilize the Python Bindings.

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

## install the minisat solver

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

## The SMT of Bitwuzla

This document provides examples of using Bitwuzla, which can be found in the [Bitwuzla Documentation](https://bitwuzla.github.io/docs/python/api.html). These examples demonstrate how to use Bitwuzla to solve SMT problems effectively. Additionally, the Python interface allows us to leverage the capabilities that Bitwuzla offers.
