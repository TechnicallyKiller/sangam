"""Execute and export a real local-EVM run for the dashboard and defence."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
from backend.app.store import Store
from backend.app.engine import Engine


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=30)
    p.add_argument("--attack", choices=["none", "label_flip", "sign_flip", "free_rider"], default="none")
    p.add_argument("--no-dp", action="store_true")
    a = p.parse_args()
    engine = Engine(Store())
    engine.initialize(a.attack, not a.no_dp)
    for _ in range(min(a.rounds, engine.cfg["rounds"])):
        engine.round()
        r = engine.snapshot()["rounds"][-1]
        print(f"Round {r['id']}: accuracy={r['accuracy']:.2f}%, txs={len(r['txs'])}, gas={sum(t['gas'] for t in r['txs'])}", flush=True)
    s = engine.snapshot()
    s.update(running=False, archived=True)
    (ROOT / "submission").mkdir(exist_ok=True)
    (ROOT / "submission" / f"integrated-{a.attack}.json").write_text(json.dumps(s, indent=2, allow_nan=False))
    public = ROOT / "frontend/public"
    public.mkdir(exist_ok=True)
    (public / "evidence.json").write_text(json.dumps(s, separators=(",", ":"), allow_nan=False))
    print("Saved measured run and public read-only evidence")


if __name__ == "__main__":
    main()
