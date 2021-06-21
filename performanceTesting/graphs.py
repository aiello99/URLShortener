#!/usr/bin/python3

import subprocess, time
from matplotlib import pyplot as plt

def timeCommand(mode, count):
    startTime = time.perf_counter()
    p = subprocess.run(f"./batch{mode} {int(count/5)}",stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    endTime = time.perf_counter()
    runTime = endTime - startTime
    return runTime

for mode in ["Write", "Read"]:
    xs = []
    ys = []
    for count in [i*200 for i in range(3)]:
        xs.append(count)
        y = timeCommand(mode, count)
        ys.append(y)
    if mode == "Write":
        color = "red"
    else:
        color = "blue"
    plt.plot(xs,ys, color=color, marker='o',  label=mode)

plt.title("amount of time for read/writes tested using wrk")
plt.xlabel("time (seconds)")
plt.ylabel("number of read/writes")
plt.legend()
plt.savefig("graph.png")
