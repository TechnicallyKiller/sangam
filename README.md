# Sangam

A college research prototype for **blockchain-coordinated federated learning in healthcare**.
Four simulated hospitals train a shared model. Contribution scores determine their influence;
Solidity contracts record update hashes, model content IDs, reputation, and reward points.

**Live dashboard:** https://sangam-eight-drab.vercel.app
**API / interactive documentation:** https://sangam-api-t4z4.onrender.com/docs

Team: Divyanshh Kalra · Shrey Khandal · Tanish Garg
Guide: Dr. Mohit Mittal · MAIT, CSE-AIML

## What works

- Real NumPy training on Breast Cancer Wisconsin: 569 cases, 30 features, four non-IID partitions.
- DP-SGD with integer-order RDP accounting; contribution scoring and asymmetric reputation.
- Real execution of the two Solidity contracts on a clearly labelled local Ethereum test chain.
- An authenticated training API, persistent run history, model downloads, and hash verification.
- A dashboard showing measured values and actual transaction receipts.
- Saved evidence remains readable after a service restart or while the free API wakes up.

This is a one-process research simulation, not a clinical product. Validators see individual
updates, the pairwise-mask routine is an arithmetic simulation, and normalization uses pooled
training statistics. The hosted demo is **not Polygon Amoy**. Models are content-addressed
and stored off chain; public IPFS pinning is not claimed. See [decisions](docs/DECISIONS.md).

## Final submission

Start with [the handoff guide](submission/START_HERE.md).

- [Final paper: PDF](submission/Sangam_Final_Paper.pdf), [editable Word](submission/Sangam_Final_Paper.docx), [Markdown](submission/Sangam_Final_Paper.md)
- [Final presentation: PowerPoint](submission/Sangam_Final_Defence.pptx), [PDF](submission/Sangam_Final_Defence.pdf)
- [Speaker notes](submission/SPEAKER_NOTES.md), [demo script and viva answers](submission/DEMO_AND_VIVA.md)
- [Reproduced evaluation](submission/evaluation.json), [per-seed evidence](submission/evaluation.seeds.json)
- [Publication route](submission/PUBLICATION.md)

## Run locally

On this already-prepared laptop, `bash tools/demo.sh` starts both parts with local SQLite
and no cloud connection. The commands below describe the separate setup steps.

Python 3.12 and Node 22 are a supported setup. Keep private values in `.env` (see `.env.example`).
The database is optional locally: leave `DATABASE_URL` empty to use SQLite.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r backend/requirements.txt
# Set SANGAM_ADMIN_TOKEN in .env to a long random private value.
bash tools/start_local.sh
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

If a local `frontend/.env.local` points to the hosted API, change `VITE_API_URL` to
`http://127.0.0.1:8000` for the fully local demo. Open http://localhost:5173, select
**Operator access**, and enter the token saved in `.env`. Start an experiment, then open
successive rounds. A new experiment retains previous run records.

The runtime contract artifacts are tracked in `backend/compiled/`. To rebuild them:

```bash
cd contracts
npm ci
npx hardhat compile
cd ..
.venv/bin/python tools/prepare_artifacts.py
```

## Reproduce and verify

```bash
uv pip install --python .venv/bin/python pytest
.venv/bin/python -m pytest fl/tests backend/tests -q
cd contracts && npm ci && npx hardhat test
cd ../frontend && npm ci && npm run build
```

For the research experiments:

```bash
cd fl
OPENBLAS_NUM_THREADS=1 ../.venv/bin/python simulate.py --out ../submission/evaluation.json
```

For a measured contract-integrated run:

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python tools/run_demo.py --rounds 30
# Optional separate poisoning demonstration:
OPENBLAS_NUM_THREADS=1 .venv/bin/python tools/run_demo.py --rounds 12 --attack sign_flip
```

The experiment table and interactive run are distinct evidence sources. Do not replace
live metrics with paper averages or claim the non-private attack study proves joint DP robustness.

## Hosting

The free Render service builds `Dockerfile`; one worker owns the local EVM. Supabase persists
runs and model bytes. Vercel builds `frontend/`, with `VITE_API_URL` pointing to the Render API.
Set the frontend's exact origin in the API's `CORS_ORIGINS`. Free hosting may sleep or pause;
keep the local demo available. No mainnet currency, paid API, custom domain, or GPU is required.

The original Amoy deployment script remains in `contracts/scripts/deploy.ts` for future use
with `AMOY_RPC_URL` and a funded **testnet-only** `DEPLOYER_PRIVATE_KEY`. It is separate from
the deployed local-EVM prototype.
