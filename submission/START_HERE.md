# Your submission is here

## Open these first

1. `Sangam_Final_Defence.pptx` — 17 slides, editable diagrams, short labels, speaker notes.
2. `Sangam_Final_Defence.pdf` — presentation backup for a different laptop.
3. `Sangam_Final_Paper.pdf` — rebuilt research paper with measured results.
4. `Sangam_Final_Paper.docx` — editable paper source; Markdown source is also included.
5. `DEMO_AND_VIVA.md` — a short demo script and easy answers to likely questions.
6. `PUBLICATION.md` — a free journal route and the remaining external-submission steps.

Dashboard: https://sangam-eight-drab.vercel.app
API: https://sangam-api-t4z4.onrender.com/docs

For operator access, use `SANGAM_ADMIN_TOKEN` in the private root `.env` file. It is not included
in the public submission files. Anybody can view results; only the operator can start training.

## What changed and why

- Built the missing backend: the project now connects learning, contracts, storage, and the website.
- Removed fake wallet signing and generated dashboard numbers: the demo now shows what actually ran.
- Kept the learning and contract rules: no new medical dataset or extra research framework was added.
- Used a real local test chain: there was no funded testnet wallet; this avoids spending money.
- Re-ran all ten seeds: the paper uses the reproduced numbers rather than the old draft's claims.
- Corrected the dataset split: 415 training / 40 validation / 114 test.
- Made slides more visual: architecture and methodology diagrams carry the explanation; notes carry detail.
- Kept limitations clear: this is a college research prototype, not a hospital deployment.

The detailed decision history is in `../docs/DECISIONS.md`.

## Before the defence

Put the PPTX, slide PDF, paper PDF, and this folder on your pen drive. Open the free API a few
minutes before presenting so it has time to wake up. Keep the local demo ready as a backup.
All three team members must attend; the notice requires formal dress and reporting 15 minutes early.
The final defence is 20 November 2026. The allotted time and venue are not in the provided notice.

The paper is prepared for the college submission. Journal acceptance/publication is a separate
editorial process; no acceptance or publication certificate has been invented.

## One-command local backup

From the project directory, run `bash tools/demo.sh`, then open http://127.0.0.1:5173.
It uses local SQLite and the local test chain, so the already-prepared laptop does not need
Supabase or the hosted API. Press Ctrl+C to stop it. Dependencies must already be installed.
