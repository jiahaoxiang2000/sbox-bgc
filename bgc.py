import subprocess
import time

start_time = time.time()

with open("output.txt", "w") as f:
    process = subprocess.Popen(
        [
            "stp",
            "--SMTLIB2",
            "./smt2/qarmav2.smt2",
            "--threads",
            "26",
            "--cryptominisat",
        ],
        stdout=f,
    )
    process.wait()

end_time = time.time()

total_time = end_time - start_time

with open("log.txt", "w") as f:
    f.write(f"Total execution time: {total_time} seconds\n")
