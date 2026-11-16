"""Sangam API. Read-only endpoints are public; training requires operator access."""
import hmac
import os
import re
from pathlib import Path

from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from .engine import Engine, content_id
from .store import Store

app = FastAPI(title="Sangam", version="1.0", description="Measured federated learning and Solidity execution for a college prototype.")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")], allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
store = Store()
engine = Engine(store)


def authorize(header):
    expected = os.getenv("SANGAM_ADMIN_TOKEN", "")
    supplied = header.removeprefix("Bearer ") if header else ""
    if not expected or not hmac.compare_digest(supplied, expected):
        raise HTTPException(401, "Operator token required")


@app.get("/health")
def health():
    return {"ok": True, "mode": "local-evm", "persistence": "postgres" if store.url else "sqlite"}


@app.get("/state")
def state():
    return engine.snapshot()


@app.get("/rounds")
def rounds():
    return engine.snapshot()["rounds"]


@app.get("/rounds/{round_id}")
def get_round(round_id: int):
    for row in engine.snapshot()["rounds"]:
        if row["id"] == round_id:
            return row
    raise HTTPException(404, "Round not found")


@app.get("/participants")
def participants():
    s = engine.snapshot()
    return [dict(h, reputation=s["reputation"][str(h["id"])], rewards=s["rewards"][str(h["id"])]) for h in s["hospitals"]]


@app.get("/audit")
def audit():
    return [tx for r in engine.snapshot()["rounds"] for tx in r["txs"]]


@app.get("/audit/verify/{value}")
def verify(value: str):
    return engine.verify(value)


@app.get("/models/{cid}")
def model(cid: str):
    if not re.fullmatch(r"b[a-z2-7]{58}", cid):
        raise HTTPException(400, "Expected a raw SHA-256 CIDv1")
    data = store.model(cid)
    if data is None:
        raise HTTPException(404, "Model not found")
    if content_id(data) != cid:
        raise HTTPException(500, "Model integrity check failed")
    return Response(data, media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{cid}.f64"', "X-Model-Format": "513 little-endian float64 parameters"})


@app.get("/runs")
def runs():
    return [{"id": s["runId"], "createdAt": s["createdAt"], "rounds": len(s["rounds"]), "attack": s["attack"], "privacy": s["privacy"]} for s in store.runs()]


@app.get("/runs/{run_id}")
def run(run_id: str):
    for s in store.runs():
        if s["runId"] == run_id:
            s.update(running=False, archived=True)
            return s
    raise HTTPException(404, "Run not found")


@app.post("/auth/check")
def auth_check(authorization: str | None = Header(default=None)):
    authorize(authorization)
    return {"ok": True}


class RunOptions(BaseModel):
    attack: str = "none"
    privacy: bool = True
    newRun: bool = False


@app.post("/rounds/open", status_code=202)
def open_round(options: RunOptions, authorization: str | None = Header(default=None)):
    authorize(authorization)
    if options.attack not in ("none", "label_flip", "sign_flip", "free_rider"):
        raise HTTPException(400, "Unknown attack")
    try:
        engine.start(options.attack, options.privacy, options.newRun)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"accepted": True}
