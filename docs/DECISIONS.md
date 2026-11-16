# Sangam decision log

Plain-language record for the final college submission. Started 16 November 2026,
after the requested 12:49 IST reset. Budget: ₹0.

| Decision | What and why |
|---|---|
| Keep the core | Keep the four-hospital Breast Cancer Wisconsin experiment, DP-SGD, contribution scoring, asymmetric reputation, masking, and the two Solidity contracts. Finish their integration rather than adding a new research problem. |
| Honest evidence | Replace generated dashboard numbers with measured training results and actual contract receipts. Label local-chain evidence as local; never present it as Polygon Amoy. |
| Practical scope | Flower, medical images, zero-knowledge proofs, and a production hospital deployment remain future work. They are not necessary for a working college demonstration. |
| Privacy boundary | Validators see individual DP-protected updates. The original mask routine is a reproducible arithmetic simulation, not a production secure-aggregation protocol. Describe that limit in the paper and slides. |
| Scientific consistency | Regenerate results with saved per-seed evidence. Correct the old paper's split counts, accountant description, and result values to match the implementation. |
| Clear slides | Use editable diagrams, short captions, and speaker notes. Retain all topics required by the college notice. |
| Free hosting | Use existing free Vercel/Render accounts and Supabase persistence. Training can also run locally for an internet-independent demonstration. |
| Publication | Prepare a real manuscript and venue-specific submission materials. Do not claim publication, acceptance, indexing, or guaranteed review times. |

Further implementation decisions and verification outcomes are appended below.

## Integration choices

- **Actual local EVM by default:** no funded testnet key was provided. Use an in-process Ethereum test chain to execute the real compiled contracts. This removes an extra server and costs nothing. Mark it clearly as a local EVM; keep Amoy deployment scripts for a funded testnet wallet. This changes deployment plumbing, not the learning or contract rules.
- **Operator authorization:** replace the pretend wallet/signing flow with a real private operator token for the demonstration. The service submits transactions for four simulated hospitals. Do not pretend that pressing a button signed a MetaMask transaction.
- **Durable artifacts:** store model bytes and their real content IDs off chain. Supabase can persist the tiny artifacts and run records for free. IPFS publication is optional, and no unpinned artifact is described as publicly pinned.
- **Faster accountant, same equations:** vectorize the existing integer-order RDP calculation and cache noise calibration. This cuts repeated Python/SciPy overhead; a scalar-reference test verifies numerical agreement. The privacy method is unchanged.
- **Stable scoring arithmetic:** use the standard sigmoid implementation for the same score equation, avoiding overflow warnings for extremely bad updates.
- **Dataset correction:** the implemented 7% validation split has 415 training, 40 validation, and 114 test records. The previous paper's 398/57/114 figures described a different split; the final manuscript uses the code's actual counts.
- **Separate evidence:** multi-seed research results remain separate from a single interactive demonstration. The dashboard never fabricates comparison curves or substitutes paper averages for live measurements.

## Verification and deployment

- Python tests cover gradient correctness, mask cancellation, privacy-accountant agreement, reputation, API authorization, actual contract execution, and model integrity. Eight tests pass.
- All eight existing Hardhat contract tests pass. The production frontend builds successfully.
- The free Render API uses PostgreSQL persistence and executes real local-EVM rounds. Live API authorization and model/hash verification were checked.
- The Vercel frontend uses the hosted API. Its Git build root is `frontend/`, and the API URL is a saved build environment setting.
- Browser checks cover all four pages, hash verification, and a mobile viewport. An obsolete mock-wallet initializer was removed after the first browser check exposed it. The mobile layout was adjusted after an overflow check.
- Journal preparation uses Informatica's stated free Normal track as the practical no-fee option. Its stated first-decision target is 6–12 months, so it cannot be represented as a completed publication for the immediate defence.
- The paper, slides, and evidence use reproduced measurements. The old draft's dataset counts and unverified gas figures are superseded.
- **Repository handoff:** retain the original Git history, review the completed work through a pull request, and merge the verified submission into the default branch so a new clone opens the finished project.
