import matplotlib.pyplot as plt
import numpy as np

results = {"sequential": 575.622, "connection reuse": 345.897, "aiohttp": 21.304}

y_pos = np.arange(len(results))
plt.bar(y_pos, [time for _, time in results.items()], align='center', alpha=0.5)
plt.xticks(y_pos, [method for method, _ in results.items()])
plt.ylabel("Time (s)")
plt.title("Time to download 500 entries")

plt.show()
