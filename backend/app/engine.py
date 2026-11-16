"""Connect measured NumPy training to real Solidity execution on a local EVM.

Hospital workers and validator/aggregator roles are logically separated here but
run in one process: an explicit, reproducible college prototype, not a deployment
in independent hospitals. Raw updates are never written to the public store.
"""
import base64
import copy
import hashlib
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path

import numpy as np
import yaml
from web3 import Web3, EthereumTesterProvider

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "fl"))
from data import make_split
from fed import evaluate, local_update, malicious_update
from model import init_params
from privacy import dp, secagg
from strategy import aggregation_weights, bound_norms, score_updates


def now():
    return int(time.time() * 1000)


def model_bytes(weights):
    return np.asarray(weights, dtype="<f8").tobytes()


def content_id(data):
    # CIDv1 + raw codec + sha2-256 multihash. Exact bytes, not a made-up CID.
    return "b" + base64.b32encode(b"\x01\x55\x12\x20" + hashlib.sha256(data).digest()).decode().lower().rstrip("=")


class Engine:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.cfg = yaml.safe_load((ROOT / "fl/config.yaml").read_text())
        self.active = False
        old = store.runs()
        self.state = old[0] if old else self.empty()
        self.state.update(running=False, archived=bool(old))
        if old:
            self.state["error"] = None
        self.w3 = None

    def empty(self):
        return {"runId": "", "createdAt": now(), "hospitals": [], "rounds": [],
                "reputation": {}, "rewards": {}, "head": 0, "running": False,
                "archived": False, "error": None, "chain": {"id": 131277322940537, "name": "Local Ethereum test chain", "symbol": "test ETH"},
                "coordinator": "", "registry": "", "aggregator": "", "totalRounds": self.cfg["rounds"],
                "epsilonBudget": 4, "storage": "Content-addressed off-chain storage",
                "mode": "local-evm", "attack": "none", "privacy": True,
                "baseline": None, "split": None}

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def save(self):
        self.store.save(self.state)

    def artifact(self, w):
        data = model_bytes(w)
        cid = content_id(data)
        self.store.model(cid, data)
        return Web3.to_hex(Web3.keccak(data)), cid

    def deploy(self, name):
        path = ROOT / f"backend/compiled/{name}.json"
        if not path.exists():
            path = ROOT / f"contracts/artifacts/contracts/{name}.sol/{name}.json"
        if not path.exists():
            raise RuntimeError("Compile contracts first: cd contracts && npm ci && npx hardhat compile")
        a = json.loads(path.read_text())
        factory = self.w3.eth.contract(abi=a["abi"], bytecode=a["bytecode"])
        receipt = self.w3.eth.wait_for_transaction_receipt(factory.constructor(self.agg).transact({"from": self.owner}))
        return self.w3.eth.contract(address=receipt.contractAddress, abi=a["abi"])

    def send(self, fn, sender, label, round_id, detail):
        txhash = fn.transact({"from": sender})
        r = self.w3.eth.wait_for_transaction_receipt(txhash)
        if r.status != 1:
            raise RuntimeError(f"{label} transaction reverted")
        b = self.w3.eth.get_block(r.blockNumber)
        return {"hash": Web3.to_hex(txhash), "fn": label, "from": sender, "round": round_id,
                "block": r.blockNumber, "gas": r.gasUsed, "ts": int(b.timestamp) * 1000, "detail": detail,
                "blockHash": Web3.to_hex(r.blockHash), "status": r.status}

    def initialize(self, attack="none", privacy=True):
        self.w3 = Web3(EthereumTesterProvider())
        accounts = self.w3.eth.accounts
        self.owner, self.agg = accounts[:2]
        self.addresses = accounts[2:6]
        self.coord = self.deploy("SangamCoordinator")
        self.reg = self.deploy("ReputationRegistry")
        self.split = make_split(0, self.cfg["num_hospitals"], self.cfg["dirichlet_alpha"], self.cfg["min_class_share"])
        self.rng = np.random.default_rng(0)
        self.w = init_params(self.rng)
        self.prev_norm = 0.0
        self.sizes = np.array([len(y) for _, y in self.split.hospitals], float)
        self.sigmas = []
        for n in self.sizes:
            q = min(1, self.cfg["batch_size"] / n)
            steps = self.cfg["rounds"] * self.cfg["local_epochs"] * max(1, round(n / self.cfg["batch_size"]))
            self.sigmas.append(dp.calibrate_sigma(q, steps, 4, self.cfg["dp"]["target_delta"]) if privacy else None)
        names = ["Hospital A", "Hospital B", "Hospital C", "Hospital D"]
        colors = ["var(--ganga)", "var(--yamuna)", "var(--verified)", "var(--clay)"]
        self.state = self.empty()
        self.state.update(runId=uuid.uuid4().hex, createdAt=now(), attack=attack, privacy=privacy,
                          coordinator=self.coord.address, registry=self.reg.address, aggregator=self.agg,
                          chain={"id": self.w3.eth.chain_id, "name": "Local Ethereum test chain", "symbol": "test ETH"},
                          split={"train": len(self.split.y_train), "validation": len(self.split.y_val), "test": len(self.split.y_test)})
        self.state["hospitals"] = [dict(id=i, name=names[i], city="Simulated participant", address=a, records=int(self.sizes[i]), color=colors[i]) for i, a in enumerate(self.addresses)]
        for a in self.addresses:
            self.send(self.coord.functions.registerParticipant(a), self.owner, "registerParticipant", 0, "Hospital registered")
        self.state["reputation"] = {str(i): 0.5 for i in range(4)}
        self.state["rewards"] = {str(i): 0 for i in range(4)}
        self.save()
        self.active = True

    def start(self, attack="none", privacy=True, new_run=False):
        with self.lock:
            if self.state["running"]:
                raise ValueError("A round is already running")
            if self.active and not new_run and len(self.state["rounds"]) >= self.cfg["rounds"]:
                raise ValueError("Training is complete. Start a new experiment.")
            self.state["running"] = True
            self.state["error"] = None
        worker = threading.Thread(target=self._worker, args=(attack, privacy, new_run), daemon=True)
        worker.start()

    def _worker(self, attack, privacy, new_run):
        try:
            if not self.active or new_run:
                with self.lock:
                    self.initialize(attack, privacy)
                    self.state["running"] = True
            self.round()
        except Exception as e:
            import logging
            logging.exception("Training round failed")
            with self.lock:
                # Never send exception text (which could contain credentials) to clients.
                self.state["error"] = "The round could not complete. Check the server log and start a new experiment."
                self.active = False
        finally:
            with self.lock:
                self.state["running"] = False
                if self.state["runId"]:
                    self.save()

    def append_tx(self, row, tx):
        with self.lock:
            row["txs"].append(tx)
            self.state["head"] = tx["block"]
            self.save()

    def round(self):
        cfg = self.cfg
        idx = len(self.state["rounds"]) + 1
        start_hash, start_cid = self.artifact(self.w)
        tx = self.send(self.coord.functions.openRound(start_hash, start_cid), self.agg, "openRound", idx, "Start model committed")
        row = dict(id=idx, status="open", startModelHash=start_hash, startCid=start_cid,
                   globalModelHash=None, globalCid=None, accuracy=None, auc=None, f1=None,
                   epsilonSpent=0, epsilonByHospital=[], openedAt=tx["ts"], closedAt=None,
                   updates=[], txs=[], phase="training", durationMs=None)
        with self.lock:
            self.state["rounds"].append(row)
        self.append_tx(row, tx)
        started = time.perf_counter()
        deltas = []
        for i, (X, y) in enumerate(self.split.hospitals):
            # The malicious participant deliberately opts out of DP. Its published
            # privacy budget must therefore be null, never the honest-client budget.
            attack = self.state["attack"]
            if i == 3 and attack != "none":
                d = malicious_update(attack, self.w, X, y, self.rng, cfg, self.prev_norm)
            else:
                d = local_update(self.w, X, y, self.rng, cfg, self.sigmas[i])
            deltas.append(d)
            update_hash = Web3.to_hex(Web3.keccak(model_bytes(d)))
            tx = self.send(self.coord.functions.submitUpdate(idx, update_hash), self.addresses[i], "submitUpdate", idx, f"Update from Hospital {chr(65+i)}")
            with self.lock:
                row["updates"].append(dict(hospitalId=i, updateHash=update_hash, txHash=tx["hash"], score=0, weight=0, flagged=False, excluded=False, reputationAfter=self.state["reputation"][str(i)]))
            self.append_tx(row, tx)
        with self.lock:
            row["phase"] = "scoring"
        scores = score_updates(self.w, deltas, self.split.X_val, self.split.y_val)
        # Use the contract's quantized integer scores/reputation as the authoritative
        # weights, so the displayed reputation and the aggregate agree exactly.
        scores_bps = np.clip(np.rint(scores * 10000), 0, 10000).astype(int).tolist()
        ordered = sorted(scores_bps)
        contract_threshold = ((ordered[1] + ordered[2]) // 2) // 2
        tx = self.send(self.reg.functions.recordScores(idx, self.addresses, scores_bps), self.agg, "recordScores", idx, "Four contribution scores recorded")
        self.append_tx(row, tx)
        rep = np.array([self.reg.functions.reputationOf(a).call() / 10000 for a in self.addresses])
        omega = aggregation_weights(rep, self.sizes)
        scaled = [o * b for o, b in zip(omega, bound_norms(deltas))]
        masked = secagg.mask_updates(scaled, idx, cfg["secagg"]["fixed_point_bits"])
        step = secagg.unmask_sum(masked, cfg["secagg"]["fixed_point_bits"])
        masking_error = float(np.max(np.abs(step - sum(scaled))))
        self.w = self.w + step
        self.prev_norm = float(np.linalg.norm(step))
        epsilons = []
        for i, n in enumerate(self.sizes):
            if self.sigmas[i] is None or (i == 3 and self.state["attack"] != "none"):
                epsilons.append(None)
            else:
                q = min(1, cfg["batch_size"] / n)
                steps = idx * cfg["local_epochs"] * max(1, round(n / cfg["batch_size"]))
                epsilons.append(dp.epsilon(q, self.sigmas[i], steps, cfg["dp"]["target_delta"]))
        with self.lock:
            row["phase"] = "aggregating"
            row["epsilonByHospital"] = epsilons
            row["epsilonSpent"] = max((e for e in epsilons if e is not None), default=0)
            row["maskingError"] = masking_error
            for i, u in enumerate(row["updates"]):
                u.update(score=scores_bps[i] / 10000, weight=float(omega[i]), flagged=bool(scores_bps[i] < contract_threshold), excluded=bool(omega[i] == 0), reputationAfter=float(rep[i]))
                self.state["reputation"][str(i)] = float(rep[i])
                self.state["rewards"][str(i)] = int(self.reg.functions.rewardOf(self.addresses[i]).call())
        h, cid = self.artifact(self.w)
        tx = self.send(self.coord.functions.commitGlobalModel(idx, h, cid), self.agg, "commitGlobalModel", idx, "Global model content ID committed")
        metrics = evaluate(self.w, self.split.X_test, self.split.y_test)
        with self.lock:
            row.update(status="aggregated", globalModelHash=h, globalCid=cid, accuracy=metrics["acc"], auc=metrics["auc"], f1=metrics["f1"])
        self.append_tx(row, tx)
        tx = self.send(self.coord.functions.closeRound(idx), self.agg, "closeRound", idx, "Round finalized")
        self.append_tx(row, tx)
        with self.lock:
            row.update(status="closed", phase="done", closedAt=tx["ts"], durationMs=round((time.perf_counter() - started) * 1000))
            self.save()

    def verify(self, value):
        q = value.lower()
        if not q.startswith("0x") or len(q) != 66:
            return {"found": False}
        for r in self.snapshot()["rounds"]:
            for tx in r["txs"]:
                if tx["hash"].lower() == q:
                    live = False
                    if self.active:
                        receipt = self.w3.eth.get_transaction_receipt(value)
                        live = receipt.status == 1 and Web3.to_hex(receipt.blockHash) == tx["blockHash"]
                    return dict(found=True, kind="transaction", round=r["id"], tx=tx, liveVerified=live, archived=not self.active)
            for u in r["updates"]:
                if u["updateHash"].lower() == q:
                    live = self.active and Web3.to_hex(self.coord.functions.updateOf(r["id"], self.addresses[u["hospitalId"]]).call()).lower() == q
                    return dict(found=True, kind="update", round=r["id"], liveVerified=bool(live), archived=not self.active)
            for h, cid in ((r["startModelHash"], r["startCid"]), (r["globalModelHash"], r["globalCid"])):
                if h and h.lower() == q:
                    data = self.store.model(cid)
                    matches = data is not None and Web3.to_hex(Web3.keccak(data)).lower() == q
                    chain_match = False
                    if self.active:
                        entry = self.coord.functions.getRound(r["id"]).call()
                        chain_match = q in (Web3.to_hex(entry[1]).lower(), Web3.to_hex(entry[3]).lower())
                    return dict(found=True, kind="model", round=r["id"], cid=cid, artifactVerified=matches, liveVerified=chain_match, archived=not self.active)
        return {"found": False}
