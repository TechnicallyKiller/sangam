"""Training loops: centralised, local-only, FedAvg, median, and Sangam (+DP, +attacks)."""
import numpy as np

from model import init_params, per_example_grads, predict_proba, N_PARAMS
from privacy import dp, secagg
from strategy import (aggregation_weights, bound_norms, score_updates,
                      update_reputation, INIT_REP)


def sgd_epochs(w, X, y, rng, epochs, batch, lr):
    w = w.copy()
    n = len(X)
    for _ in range(epochs):
        order = rng.permutation(n)
        for s in range(0, n, batch):
            i = order[s:s + batch]
            w -= lr * per_example_grads(w, X[i], y[i]).mean(0)
    return w


def local_update(w, X, y, rng, cfg, sigma=None):
    if sigma is None:
        return sgd_epochs(w, X, y, rng, cfg["local_epochs"], cfg["batch_size"], cfg["lr"]) - w
    return dp.dp_sgd_epochs(w, X, y, rng, cfg["local_epochs"], cfg["batch_size"], cfg["lr"],
                            cfg["dp"]["max_grad_norm"], sigma) - w


def malicious_update(kind, w, X, y, rng, cfg, prev_norm):
    if kind == "label_flip":
        return local_update(w, X, 1 - y, rng, cfg)
    if kind == "sign_flip":
        return -5 * local_update(w, X, y, rng, cfg)
    if kind == "free_rider":
        v = rng.normal(size=N_PARAMS)
        return v / np.linalg.norm(v) * max(prev_norm, 1e-3)
    raise ValueError(kind)


def run_federated(split, cfg, rng, method="fedavg", attack=None, epsilon=None, seed=0):
    """method: fedavg | median | sangam. Hospital 4 (index -1) is malicious when attack is set.
    Returns (final weights, per-round weight given to the last hospital)."""
    k = len(split.hospitals)
    sizes = np.array([len(h[1]) for h in split.hospitals], float)
    w = init_params(rng)
    rep = np.full(k, INIT_REP)
    sigmas = [None] * k
    if epsilon is not None:
        for i, n in enumerate(sizes):
            q = min(1.0, cfg["batch_size"] / n)
            steps = cfg["rounds"] * cfg["local_epochs"] * max(1, round(n / cfg["batch_size"]))
            sigmas[i] = dp.calibrate_sigma(q, steps, epsilon, cfg["dp"]["target_delta"])
    prev_norm, last_weight = 0.0, []
    for t in range(cfg["rounds"]):
        deltas = []
        for i, (X, y) in enumerate(split.hospitals):
            if attack and i == k - 1:
                deltas.append(malicious_update(attack, w, X, y, rng, cfg, prev_norm))
            else:
                deltas.append(local_update(w, X, y, rng, cfg, sigmas[i]))
        if method == "fedavg":
            omega = sizes / sizes.sum()
            step = sum(o * d for o, d in zip(omega, deltas))
        elif method == "median":
            omega = None
            step = np.median(np.stack(deltas), axis=0)
        else:  # sangam
            scores = score_updates(w, deltas, split.X_val, split.y_val)
            rep = update_reputation(rep, scores)
            omega = aggregation_weights(rep, sizes)
            bounded = bound_norms(deltas)
            scaled = [o * b for o, b in zip(omega, bounded)]
            masked = secagg.mask_updates(scaled, seed * 1000 + t, cfg["secagg"]["fixed_point_bits"])
            step = secagg.unmask_sum(masked, cfg["secagg"]["fixed_point_bits"])
        last_weight.append(float(omega[-1]) if omega is not None else float("nan"))
        w = w + step
        prev_norm = float(np.linalg.norm(step))
    return w, last_weight


def run_centralised(split, cfg, rng):
    w = init_params(rng)
    return sgd_epochs(w, split.X_train, split.y_train, rng,
                      cfg["rounds"] * cfg["local_epochs"], cfg["batch_size"], cfg["lr"])


def run_local_only(split, cfg, rng):
    return [sgd_epochs(init_params(rng), X, y, rng, cfg["rounds"] * cfg["local_epochs"],
                       cfg["batch_size"], cfg["lr"]) for X, y in split.hospitals]


def evaluate(w, X, y):
    from sklearn.metrics import f1_score, roc_auc_score
    p = predict_proba(w, X)
    return {"acc": 100 * float(np.mean((p > 0.5) == y)),
            "auc": 100 * float(roc_auc_score(y, p)),
            "f1": 100 * float(f1_score(y, p > 0.5))}
