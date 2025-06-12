## Introduction

Utilize the SMT, also known as a constraint solver, to decipher the s-box, a component used in cryptography.

## Environment

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

### Required Dependencies

Based on install.rst, the following are required:

* **System Dependencies:**
  - Python >= 3.7
  - Meson >= 0.64
  - Ninja
  - GMP >= v6.1 (GNU Multi-Precision arithmetic library)

* **Python Dependencies:**
  - cython >= 3.0.0
  - meson-python

* **Auto-downloaded Dependencies:**
  - CaDiCaL >= 1.5.0 (automatically downloaded if not found)
  - SymFPU (automatically downloaded if not found)

## The SMT of Bitwuzla 

This document provides examples of using Bitwuzla, which can be found in the [Bitwuzla Documentation](https://bitwuzla.github.io/docs/python/api.html). These examples demonstrate how to use Bitwuzla to solve SMT problems effectively. Additionally, the Python interface allows us to leverage the capabilities that Bitwuzla offers.
