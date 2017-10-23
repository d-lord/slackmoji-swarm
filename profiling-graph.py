import matplotlib.pyplot as plt
import numpy as np

"""
Documenting an unscientific performance test (the content of 'tests.py').
"""

results = {"sequential": 575.622, "connection reuse": 345.897, "aiohttp": 21.304}
methods, times = zip(*sorted(results.items()))
num_results = np.arange(len(methods))

plt.barh(num_results, times, align='center', alpha=0.5)
plt.yticks(num_results, methods)
plt.xlabel("Time (s)")
plt.title("Time to download 500 entries")

plt.show()
