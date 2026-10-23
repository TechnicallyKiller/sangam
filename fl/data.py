"""Breast Cancer Wisconsin loading and the non-IID hospital partition."""
from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split


@dataclass
class Split:
    hospitals: list  # list of (X, y) per hospital
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    X_train: np.ndarray
    y_train: np.ndarray


def dirichlet_partition(y, k, alpha, min_share, rng):
    """Dirichlet label partition; every hospital gets >= min_share of each class."""
    while True:
        parts = [[] for _ in range(k)]
        for c in np.unique(y):
            idx = rng.permutation(np.flatnonzero(y == c))
            p = rng.dirichlet(alpha * np.ones(k))
            cuts = (np.cumsum(p)[:-1] * len(idx)).astype(int)
            for h, chunk in enumerate(np.split(idx, cuts)):
                parts[h].extend(chunk.tolist())
        ok = all(
            sum(y[i] == c for i in part) >= min_share * (y == c).sum()
            for part in parts
            for c in np.unique(y)
        )
        if ok:
            return [np.array(p) for p in parts]


def make_split(seed, k=4, alpha=0.5, min_share=0.08, test_frac=0.20, val_frac=0.07):
    X, y = load_breast_cancer(return_X_y=True)  # label 1 = benign
    X = X.astype(float)
    X_rest, X_test, y_rest, y_test = train_test_split(
        X, y, test_size=test_frac, stratify=y, random_state=seed
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_rest, y_rest, test_size=val_frac / (1 - test_frac), stratify=y_rest, random_state=seed
    )
    mu, sd = X_train.mean(0), X_train.std(0) + 1e-8
    X_train, X_val, X_test = [(a - mu) / sd for a in (X_train, X_val, X_test)]
    rng = np.random.default_rng(seed)
    idxs = dirichlet_partition(y_train, k, alpha, min_share, rng)
    hospitals = [(X_train[i], y_train[i]) for i in idxs]
    return Split(hospitals, X_val, y_val, X_test, y_test, X_train, y_train)
