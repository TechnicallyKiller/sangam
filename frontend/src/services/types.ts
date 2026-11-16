export type Role = "aggregator" | "hospital" | "observer";

export interface Hospital {
  id: number;
  name: string;
  city: string;
  address: string;
  records: number;
  color: string;
}

export type TxFn = "registerParticipant" | "openRound" | "submitUpdate" | "recordScores" | "commitGlobalModel" | "closeRound";

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
  epsilonByHospital?: (number | null)[];
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
