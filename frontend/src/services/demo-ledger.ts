/**
 * Ledger service: the single place the UI reads chain state from and writes
 * transactions to. Pages only use the exports below, so pointing this module
 * at web3.py / the FastAPI endpoints does not touch any component.
 */
import { hex, rng } from "../lib/random";

export const TOTAL_ROUNDS = 30;
export const EPSILON_BUDGET = 4;
export const CHAIN = { id: 80002, name: "Polygon Amoy", symbol: "POL" };

export const GAS = {
  openRound: 83_117,
  submitUpdate: 58_246,
  recordScores: 197_384,
  commitGlobalModel: 122_571,
  closeRound: 32_393,
} as const;

export type Role = "aggregator" | "hospital" | "observer";

export interface Hospital {
  id: number;
  name: string;
  city: string;
  address: string;
  records: number;
  color: string;
}

export type TxFn = keyof typeof GAS | "registerParticipant";

export interface Tx {
  hash: string;
  fn: TxFn;
  from: string;
  block: number;
  gas: number;
  ts: number;
  round: number;
  detail: string;
}

export interface UpdateRecord {
  hospitalId: number;
  updateHash: string;
  txHash: string;
  score: number; // 0..1
  weight: number; // aggregation weight, sums to 1 over included hospitals
  flagged: boolean;
  excluded: boolean;
  reputationAfter: number; // 0..1
}

export type RoundStatus = "open" | "aggregated" | "closed";

export interface Round {
  id: number;
  status: RoundStatus;
  startModelHash: string;
  startCid: string;
  globalModelHash: string | null;
  globalCid: string | null;
  accuracy: number | null;
  auc: number | null;
  epsilonSpent: number;
  openedAt: number;
  closedAt: number | null;
  updates: UpdateRecord[];
  txs: Tx[];
  phase: "training" | "scoring" | "aggregating" | "done";
}

export interface Ledger {
  hospitals: Hospital[];
  rounds: Round[];
  reputation: Record<number, number>;
  rewards: Record<number, number>;
  head: number;
  running: boolean;
}

export const AGGREGATOR_ADDRESS = "0x7a3F9bC2e41d08A56E3c91b7D2f0A84c6B15e9D3";
export const COORDINATOR_ADDRESS = "0x2B91c4E7a0F35d86C1b9A74e3D0f58B6a2C7E410";
export const REGISTRY_ADDRESS = "0xC40e8D17b92A63f5E0d4B718a9C3F26e5D81b0A7";

export const HOSPITALS: Hospital[] = [
  { id: 0, name: "Rohini General Hospital", city: "Delhi", address: "0x91Be2A07d4C5f83E16b0a9D72c48F5e3B0A1d6C4", records: 98, color: "var(--ganga)" },
  { id: 1, name: "Dwarka Medical Centre", city: "Delhi", address: "0x3dC70f18A2b9E4565c01F8a7D3e92B64c0fA8E15", records: 104, color: "var(--yamuna)" },
  { id: 2, name: "Saket Diagnostics", city: "Delhi", address: "0xA52f60C9e18B7d43F0a2E95c7B1d86034aC9e2F7", records: 81, color: "var(--verified)" },
  { id: 3, name: "Noida Cancer Institute", city: "Uttar Pradesh", address: "0x68E0b3A5d92F14c7E8a0C63B5f21d94A7e0C3B82", records: 115, color: "var(--clay)" },
];

const SEED_ROUNDS = 18;
const BLOCK_TIME_MS = 2_100;
const GENESIS_BLOCK = 14_820_310;
const T0 = Date.UTC(2026, 9, 20, 9, 30, 0);

// ---- reputation rule (Eq. 4) and weights ------------------------------------

function nextReputation(rep: number[], scores: number[]): number[] {
  const sorted = [...scores].sort((a, b) => a - b);
  const mid = sorted.length / 2;
  const median = sorted.length % 2 ? sorted[Math.floor(mid)] : (sorted[mid - 1] + sorted[mid]) / 2;
  return rep.map((r, i) => (scores[i] < median / 2 ? r / 2 : 0.8 * r + 0.2 * scores[i]));
}

