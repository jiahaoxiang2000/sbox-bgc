import os
import subprocess
import time

start_time = time.time()

with open("output.txt", "w") as f:
    order = "stp --SMTLIB2 ./smt2/midori.smt2 --threads 30 --cryptominisat  -n"
    s = os.popen(order).read()
    f.write(s)

end_time = time.time()

total_time = end_time - start_time

with open("time.log", "w") as f:
    f.write(f"Total execution time: {total_time} seconds\n")
