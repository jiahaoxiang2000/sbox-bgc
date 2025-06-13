#!/bin/bash
# Wrapper script for STP to ensure proper library loading

# Set library path for STP dependencies
export LD_LIBRARY_PATH="/home/xjh/py/sbox-bgc/stp/deps/cadiback:/home/xjh/py/sbox-bgc/stp/deps/cadical/build:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Run STP with all provided arguments
exec /home/xjh/py/sbox-bgc/stp/build/stp "$@"
