# Sangam, simply explained

The product's core is unchanged: hospitals learn together, useful contributions get more
influence, and contracts keep the contribution history.

- `fl/` is the brain: trains the model, adds experimental DP noise, scores updates, and combines them.
- `contracts/` is the rulebook: two real Solidity contracts enforce rounds and store reputation.
- `backend/` is the bridge: runs the learning and contracts together and serves real measurements.
- `frontend/` is the face: shows those measurements, rather than inventing dashboard numbers.
- `submission/` is the college hand-in package: final paper, slides, notes, evidence, and demo guide.
- `tools/` contains the commands that rebuild the contract artifacts, evidence, and documents.

The service uses a local Ethereum test chain, with four simulated hospitals. No real patient
records, real cryptocurrency, or real clinical deployment are involved. Models are kept off
chain; their hashes and content IDs go into the contracts. A saved run stays available after
restart, but live chain verification applies only to the active chain.

To present: open the dashboard, explain the diagram, run one round, inspect the four updates,
and verify the global model hash. The speaker notes explain each slide in plain language.

What remains research rather than production: secret pairwise key exchange, independent
hospital processes, dropout recovery, proof of correct aggregation, and a large clinical evaluation.
