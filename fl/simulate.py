"""Run the evaluation grid and print mean +- SD over seeds. Writes results.json."""
import argparse
import json

import numpy as np
import yaml

from data import make_split
from fed import (evaluate, run_centralised, run_federated, run_local_only)


def load_cfg(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def one_seed(seed, cfg, experiments):
    split = make_split(seed, cfg["num_hospitals"], cfg["dirichlet_alpha"], cfg["min_class_share"])
    ev = lambda w: evaluate(w, split.X_test, split.y_test)
    rng = lambda: np.random.default_rng(seed)
    out = {}
    if "utility" in experiments:
        out["centralised"] = ev(run_centralised(split, cfg, rng()))
        locs = [ev(w) for w in run_local_only(split, cfg, rng())]
        out["local_only"] = {m: float(np.mean([l[m] for l in locs])) for m in locs[0]}
        out["fedavg"] = ev(run_federated(split, cfg, rng(), "fedavg")[0])
        out["median"] = ev(run_federated(split, cfg, rng(), "median")[0])
        out["sangam"] = ev(run_federated(split, cfg, rng(), "sangam", seed=seed)[0])
    if "privacy" in experiments:
        for eps in (1, 2, 4, 8):
            out[f"sangam_eps{eps}"] = ev(run_federated(split, cfg, rng(), "sangam", epsilon=eps, seed=seed)[0])
    if "attacks" in experiments:
        for atk in ("label_flip", "sign_flip", "free_rider"):
            for m in ("fedavg", "median", "sangam"):
                w, lw = run_federated(split, cfg, rng(), m, attack=atk, seed=seed)
                out[f"{atk}/{m}"] = {**ev(w), "h4_weight": float(np.nanmean(lw)) * 100 if m == "sangam" else float("nan")}
        _, lw = run_federated(split, cfg, rng(), "sangam", seed=seed)
        out["honest/sangam"] = {"h4_weight": float(np.mean(lw)) * 100}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--experiments", nargs="+", default=["utility", "privacy", "attacks"])
    ap.add_argument("--out", default="results.json")
    a = ap.parse_args()
    cfg = load_cfg()
    n = a.seeds or cfg["seeds"]
    runs = [one_seed(s, cfg, a.experiments) for s in range(n)]
    summary = {}
    for key in runs[0]:
        summary[key] = {m: (float(np.nanmean([r[key][m] for r in runs])),
                            float(np.nanstd([r[key][m] for r in runs])))
                        for m in runs[0][key]}
    json.dump(summary, open(a.out, "w"), indent=2)
    for key, v in summary.items():
        print(f"{key:24s}", "  ".join(f"{m}={mu:6.2f}±{sd:5.2f}" for m, (mu, sd) in v.items()))


if __name__ == "__main__":
    main()
