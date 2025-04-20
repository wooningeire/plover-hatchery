import time

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


registry.update()
system.setup(DEFAULT_SYSTEM_NAME)


from plover_hatchery.lib.theory_presets.lapwing import theory

# We are going to increase this as the code gets faster and faster.
N_ITERS = 5

with open(r"./local-utils/out/unilex.hatchery", "r", encoding="utf-8") as file:
    entries = tuple(file.readline() for _ in range(5000))

    t0 = time.perf_counter()
    for _ in range(N_ITERS):
        lookup, reverse_lookup = theory.build_lookup(entries=entries)
    t1 = time.perf_counter()

time_elapsed = (t1 - t0) / N_ITERS
print(f"{time_elapsed * 1000:.4f} ms / iter")