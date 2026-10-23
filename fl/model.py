"""30-16-1 MLP (513 parameters) with vectorised per-example gradients."""
import numpy as np

D_IN, D_H = 30, 16
N_PARAMS = D_IN * D_H + D_H + D_H + 1  # 513


def init_params(rng):
    w1 = rng.normal(0, np.sqrt(2 / D_IN), (D_IN, D_H))
    w2 = rng.normal(0, np.sqrt(1 / D_H), (D_H, 1))
    return pack(w1, np.zeros(D_H), w2, np.zeros(1))


def pack(w1, b1, w2, b2):
    return np.concatenate([w1.ravel(), b1, w2.ravel(), b2])


def unpack(w):
    a = D_IN * D_H
    return (w[:a].reshape(D_IN, D_H), w[a:a + D_H],
            w[a + D_H:a + 2 * D_H].reshape(D_H, 1), w[-1:])


def _sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def predict_proba(w, X):
    w1, b1, w2, b2 = unpack(w)
    return _sigmoid(np.maximum(X @ w1 + b1, 0) @ w2 + b2).ravel()


def loss(w, X, y):
    p = np.clip(predict_proba(w, X), 1e-7, 1 - 1e-7)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def per_example_grads(w, X, y):
    """Return (B, 513) matrix of per-example gradients of the log loss."""
    w1, b1, w2, b2 = unpack(w)
    h = np.maximum(X @ w1 + b1, 0)
    p = _sigmoid(h @ w2 + b2).ravel()
    dz2 = (p - y)[:, None]                         # (B,1)
    dh = dz2 @ w2.T * (h > 0)                      # (B,16)
    g_w1 = (X[:, :, None] * dh[:, None, :]).reshape(len(X), -1)
    return np.concatenate([g_w1, dh, h * dz2, dz2], axis=1)
