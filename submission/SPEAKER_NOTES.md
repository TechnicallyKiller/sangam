# Speaker notes

## 1. Sangam

We built a research prototype in which four simulated hospitals train a diagnostic model together. Their records remain in their simulation partitions. Smart contracts record updates, model versions, and contribution scores. We demonstrate measured training and actual local-Ethereum execution, not a deployment in real hospitals.

## 2. The team

Divyanshh Kalra, Shrey Khandal, and Tanish Garg are the student authors. Dr. Mohit Mittal is the project guide. Roll numbers and institution are carried forward from the confirmed second-defence deck. The team should agree on who explains the methodology, implementation, and evaluation before the final defence.

## 3. The problem: learning across data silos

A single hospital may have limited and unbalanced data. Pooling patient records creates privacy and institutional concerns. Ordinary federated learning shares model updates, but a trusted server still controls aggregation. Our objective is to combine useful learning, a recorded contribution history, and explicit privacy/robustness mechanisms in a reproducible prototype.

## 4. What existing approaches leave open

FedAvg establishes learning through model averaging. Secure aggregation protects individual updates but does not by itself detect poisoning. Robust methods such as the median and FLTrust address malicious updates. Blockchain FL papers add coordination or incentives. Sangam studies these roles together in a small, explicit prototype; we do not claim that no previous framework combines them, or that our method is universally best.

## 5. The system, at a glance

Hospitals train locally with DP-SGD in separate simulation partitions. Validators receive the individual updates and compute scores. Reputation determines weights; pairwise masks cancel in the aggregate. Solidity stores hashes, content IDs, and scores. Off-chain storage holds the actual model bytes. In the prototype these roles execute in one Python service, and the contracts execute on a real local EVM. Validators see more than the aggregation role.

## 6. One round in six steps

The aggregator first opens a round with the starting model commitment. Each hospital trains locally. Hospitals commit update hashes. Validators score the updates, and the contract updates reputations. Reputation-weighted updates are masked and summed. Finally the new model is stored off chain and its hash and content ID are committed before the round closes. Each step produces an actual transaction receipt in the integrated demonstration.

## 7. Privacy has two separate jobs

DP-SGD clips per-example gradients and adds Gaussian noise; the accountant measures composition across training. Pairwise masking demonstrates that individual scaled updates can sum without retaining masks in the final aggregate. Validators still inspect individual DP updates to score them. The mask routine is an arithmetic simulation with reproducible seeds, not a production key-exchange and dropout-tolerant protocol. Reproducible experimental seeds must not be treated as secret production randomness.

## 8. Bad contributions lose influence

An update is scored by agreement with the median direction and by validation-loss improvement. A score below half the round median halves reputation. Other reputations move 20 percent toward the new score. Clients below one quarter of the maximum reputation are excluded; the rest are weighted by dataset size times reputation. Rewards are contribution points, not cash or tokens. In the integrated run we use the contract integer values to determine weights.

## 9. What we built

The diagnostic model is a 30–16–1 NumPy MLP with 513 parameters. Python implements the learning, scoring, DP accountant, and masking arithmetic. FastAPI joins training to the compiled Solidity contracts on a local EVM. React displays actual measurements and receipts. Supabase persists experiments and model bytes. The public deployment is a college prototype; it is not a hospital system or medical advice.

## 10. A small, reproducible benchmark

Breast Cancer Wisconsin has 569 cases and 30 numeric features. The actual implementation uses 415 training, 40 validation, and 114 test records, with a stratified test split and a Dirichlet alpha 0.5 partition across four simulated hospitals. We run 30 rounds, two local epochs, batch size 16, learning rate 0.1, and ten seeds. The old draft had inconsistent split counts; these are corrected. Preprocessing is centralized in the simulation and would need a privacy-aware protocol in a real deployment.

## 11. Useful learning, with a privacy cost

Sangam without DP reaches 97.72 percent mean accuracy; FedAvg reaches 97.63 percent and the coordinate median 97.89 percent. We do not claim Sangam is the most accurate honest-case baseline. With epsilon 4 the mean accuracy is 96.84 percent. The benefit being studied is the combination of useful learning, contribution history, and robustness. These are reproduced figures from this repository, not the old paper numbers.

## 12. One attacker: FedAvg vs Sangam

Hospital D attacks while the other hospitals follow ordinary non-private training. For sign flipping, FedAvg averages 35.61 percent accuracy while Sangam averages 97.19 percent. Label flipping reduces FedAvg to 87.11 percent, while Sangam stays at 97.19 percent. The median baseline is also robust. We evaluate these attacks separately from the privacy sweep; these results do not demonstrate a joint DP-plus-attack guarantee.

## 13. Poisoning earns less say in the model

The honest Hospital D has an average 23.44 percent influence under Sangam. That falls to 2.06 percent with label flipping and 2.95 percent with sign flipping. The free rider still keeps about 12.09 percent, so free-rider detection is incomplete. On-chain score history makes this weighting auditable; reputation does not prove an update is honest.

## 14. Privacy is a measurable trade-off

With delta 10 to the minus five, epsilon 1 gives 93.42 percent mean accuracy; epsilon 2 gives 95.79; epsilon 4 gives 96.84; and epsilon 8 gives 97.28. Error bars are standard deviations across ten seeds, not confidence intervals. Privacy is computed per hospital using the implemented integer-order RDP accountant, with Poisson sampling and per-example clipping. It is an experimental accounting calculation, not a certification of the deployed service.

## 15. The demo leaves evidence you can inspect

Show one round in the dashboard. Open the round drawer, inspect the four update hashes, contribution scores, and eight transaction receipts. Download the global-model bytes. Paste its hash into Audit: the API checks the artifact bytes and the active contract state. Archived runs are explicitly labelled after a restart. The test suite checks unauthorized access, the complete contract lifecycle, reputation, numerical gradients, accounting equivalence, and artifact integrity.

## 16. What this prototype does — and what comes next

The contribution is a reproducible integration of reputation-weighted learning, privacy accounting, and a real contract audit trail, evaluated on one small public dataset. Limitations include four simulated hospitals, centralized simulation preprocessing, validator visibility, incomplete free-rider detection, and no binding proof between a masked input and its commitment. Next steps are independent hospital processes, secret pairwise key agreement, funded Amoy deployment, medical images, and stronger adaptive-attack evaluation. Publication is a separate review process and is not claimed as completed.

## 17. References

The manuscript contains the full references. The presentation cites the original FedAvg, secure aggregation, DP-SGD, RDP accounting, robust aggregation, and FLTrust work. We distinguish features described in those papers from the simplified implementation in Sangam.
