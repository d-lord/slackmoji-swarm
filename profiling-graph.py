import matplotlib.pyplot as plt
import numpy as np

"""
Documenting an unscientific performance test (the content of 'tests.py').
"""

results = {"sequential": 575.622, "connection reuse": 345.897, "aiohttp": 21.304}

y_pos = np.arange(len(results))
plt.barh(y_pos, [time for _, time in results.items()], align='center', alpha=0.5)
plt.yticks(y_pos, [method for method, _ in results.items()])
plt.xlabel("Time (s)")
plt.title("Time to download 500 entries")

plt.show()
