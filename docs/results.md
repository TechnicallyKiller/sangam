# Reproduced results

Final run: 16 November 2026. Ten seeds (0–9); mean ± population SD. Actual split: 415 training / 40 validation / 114 test.

| Method | Accuracy % | AUC % | F1 % |
|---|---|---|---|
| centralised | 97.54 ± 1.23 | 99.77 ± 0.22 | 98.05 ± 0.97 |
| local_only | 96.21 ± 1.21 | 99.46 ± 0.33 | 96.97 ± 1.01 |
| fedavg | 97.63 ± 1.11 | 99.76 ± 0.21 | 98.13 ± 0.88 |
| median | 97.89 ± 0.89 | 99.71 ± 0.25 | 98.34 ± 0.71 |
| sangam | 97.72 ± 0.80 | 99.72 ± 0.19 | 98.20 ± 0.63 |
| sangam_eps1 | 93.42 ± 3.22 | 97.95 ± 1.77 | 94.74 ± 2.71 |
| sangam_eps2 | 95.79 ± 2.47 | 99.16 ± 0.52 | 96.65 ± 1.97 |
| sangam_eps4 | 96.84 ± 1.12 | 99.57 ± 0.27 | 97.48 ± 0.90 |
| sangam_eps8 | 97.28 ± 1.38 | 99.61 ± 0.33 | 97.85 ± 1.09 |
| label_flip/fedavg | 87.11 ± 11.08 | 91.77 ± 16.77 | 89.72 ± 8.03 |
| label_flip/sangam | 97.19 ± 1.23 | 99.70 ± 0.20 | 97.78 ± 0.96 |
| sign_flip/fedavg | 35.61 ± 28.92 | 17.16 ± 27.60 | 27.26 ± 37.13 |
| sign_flip/sangam | 97.19 ± 1.10 | 99.63 ± 0.21 | 97.79 ± 0.85 |

Research results are separate from the contract-integrated single-seed demonstration.
The attack comparison is non-private; it is not a joint privacy-and-attack evaluation.

Integrated honest run: 30 rounds, 240 transactions, mean gas 842,351/round.
The old paper gas and accuracy values are superseded, not silently reused.

Raw evidence: `submission/evaluation.json`, `submission/evaluation.seeds.json`, and `submission/integrated-none.json`.
