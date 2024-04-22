## Introduction

Utilize the SMT, also known as a constraint solver, to decipher the s-box, a component used in cryptography.

## Environment

For Bitwuzla, a detailed installation guide can be found at the [installation page](https://bitwuzla.github.io/docs/install.html).

To make it easier to use, we utilize the Python Bindings.

```bash
# Clone Bitwuzla repository
git clone https://github.com/bitwuzla/bitwuzla
cd bitwuzla

# have some dependencies on ubuntu 22.04
sudo apt-get install -y libgmp-dev

pip install meson-python
pip install Cython
 
# Build and install Bitwuzla Python bindings
pip install .
# note the install progress need to git fetch from github, for its dependencies.
```

## The SMT of Bitwuzla 

This document provides examples of using Bitwuzla, which can be found in the [Bitwuzla Documentation](https://bitwuzla.github.io/docs/python/api.html). These examples demonstrate how to use Bitwuzla to solve SMT problems effectively. Additionally, the Python interface allows us to leverage the capabilities that Bitwuzla offers.