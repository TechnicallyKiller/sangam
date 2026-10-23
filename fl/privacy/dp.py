"""DP-SGD step and an RDP accountant for the Poisson-subsampled Gaussian mechanism."""
import math

import numpy as np
from scipy.special import gammaln, logsumexp  # installed with scikit-learn

from model import per_example_grads

ORDERS = list(range(2, 129))


def _log_binom(n, k):
    return gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)


def rdp_step(q, sigma, alpha):
    """RDP of one subsampled-Gaussian step at integer order alpha (Mironov et al. 2019)."""
    if q == 0:
        return 0.0
    if q >= 1:
        return alpha / (2 * sigma ** 2)
    k = np.arange(alpha + 1)
    terms = (_log_binom(alpha, k) + (alpha - k) * math.log1p(-q) + k * math.log(q)
             + (k * k - k) / (2 * sigma ** 2))
    return float(logsumexp(terms)) / (alpha - 1)


def epsilon(q, sigma, steps, delta):
    """(eps, delta)-DP after `steps` compositions, minimising over RDP orders."""
    return min(steps * rdp_step(q, sigma, a) + math.log(1 / delta) / (a - 1) for a in ORDERS)


def calibrate_sigma(q, steps, target_eps, delta, lo=0.3, hi=200.0):
    """Smallest noise multiplier whose total release satisfies target_eps."""
    for _ in range(40):
        mid = (lo + hi) / 2
        if epsilon(q, mid, steps, delta) > target_eps:
            lo = mid
        else:
            hi = mid
    return hi


def dp_sgd_epochs(w, X, y, rng, epochs, batch, lr, clip, sigma):
    """Local DP-SGD: Poisson sampling, per-example clipping, Gaussian noise."""
    n = len(X)
    q = min(1.0, batch / n)
    w = w.copy()
    for _ in range(epochs * max(1, round(n / batch))):
        mask = rng.random(n) < q
        if mask.any():
            g = per_example_grads(w, X[mask], y[mask])
            g /= np.maximum(1, np.linalg.norm(g, axis=1, keepdims=True) / clip)
            total = g.sum(0)
        else:
            total = np.zeros_like(w)
        total = total + rng.normal(0, sigma * clip, size=w.shape)
        w -= lr * total / (q * n)
    return w
