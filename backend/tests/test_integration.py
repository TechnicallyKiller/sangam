"""Exercise the actual API, training, Solidity receipts, and stored model bytes."""
import os
import tempfile
import time

os.environ["DATABASE_URL"] = ""
os.environ["SANGAM_DATA_DIR"] = tempfile.mkdtemp(prefix="sangam-test-")
os.environ["SANGAM_ADMIN_TOKEN"] = "integration-test-only"

from fastapi.testclient import TestClient
from web3 import Web3
from backend.app.main import app, engine

client = TestClient(app)
AUTH = {"Authorization": "Bearer integration-test-only"}


def test_authorization():
    assert client.get("/health").status_code == 200
    assert client.post("/rounds/open", json={}).status_code == 401
    assert client.post("/auth/check", headers=AUTH).status_code == 200
    assert client.post("/rounds/open", json={"attack": "invented"}, headers=AUTH).status_code == 400


def test_end_to_end_contract_training_and_artifact():
    assert client.post("/rounds/open", json={"privacy": True, "attack": "sign_flip", "newRun": True}, headers=AUTH).status_code == 202
    for _ in range(180):
        s = client.get("/state").json()
        if not s["running"]:
            break
        time.sleep(0.25)
    assert s["error"] is None
    r = s["rounds"][-1]
    assert r["status"] == "closed" and len(r["txs"]) == 8
    assert len(r["updates"]) == 4
    assert abs(sum(u["weight"] for u in r["updates"]) - 1) < 1e-10
    assert r["epsilonSpent"] <= 4
    assert r["epsilonByHospital"][3] is None  # attacker does not run DP
    assert r["maskingError"] < 1e-5
    for tx in r["txs"]:
        proof = client.get("/audit/verify/" + tx["hash"]).json()
        assert proof["found"] and proof["liveVerified"]
    proof = client.get("/audit/verify/" + r["globalModelHash"]).json()
    assert proof["artifactVerified"] and proof["liveVerified"]
    artifact = client.get("/models/" + r["globalCid"])
    assert artifact.status_code == 200 and len(artifact.content) == 513 * 8
    assert Web3.to_hex(Web3.keccak(artifact.content)) == r["globalModelHash"]
    assert not client.get("/audit/verify/0x" + "ff" * 32).json()["found"]
    assert client.get("/rounds/99").status_code == 404
    assert client.get("/models/not-a-cid").status_code == 400
    assert client.get("/participants").json()[0]["reputation"] == r["updates"][0]["reputationAfter"]