function weightsFor(rep: number[]): { weights: number[]; excluded: boolean[] } {
  const max = Math.max(...rep);
  const excluded = rep.map((r) => r < max / 4);
  const raw = rep.map((r, i) => (excluded[i] ? 0 : HOSPITALS[i].records * r));
  const sum = raw.reduce((a, b) => a + b, 0);
  return { weights: raw.map((w) => w / sum), excluded };
}

// ---- deterministic history ---------------------------------------------------

function accuracyAt(round: number, r: () => number): { accuracy: number; auc: number } {
  const accuracy = 96.7 - 10.2 * Math.exp(-round / 4.4) + (r() - 0.5) * 0.45;
  const auc = 99.45 - 9.5 * Math.exp(-round / 3.6) + (r() - 0.5) * 0.18;
  return { accuracy: +accuracy.toFixed(2), auc: +Math.min(99.9, auc).toFixed(2) };
}

const epsilonAt = (round: number) => +(EPSILON_BUDGET * Math.sqrt(round / TOTAL_ROUNDS)).toFixed(2);

// Rounds where Noida Cancer Institute submits a label-flipped update.
const ATTACK_ROUNDS = new Set([6, 11]);

function mkTx(fn: TxFn, from: string, round: number, ts: number, block: number, detail: string, tag: string): Tx {
  return { hash: hex(`tx:${fn}:${round}:${tag}`, 64), fn, from, block, gas: fn === "registerParticipant" ? 47_526 : GAS[fn], ts, round, detail };
}

function buildSeed(): Ledger {
  const reputation: Record<number, number> = { 0: 0.5, 1: 0.5, 2: 0.5, 3: 0.5 };
  const rewards: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0 };
  const rounds: Round[] = [];
  let block = GENESIS_BLOCK;
  let ts = T0;
  let prevGlobal = hex("model:0", 64);
  let prevCid = cidOf("model:0");

  for (let id = 1; id <= SEED_ROUNDS; id++) {
    const r = rng(`round:${id}`);
    const txs: Tx[] = [];
    const bump = (n = 1) => { block += n; ts += n * BLOCK_TIME_MS + Math.floor(r() * 900); };

    bump(2);
    txs.push(mkTx("openRound", AGGREGATOR_ADDRESS, id, ts, block, `model ${short(prevGlobal)}`, "open"));
    const openedAt = ts;

    const updates: UpdateRecord[] = [];
    const rawScores = HOSPITALS.map((h) => {
      if (h.id === 3 && ATTACK_ROUNDS.has(id)) return 0.04 + r() * 0.06;
      return 0.72 + r() * 0.26;
    });
    HOSPITALS.forEach((h) => {
      bump(1 + Math.floor(r() * 3));
      const tx = mkTx("submitUpdate", h.address, id, ts, block, `keccak256(Δ) from ${h.name}`, `h${h.id}`);
      txs.push(tx);
      updates.push({ hospitalId: h.id, updateHash: hex(`update:${id}:${h.id}`, 64), txHash: tx.hash, score: 0, weight: 0, flagged: false, excluded: false, reputationAfter: 0 });
    });

    const repBefore = HOSPITALS.map((h) => reputation[h.id]);
    const repAfter = nextReputation(repBefore, rawScores);
    const { weights, excluded } = weightsFor(repAfter);
    bump(2);
    txs.push(mkTx("recordScores", AGGREGATOR_ADDRESS, id, ts, block, "4 scores, batched", "scores"));
    const sorted = [...rawScores].sort((a, b) => a - b);
    const median = (sorted[1] + sorted[2]) / 2;
    updates.forEach((u, i) => {
      u.score = rawScores[i];
      u.weight = weights[i];
      u.excluded = excluded[i];
      u.flagged = rawScores[i] < median / 2;
      u.reputationAfter = repAfter[i];
      reputation[u.hospitalId] = repAfter[i];
      rewards[u.hospitalId] += Math.round(rawScores[i] * 10_000);
    });

    const gHash = hex(`model:${id}`, 64);
    const gCid = cidOf(`model:${id}`);
    bump(2);
    txs.push(mkTx("commitGlobalModel", AGGREGATOR_ADDRESS, id, ts, block, `CID ${short(gCid, 8, 4)}`, "commit"));
    bump(1);
    txs.push(mkTx("closeRound", AGGREGATOR_ADDRESS, id, ts, block, "round finalised", "close"));

    const m = accuracyAt(id, r);
    rounds.push({
      id, status: "closed", startModelHash: prevGlobal, startCid: prevCid,
      globalModelHash: gHash, globalCid: gCid, accuracy: m.accuracy, auc: m.auc,
      epsilonSpent: epsilonAt(id), openedAt, closedAt: ts, updates, txs, phase: "done",
    });
    prevGlobal = gHash;
    prevCid = gCid;
    bump(4);
  }

  return { hospitals: HOSPITALS, rounds, reputation, rewards, head: block, running: false };
}

