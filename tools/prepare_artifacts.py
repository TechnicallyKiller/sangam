"""Copy only the compiled ABI/bytecode needed at runtime, never node_modules."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "backend/compiled"
out.mkdir(parents=True, exist_ok=True)
for name in ("SangamCoordinator", "ReputationRegistry"):
    a = json.loads((root / f"contracts/artifacts/contracts/{name}.sol/{name}.json").read_text())
    (out / f"{name}.json").write_text(json.dumps({"abi": a["abi"], "bytecode": a["bytecode"]}, separators=(",", ":")))
print("Prepared two compiled contract artifacts")
