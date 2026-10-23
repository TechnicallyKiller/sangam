"""Pairwise additive masking in fixed point (mod 2^32); masks cancel in the sum."""
import numpy as np

MOD = 1 << 32


def mask_updates(updates, seed, bits=20):
    """updates: list of float vectors (already scaled by public weights).
    Returns the masked uint32 vectors each hospital would send."""
    k, d = len(updates), len(updates[0])
    out = []
    for i, u in enumerate(updates):
        y = np.round(np.asarray(u) * (1 << bits)).astype(np.int64) % MOD
        for j in range(k):
            if j == i:
                continue
            a, b = min(i, j), max(i, j)
            m = np.random.default_rng([seed, a, b]).integers(0, MOD, d, dtype=np.int64)
            y = (y + m) % MOD if i < j else (y - m) % MOD
        out.append(y.astype(np.uint64))
    return out


def unmask_sum(masked, bits=20):
    """Aggregator: sum masked vectors mod 2^32, map to signed, rescale."""
    s = np.zeros(len(masked[0]), dtype=np.uint64)
    for y in masked:
        s = (s + y) % MOD
    s = s.astype(np.int64)
    s = np.where(s >= MOD // 2, s - MOD, s)
    return s / (1 << bits)
