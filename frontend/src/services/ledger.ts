/** Real API state; offline evidence is a measured exported run, never generated data. */
import type { Ledger as BaseLedger, Round, TxFn, Hospital, UpdateRecord, Tx } from "./types";
export type { Round, TxFn, Hospital, UpdateRecord, Tx, Role, RoundStatus } from "./types";
export interface Ledger extends BaseLedger {
  loading: boolean; connection: "live" | "saved" | "unavailable";
  error: string | null; archived: boolean; runId: string;
  attack: string; privacy: boolean; storage: string;
}
export const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
export let TOTAL_ROUNDS = 30;
export const EPSILON_BUDGET = 4;
export let CHAIN = { id: 0, name: "Connecting", symbol: "test ETH" };
export let AGGREGATOR_ADDRESS = "";
export let COORDINATOR_ADDRESS = "";
export let REGISTRY_ADDRESS = "";
export let HOSPITALS: Hospital[] = [];
let state: Ledger = { hospitals: [], rounds: [], reputation: {}, rewards: {}, head: 0, running: false, loading: true, connection: "unavailable", error: null, archived: false, runId: "", attack: "none", privacy: true, storage: "Off-chain model storage" };
const listeners = new Set<() => void>();
const txListeners = new Set<(e: TxEvent) => void>();
let known = new Set<string>();
let loaded = false;
export const ledger = {
  get: () => state,
  subscribe(fn: () => void) { listeners.add(fn); return () => { listeners.delete(fn); }; },
};
const emit = () => listeners.forEach(fn => fn());
function accept(data: any, connection: Ledger["connection"]) {
  const txs: Tx[] = data.rounds.flatMap((r: Round) => r.txs);
  if (loaded && data.runId === state.runId) {
    txs.filter(t => !known.has(t.hash)).forEach(t => txListeners.forEach(fn => fn({ fn: t.fn, hash: t.hash, round: t.round })));
  }
  known = new Set(txs.map(t => t.hash)); loaded = true;
  CHAIN = data.chain; TOTAL_ROUNDS = data.totalRounds;
  AGGREGATOR_ADDRESS = data.aggregator; COORDINATOR_ADDRESS = data.coordinator;
  REGISTRY_ADDRESS = data.registry; HOSPITALS = data.hospitals;
  state = { ...data, loading: false, connection };
  emit();
}
export async function refresh() {
  try {
    const response = await fetch(`${API}/state`, { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error("API unavailable");
    accept(await response.json(), "live");
  } catch {
    if (!loaded) {
      try {
        const r = await fetch("/evidence.json");
        if (!r.ok) throw new Error();
        const data = await r.json();
        accept({ ...data, running: false, archived: true }, "saved");
        return;
      } catch { /* show an honest empty state */ }
    }
    state = { ...state, loading: false, running: false, connection: loaded ? "saved" : "unavailable" };
    emit();
  }
}
let polling = false;
export function startPolling() {
  if (polling) return () => {};
  polling = true; void refresh();
  const timer = setInterval(() => { void refresh(); }, 2500);
  return () => { clearInterval(timer); polling = false; };
}
export function operatorToken() { return sessionStorage.getItem("sangam-operator") || ""; }
export async function authenticate(token: string) {
  const r = await fetch(`${API}/auth/check`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
  if (!r.ok) throw new Error("The operator token was not accepted.");
  sessionStorage.setItem("sangam-operator", token);
}
export function canOpenRound() { return state.connection === "live" && !state.archived && !state.running && !state.error && state.rounds.length < TOTAL_ROUNDS; }
export async function openRound(options: { attack?: string; privacy?: boolean; newRun?: boolean } = {}) {
  const r = await fetch(`${API}/rounds/open`, {
    method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${operatorToken()}` },
    body: JSON.stringify(options),
  });
  if (!r.ok) { const body = await r.json(); throw new Error(body.detail || "Could not start the round."); }
  await refresh();
}
export function roleOf(address: string | null) { return address === "operator" ? "aggregator" as const : "observer" as const; }
export interface TxEvent { fn: TxFn; hash: string; round: number; hospital?: string }
export const onTx = (fn: (e: TxEvent) => void) => { txListeners.add(fn); return () => { txListeners.delete(fn); }; };
export const estimateGas = (_fn: TxFn) => 0;
export type HashMatch =
  | { kind: "update"; round: Round; update: UpdateRecord; hospital: Hospital; tx: Tx }
  | { kind: "model"; round: Round; role: "global" | "start" }
  | { kind: "tx"; round: Round; tx: Tx };
export function lookupHash(input: string): HashMatch | null {
  const q = input.trim().toLowerCase();
  for (const round of state.rounds) {
    for (const tx of round.txs) if (tx.hash.toLowerCase() === q) return { kind: "tx", round, tx };
    for (const update of round.updates) if (update.updateHash.toLowerCase() === q) return { kind: "update", round, update, hospital: HOSPITALS[update.hospitalId], tx: round.txs.find(t => t.hash === update.txHash)! };
    if (round.globalModelHash?.toLowerCase() === q) return { kind: "model", round, role: "global" };
    if (round.startModelHash.toLowerCase() === q) return { kind: "model", round, role: "start" };
  }
  return null;
}
export const fnLabel: Record<TxFn, string> = {
  registerParticipant: "ParticipantRegistered", openRound: "RoundOpened", submitUpdate: "UpdateSubmitted",
  recordScores: "ScoreRecorded", commitGlobalModel: "GlobalModelCommitted", closeRound: "RoundClosed",
};
