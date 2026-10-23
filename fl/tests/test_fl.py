import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np

from model import N_PARAMS, init_params, loss, per_example_grads
from privacy import dp, secagg
from strategy import aggregation_weights, update_reputation


def test_param_count():
    assert N_PARAMS == 513 and len(init_params(np.random.default_rng(0))) == 513


def test_gradient_matches_finite_difference():
    rng = np.random.default_rng(1)
    w, X, y = init_params(rng), rng.normal(size=(5, 30)), rng.integers(0, 2, 5).astype(float)
    g = per_example_grads(w, X, y).mean(0)
    for i in rng.choice(513, 8, replace=False):
        e = np.zeros(513); e[i] = 1e-5
        num = (loss(w + e, X, y) - loss(w - e, X, y)) / 2e-5
        assert abs(num - g[i]) < 1e-5


def test_secagg_masks_cancel_and_hide():
    rng = np.random.default_rng(2)
    ups = [rng.normal(0, 0.1, 513) for _ in range(4)]
    masked = secagg.mask_updates(ups, seed=7)
    assert np.abs(secagg.unmask_sum(masked) - sum(ups)).max() < 1e-5
    assert abs(np.corrcoef(masked[0].astype(float), ups[0])[0, 1]) < 0.2


def test_epsilon_monotone_and_calibration():
    assert dp.epsilon(0.05, 2.0, 100, 1e-5) < dp.epsilon(0.05, 1.0, 100, 1e-5)
    s = dp.calibrate_sigma(0.05, 600, 4.0, 1e-5)
    assert dp.epsilon(0.05, s, 600, 1e-5) <= 4.0 + 1e-6


def test_reputation_rule():
    r = update_reputation(np.array([.5, .5, .5]), np.array([.9, .9, .1]))
    assert np.allclose(r, [.58, .58, .25])
    w = aggregation_weights(np.array([.5, .5, .1]), np.array([100., 100., 100.]))
    assert w[2] == 0 and abs(w.sum() - 1) < 1e-12
