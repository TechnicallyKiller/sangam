# Results

Source: `Sangam_Research_Paper.pdf` (Second Defence draft) and `Sangam_Second_Defence.pptx`.
Setup: Breast Cancer Wisconsin (Diagnostic), 569 cases, 4 hospitals, Dirichlet(α = 0.5),
30–16–1 MLP (513 parameters), T = 30 rounds, E = 2, 10 seeds, mean ± SD. 190 runs (19 configs × 10 seeds).

## Utility (no attack)

| Method | Accuracy (%) | ROC-AUC (%) | F1 (%) |
|---|---|---|---|
| Centralised (pooled) | 97.98 ± 1.11 | 99.75 ± 0.23 | 98.40 ± 0.88 |
| Local only (mean of 4) | 95.86 ± 1.00 | 99.40 ± 0.38 | 96.70 ± 0.81 |
| FedAvg (trusted server) | 97.72 ± 1.12 | 99.75 ± 0.24 | 98.19 ± 0.90 |
| Coordinate-wise median | 97.46 ± 1.14 | 99.71 ± 0.28 | 97.99 ± 0.90 |
| Sangam (no DP) | 97.63 ± 0.88 | 99.69 ± 0.31 | 98.13 ± 0.70 |
| Sangam, DP ε = 4 | 96.67 ± 1.46 | 99.45 ± 0.32 | 97.37 ± 1.15 |

## Privacy–utility (δ = 1e-5)

Mean noise multiplier σ = 13.1 / 7.0 / 3.9 / 2.2 for ε = 1 / 2 / 4 / 8.
Accuracy: ε = 8 → 97.63, ε = 4 → 96.67, ε = 1 → 93.77 (SD 3.0).

## Robustness (hospital 4 malicious, holds 28.8% of data)

| Attack | FedAvg acc. | Median acc. | Sangam acc. | Sangam weight of H4 |
|---|---|---|---|---|
| Label flip | 74.12 ± 28.07 | 97.11 | 96.93 | 2.4% |
| Sign flip (−5×) | 45.96 ± 36.14 | 96.75 | 97.02 | 1.9% |
| Free rider | little damage | – | – | 9.8% |
| Honest (control) | – | – | – | 29.1% |

## Secure aggregation

Masked vs plain sum error 1.6e-6; correlation of masked with raw update 0.04;
0.51 ms per round vs 0.007 ms plain.

## Gas (Hardhat, optimiser 200 runs)

| Operation | Gas |
|---|---|
| Deploy SangamCoordinator | 818,749 |
| Deploy ReputationRegistry | 396,462 |
| registerParticipant | 47,526 |
| openRound | 83,117 |
| submitUpdate (per hospital) | 58,246 |
| recordScores (4 hospitals) | 197,384 |
| commitGlobalModel | 122,571 |
| closeRound | 32,393 |
| **Round total (K = 4)** | **668,449** |

The contracts in `contracts/` were rebuilt from the paper's design; re-measure gas with
`REPORT_GAS=true npx hardhat test` before quoting these numbers as reproduced.

---

## Reproduction (`fl/`, this repo)

`cd fl && python simulate.py` (10 seeds, `config.yaml`; raw output in `fl/results.json`).
Re-implemented from the paper's description, so numbers differ slightly from the paper's own runs.

| Experiment | Paper | This repo |
|---|---|---|
| Centralised acc. | 97.98 | 97.54 |
| Local only acc. | 95.86 | 96.21 |
| FedAvg acc. | 97.72 | 97.63 |
| Sangam (no DP) acc. | 97.63 | 97.72 |
| Sangam ε = 1 / 4 / 8 acc. | 93.77 / 96.67 / 97.63 | 93.42 / 96.84 / 97.28 |
| Sign flip: FedAvg → Sangam | 45.96 → 97.02 | 35.61 → 97.19 |
| Label flip: FedAvg → Sangam | 74.12 → 96.93 | 87.11 → 97.19 |
| Attacker weight, label / sign / free rider | 2.4 / 1.9 / 9.8 % | 2.1 / 3.0 / 12.1 % |
| Attacker weight when honest | 29.1 % | 23.4 % |

Qualitative claims reproduce: FedAvg breaks under one attacker, Sangam does not, privacy
costs little above ε = 4, and the free rider keeps about a third of its fair share. The honest-case
weight (23.4 vs 29.1) and label-flip FedAvg damage (87 vs 74) differ and are worth a look
before quoting either set.
