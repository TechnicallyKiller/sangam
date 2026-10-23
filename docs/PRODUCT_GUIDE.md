# Sangam product guide: what lives where

## What is this project?

Hospitals want to build one smart model that can spot diseases, but they can't share
patient records. Sangam lets them train **together without sharing the data**, and uses a
**blockchain as a public notebook** so nobody has to blindly trust a middleman.

It has four parts. Think of them as four rooms in one house:

| Part | Folder | In one line | Status |
|---|---|---|---|
| The rulebook | `contracts/` | Programs on the blockchain that run the rounds and remember trust scores | Built, 8 tests pass |
| The brain | `fl/` | The training code: models, privacy, spotting bad updates | Built, runs the experiments |
| The face | `frontend/` | The website that shows everything | Built, runs on demo data |
| The bridge | `backend/` | Would connect the website to the real blockchain | **Empty, not built yet** |

## The folders, one by one

### `contracts/` — the rulebook

Smart contracts are small programs that live on a blockchain. Once saved, nobody can quietly change the rules.

| File | What it does |
|---|---|
| `contracts/SangamCoordinator.sol` | Runs each training round. Opens it, accepts each hospital's fingerprint, saves the new model's fingerprint, closes it. Only approved hospitals can join. A hospital can't submit twice or too late |
| `contracts/ReputationRegistry.sol` | Keeps every hospital's trust score and reward points. A bad round halves the trust. Good rounds slowly raise it |
| `test/Sangam.test.ts` | 8 automatic checks that the rules above really work |
| `scripts/deploy.ts` | Puts the two contracts onto a blockchain and saves their addresses for the other parts |
| `hardhat.config.ts` | Settings for the tool (Hardhat) that builds and tests the contracts, including the Polygon Amoy test network |
| `package.json` | List of tools this folder needs |

Run the checks: `cd contracts && npm install && npx hardhat test`

### `fl/` — the brain (federated learning)

"FL" means federated learning: learning together while the data stays at home. This folder is a
**simulation**. It pretends four hospitals exist and trains a small model on the Breast Cancer
Wisconsin dataset.

| File | What it does |
|---|---|
| `data.py` | Loads the patient data, hides some for testing, and splits the rest unevenly across 4 hospitals (like the real world) |
| `model.py` | The small neural network (513 numbers to learn) |
| `fed.py` | The training loop. Runs normal training, the comparison methods, and the three attacks (flipped labels, flipped signs, free-riding) |
| `strategy.py` | Grades each hospital's lesson, updates trust, and decides how much say each hospital gets |
| `privacy/dp.py` | Adds careful noise so no single patient can be traced, and tracks how much privacy is used (ε) |
| `privacy/secagg.py` | Scrambles each hospital's lesson so only the combined total can be read |
| `simulate.py` | Runs all the experiments over 10 random seeds and prints the table |
| `config.yaml` | The knobs: number of hospitals, rounds, learning speed, privacy settings |
| `results.json` | The saved numbers from the last full run |
| `tests/test_fl.py` | 5 checks that the maths is right (scrambling cancels out, trust rule works, etc.) |
| `requirements.txt` | Python packages needed |

Run it: `cd fl && pip install -r requirements.txt && python simulate.py`
(about 4 minutes for all 10 seeds)

### `frontend/` — the face (the website)

A React website built with Vite. Right now **every number on it is demo data**. Nothing real
sits behind it yet, but it behaves like the finished product would.

| Where | What it does |
|---|---|
| `src/pages/` | The four screens: Overview, Rounds, Participants, Audit |
| `src/components/` | Reusable pieces: the river picture (`Confluence`), the accuracy chart, round cards, the wallet popup, the confirm box, the notifications, the copy-able hash tags |
| `src/services/ledger.ts` | **Where all the data comes from.** It holds the demo history and plays out a live round. This is one of the two files to replace with the real connection |
| `src/services/wallet.ts` | **The wallet connection.** Currently pretends. The second file to replace with a real wallet |
| `src/lib/` | Small helpers: shortening hashes, remembering the connected wallet, showing notifications |
| `src/styles/` | Colours, fonts, and layout. Named after the three rivers: ochre, indigo, violet |
| `vercel.json` | Lets the site work properly when hosted on Vercel |
| `package.json` | List of tools this folder needs |

Run it: `cd frontend && npm install && npm run dev`, then open http://localhost:5173

### `backend/` — the bridge (not built yet)

Currently empty. The plan from the README is a small server that would:
- talk to the real blockchain,
- store model files on IPFS (a place for big files),
- and feed real data to the website.

Until then, the website uses its own demo data.

### `docs/` — notes

| File | What it is |
|---|---|
| `results.md` | The experiment results: the paper's numbers next to the numbers this code reproduced |
| `FRONTEND_GUIDE.md` | A plain-words tour of the website |
| `PRODUCT_GUIDE.md` | This file |

### Top-level files

| File | What it is |
|---|---|
| `README.md` | The main project description, architecture and design rules |
| `Sangam_Research_Paper.pdf` | The research paper draft |
| `Sangam_Second_Defence.pptx` | The slides for the second defence |
| `.gitignore` | Files git should never save (secrets, downloaded packages, build output) |

## How the parts fit together

```
Hospitals (fl/) ──train──► lessons ──fingerprint──► Blockchain (contracts/)
                               │                          ▲
                               ▼                          │ reads
                         combined model           Website (frontend/)
                         (stored on IPFS)                 ▲
                                                          │ would connect through
                                                     Server (backend/, not built)
```

1. Hospitals train in `fl/`.
2. Fingerprints of each lesson go to the contracts in `contracts/`.
3. The website in `frontend/` shows what happened.
4. `backend/` is the missing link that would make step 3 show real data.

## What is real and what is demo

| Piece | Real or demo? |
|---|---|
| Smart contracts and their tests | **Real.** They compile and pass their tests on a local test blockchain |
| Training, privacy, attack and trust results | **Real.** Produced by running `fl/` yourself |
| The paper's own numbers | Real, but from the authors' earlier runs. They are close to, not identical with, `fl/` |
| Website data, wallet, fees, round progress | **Demo.** Simulated so the full flow can be shown |
| Deployment to a public test network (Polygon Amoy) | **Not done yet** |
| Backend server | **Not built yet** |

## What's next

1. Deploy the contracts to the Polygon Amoy test network.
2. Build `backend/` so the website reads real events.
3. Replace `ledger.ts` and `wallet.ts` with the real connections.
4. Move training to Flower and Opacus with medical images (MedMNIST).
5. Finish the evaluation and the paper.
