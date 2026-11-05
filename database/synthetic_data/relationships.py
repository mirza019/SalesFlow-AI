from __future__ import annotations

import numpy as np

def parent_ids(prefix: str, parent_count: int, child_count: int, rng: np.random.Generator) -> list[str]:
    """Assign every child a valid parent, spreading initial children across parents."""
    base = np.arange(child_count) % parent_count
    rng.shuffle(base)
    return [f"{prefix}{i + 1:06d}" for i in base]

def distribute(total: int, parents: int, rng: np.random.Generator) -> np.ndarray:
    """Return positive child counts whose exact sum is total."""
    if total < parents:
        raise ValueError(f"Cannot give {parents} parents at least one of {total} children")
    result = np.ones(parents, dtype=int)
    for i in rng.integers(0, parents, total - parents):
        result[i] += 1
    return result

