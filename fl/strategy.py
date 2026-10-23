"""Contribution scoring, asymmetric reputation and reputation-weighted weights (Eqs. 2-5)."""
import numpy as np

from model import loss

INIT_REP = 0.5
EXCLUDE_FRAC = 0.25


def bound_norms(deltas):
    """Clip each update to the round median norm tau."""
    norms = np.array([np.linalg.norm(d) for d in deltas])
    tau = np.median(norms)
    return [d * min(1.0, tau / (n + 1e-12)) for d, n in zip(deltas, norms)]


def score_updates(w, deltas, X_val, y_val):
    """Eq. (2)-(3): agreement with the median update times validation-loss gain."""
    bounded = bound_norms(deltas)
    m = np.median(np.stack(bounded), axis=0)
    l0 = loss(w, X_val, y_val)
    cos = np.array([b @ m / (np.linalg.norm(b) * np.linalg.norm(m) + 1e-12) for b in bounded])
    gain = np.array([(l0 - loss(w + b, X_val, y_val)) / l0 for b in bounded])
    agree = np.maximum(0, cos) / max(np.maximum(0, cos).max(), 1e-12)
    util = np.minimum(1.0, 2 / (1 + np.exp(-20 * gain)))
    return agree * util


def update_reputation(rep, scores):
    """Eq. (4): halve below half the median score, otherwise 0.8 r + 0.2 s."""
    thr = 0.5 * np.median(scores)
    return np.where(scores < thr, rep / 2, 0.8 * rep + 0.2 * scores)


def aggregation_weights(rep, sizes):
    """Exclude r < 1/4 max; weights proportional to n_k r_k, normalised."""
    active = rep >= EXCLUDE_FRAC * rep.max()
    w = np.where(active, sizes * rep, 0.0)
    return w / w.sum()