// ---- helpers shared with the UI -----------------------------------------------

export function cidOf(seed: string): string {
  const alphabet = "abcdefghijklmnopqrstuvwxyz234567";
  const r = rng(`cid:${seed}`);
  let s = "bafybei";
  for (let i = 0; i < 52; i++) s += alphabet[Math.floor(r() * alphabet.length)];
  return s;
}

function short(s: string, a = 6, b = 4) {
  return `${s.slice(0, a)}…${s.slice(-b)}`;
}

export function roleOf(address: string | null): Role {
  if (!address) return "observer";
  const a = address.toLowerCase();
  if (a === AGGREGATOR_ADDRESS.toLowerCase()) return "aggregator";
  if (HOSPITALS.some((h) => h.address.toLowerCase() === a)) return "hospital";
  return "observer";
}

// ---- store ---------------------------------------------------------------------

let state: Ledger = buildSeed();
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

export const ledger = {
  get: () => state,
  subscribe(fn: () => void) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
};

function patchRound(id: number, fn: (r: Round) => Round, extra: Partial<Ledger> = {}) {
  state = { ...state, ...extra, rounds: state.rounds.map((r) => (r.id === id ? fn(r) : r)) };
  emit();
}

const sleep = (ms: number) => new Promise((res) => setTimeout(res, ms));

export interface TxEvent { fn: TxFn; hash: string; round: number; hospital?: string }
type Listener = (e: TxEvent) => void;
const txListeners = new Set<Listener>();
export const onTx = (fn: Listener) => { txListeners.add(fn); return () => { txListeners.delete(fn); }; };

/** Gas estimate shown in the wallet confirmation sheet. */
export function estimateGas(fn: TxFn): number {
  return fn === "registerParticipant" ? 47_526 : GAS[fn];
}

export function canOpenRound(): boolean {
  const last = state.rounds[state.rounds.length - 1];
  return !state.running && last.status === "closed" && last.id < TOTAL_ROUNDS;
}

/**
 * Aggregator opens the next round; hospitals train, commit, are scored, and the
 * aggregator commits the global model and closes the round.
 */
