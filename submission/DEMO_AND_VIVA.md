# A five-minute demonstration

1. Open the dashboard and explain the banner: actual training on a labelled local Ethereum test chain.
2. Open **Operator access** and use the private token saved in `.env`.
3. Choose an honest run or a sign-flipping Hospital D. Keep DP on for the privacy demonstration.
4. Click **Start experiment** or **New experiment**, wait for round 1, then **Open next round**.
5. Open a round card. Point to the four hospital updates, their scores and weights, and eight receipts.
6. Go to **Participants**. Show a poor contributor's reputation falling; rewards are points, not money.
7. Go to **Audit**. Use the example hash, then verify a global-model hash from a round.
8. Download a model from the round drawer. Explain that bytes are off chain; its hash is on chain.

A saved run is labelled as saved. Live verification checks the active chain; after a restart,
archived receipts remain inspectable and model bytes can still be integrity-checked.

# Simple answers

**What does Sangam do?** Four simulated hospitals train one shared model. Contribution scores
control influence, and smart contracts record the process.

**What is federated learning?** Move model updates between participants instead of pooling their records.
In this prototype the hospitals are separate data partitions inside a single simulation process.

**Why blockchain?** To enforce the round lifecycle and keep a contribution/model history that can be
inspected. It does not prove the training or scoring was correct.

**What is the model?** A small 30–16–1 neural network with 513 parameters, trained on 30 diagnostic features.

**What are the data splits?** 415 training cases, 40 validation cases, and 114 test cases. Ten seeds
vary the splits and hospital partitions. Validation helps score contributions; test data measure results.

**How do you detect bad updates?** Score agreement with the median direction and improvement on a
validation set. Poor scores reduce reputation and therefore reduce aggregation weight.

**How is reputation updated?** A score below half the round median halves reputation. Otherwise
reputation moves 20% toward the new score. Very low-reputation hospitals get zero weight.

**What does DP do?** Clip each example's gradient and add noise. The accountant estimates the
privacy budget over training. Smaller epsilon is more private and usually less accurate.

**What does masking do?** Add equal-and-opposite pairwise masks so the combined sum is unchanged.
Our code demonstrates this arithmetic; production key agreement and dropout recovery are future work.

**Can anyone see an update?** The validator sees individual updates so it can score them. In private
experiments they have DP noise. We do not claim that no party sees them.

**What are the headline results?** Across ten seeds: Sangam without DP 97.72% mean accuracy,
FedAvg 97.63%, and Sangam at epsilon 4 about 96.84%. Under non-private sign flipping, FedAvg
35.61% versus Sangam 97.19%. The median baseline is also robust.

**Are attacks and DP tested together?** The research attack comparison is non-private. The privacy
sweep is separate. The interactive demo can combine them, but is not a multi-seed joint evaluation.

**Is free-rider detection perfect?** No. The free rider retains about 12.09% influence, versus 23.44%
in the honest control. We describe it as partial suppression.

**Is the testnet live?** The hosted demo executes on an actual local EVM, not Polygon Amoy. Amoy
configuration is retained, but no public-testnet deployment is claimed without a funded testnet wallet.

**Is this production-ready or clinically validated?** No. It is a reproducible college prototype
on a small public benchmark. Real hospital isolation and larger clinical evaluation are future work.

**What is the contribution?** A working integration, reproducible comparisons, persistent contribution
history, and verifiable model provenance, with the privacy and trust assumptions stated clearly.

**What if the internet fails?** Use the local API/dashboard and the saved evidence, PPT PDF, and paper PDF.