export async function openRound(): Promise<void> {
  if (!canOpenRound()) return;
  const prev = state.rounds[state.rounds.length - 1];
  const id = prev.id + 1;
  const r = rng(`round:${id}`);
  let block = state.head;
  let ts = Date.now();
  const push = (tx: Tx) => {
    patchRound(id, (x) => ({ ...x, txs: [...x.txs, tx] }), { head: tx.block });
    txListeners.forEach((l) => l({ fn: tx.fn, hash: tx.hash, round: id, hospital: HOSPITALS.find((h) => h.address === tx.from)?.name }));
  };

  block += 2;
  const openTx = mkTx("openRound", AGGREGATOR_ADDRESS, id, ts, block, `model ${short(prev.globalModelHash!)}`, "open");
  state = {
    ...state, running: true, head: block,
    rounds: [...state.rounds, {
      id, status: "open", startModelHash: prev.globalModelHash!, startCid: prev.globalCid!,
      globalModelHash: null, globalCid: null, accuracy: null, auc: null, epsilonSpent: epsilonAt(id),
      openedAt: ts, closedAt: null, updates: [], txs: [openTx], phase: "training",
    }],
  };
  emit();
  txListeners.forEach((l) => l({ fn: "openRound", hash: openTx.hash, round: id }));

  const rawScores = HOSPITALS.map((h) => (h.id === 3 && ATTACK_ROUNDS.has(id) ? 0.05 : 0.72 + r() * 0.26));
  for (const h of HOSPITALS) {
    await sleep(1_100 + Math.floor(r() * 700));
    block += 1 + Math.floor(r() * 3);
    ts = Date.now();
    const tx = mkTx("submitUpdate", h.address, id, ts, block, `keccak256(Δ) from ${h.name}`, `h${h.id}`);
    patchRound(id, (x) => ({
      ...x,
      updates: [...x.updates, { hospitalId: h.id, updateHash: hex(`update:${id}:${h.id}`, 64), txHash: tx.hash, score: 0, weight: 0, flagged: false, excluded: false, reputationAfter: state.reputation[h.id] }],
    }));
    push(tx);
  }

  await sleep(900);
  patchRound(id, (x) => ({ ...x, phase: "scoring" }));
  await sleep(1_400);
  const repBefore = HOSPITALS.map((h) => state.reputation[h.id]);
  const repAfter = nextReputation(repBefore, rawScores);
  const { weights, excluded } = weightsFor(repAfter);
  const sorted = [...rawScores].sort((a, b) => a - b);
  const median = (sorted[1] + sorted[2]) / 2;
  block += 2;
  const scoresTx = mkTx("recordScores", AGGREGATOR_ADDRESS, id, Date.now(), block, "4 scores, batched", "scores");
  const reputation = { ...state.reputation };
  const rewards = { ...state.rewards };
  HOSPITALS.forEach((h, i) => { reputation[h.id] = repAfter[i]; rewards[h.id] += Math.round(rawScores[i] * 10_000); });
  patchRound(id, (x) => ({
    ...x, phase: "aggregating",
    updates: x.updates.map((u, i) => ({ ...u, score: rawScores[i], weight: weights[i], excluded: excluded[i], flagged: rawScores[i] < median / 2, reputationAfter: repAfter[i] })),
  }), { reputation, rewards });
  push(scoresTx);

  await sleep(1_300);
  block += 2;
  const gHash = hex(`model:${id}`, 64);
  const gCid = cidOf(`model:${id}`);
  const m = accuracyAt(id, r);
  const commitTx = mkTx("commitGlobalModel", AGGREGATOR_ADDRESS, id, Date.now(), block, `CID ${short(gCid, 8, 4)}`, "commit");
  patchRound(id, (x) => ({ ...x, status: "aggregated", globalModelHash: gHash, globalCid: gCid, accuracy: m.accuracy, auc: m.auc }));
  push(commitTx);

  await sleep(1_000);
  block += 1;
  const closeTx = mkTx("closeRound", AGGREGATOR_ADDRESS, id, Date.now(), block, "round finalised", "close");
  patchRound(id, (x) => ({ ...x, status: "closed", closedAt: closeTx.ts, phase: "done" }), { running: false });
  push(closeTx);
}

// ---- lookups --------------------------------------------------------------------

export type HashMatch =
  | { kind: "update"; round: Round; update: UpdateRecord; hospital: Hospital; tx: Tx }
  | { kind: "model"; round: Round; role: "global" | "start" }
  | { kind: "tx"; round: Round; tx: Tx };

export function lookupHash(input: string): HashMatch | null {
  const q = input.trim().toLowerCase().replace(/^0x/, "");
  if (q.length < 8) return null;
  for (const round of state.rounds) {
    for (const tx of round.txs) {
      if (tx.hash.toLowerCase().replace(/^0x/, "") === q) return { kind: "tx", round, tx };
    }
    for (const update of round.updates) {
      if (update.updateHash.toLowerCase().replace(/^0x/, "") === q) {
        const tx = round.txs.find((t) => t.hash === update.txHash)!;
        return { kind: "update", round, update, hospital: HOSPITALS[update.hospitalId], tx };
      }
    }
    if (round.globalModelHash?.toLowerCase().replace(/^0x/, "") === q) return { kind: "model", round, role: "global" };
    if (round.startModelHash.toLowerCase().replace(/^0x/, "") === q) return { kind: "model", round, role: "start" };
  }
  return null;
}

export const fnLabel: Record<TxFn, string> = {
  registerParticipant: "ParticipantRegistered",
  openRound: "RoundOpened",
  submitUpdate: "UpdateSubmitted",
  recordScores: "ScoreRecorded",
  commitGlobalModel: "GlobalModelCommitted",
  closeRound: "RoundClosed",
};
