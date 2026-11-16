import { FormEvent, useMemo, useState } from "react";
import { BadgeCheck, SearchX, ShieldCheck } from "lucide-react";
import { useLedger } from "../lib/hooks";
import { API, COORDINATOR_ADDRESS, HashMatch, REGISTRY_ADDRESS, TxFn, fnLabel, lookupHash } from "../services/ledger";
import { HashChip } from "../components/HashChip";
import { Button, PageHead } from "../components/ui";
import { fmtDateTime, fmtGas } from "../lib/format";

const FILTERS: (TxFn | "all")[] = ["all", "openRound", "submitUpdate", "recordScores", "commitGlobalModel", "closeRound"];

function Result({ m, proof }: { m: HashMatch | null | undefined; proof: string }) {
  if (m === undefined) return null;
  if (m === null) {
    return <div className="verdict verdict-miss"><SearchX size={20} /><div><b>No match on chain</b><span>This hash does not appear in any recorded update, model or transaction.</span></div></div>;
  }
  const what = m.kind === "update" ? `Update from ${m.hospital.name}` : m.kind === "model" ? (m.role === "global" ? "Global model" : "Starting model") : fnLabel[m.tx.fn];
  return (
    <div className="verdict verdict-ok">
      <BadgeCheck size={22} />
      <div>
        <b>{proof} · {what}</b>
        <span>Committed in round {m.round.id}{m.kind !== "model" ? `, block ${m.tx.block.toLocaleString("en-US")}` : ""}.
          {m.kind === "update" && ` Scored ${m.update.score.toFixed(3)}${m.update.flagged ? " and flagged" : ""}.`}
          {m.kind === "model" && m.round.globalCid && ` Stored as ${m.round.globalCid.slice(0, 14)}…`}
        </span>
      </div>
    </div>
  );
}

export default function Audit() {
  const { rounds } = useLedger();
  const [filter, setFilter] = useState<TxFn | "all">("all");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<HashMatch | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [proof, setProof] = useState("Recorded evidence");

  const events = useMemo(
    () => rounds.flatMap((r) => r.txs).sort((a, b) => b.block - a.block || b.ts - a.ts).filter((t) => filter === "all" || t.fn === filter),
    [rounds, filter],
  );
  const example = rounds.flatMap(r => r.updates)[0]?.updateHash || "";

  const verify = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setResult(undefined);
    setProof("Recorded evidence");
    try {
      const r = await fetch(`${API}/audit/verify/${encodeURIComponent(query.trim())}`);
      if (r.ok) { const p = await r.json(); setProof(p.liveVerified ? "Verified against local chain" : p.artifactVerified ? "Model bytes verified · archived receipt" : "Archived receipt"); }
    } catch { /* saved evidence remains available offline */ }
    setResult(lookupHash(query));
    setBusy(false);
  };

  return (
    <>
      <PageHead title="Audit" lede="Inspect actual contract receipts. Verify hashes against the active local chain, or inspect clearly labelled archived evidence after a restart." />

      <section className="card brutal-card verify">
        <div className="card-head"><h2>Verify a hash</h2><span className="muted"><ShieldCheck size={14} /> chain and artifact integrity</span></div>
        <form onSubmit={verify}>
          <input className="mono" value={query} onChange={(e) => { setQuery(e.target.value); setResult(undefined); }} placeholder="0x3fa2…9c1d" aria-label="Hash to verify" spellCheck={false} />
          <Button variant="chain" type="submit" loading={busy} disabled={query.trim().length < 8}>Verify on chain</Button>
        </form>
        <p className="hint">Try a recorded hash: <button type="button" className="linklike mono" onClick={() => { setQuery(example); setResult(undefined); }}>{example.slice(0, 18)}…</button></p>
        <Result m={result} proof={proof} />
      </section>

      <section className="two-col contracts">
        <div className="addr brutal-card"><span className="eyebrow">SangamCoordinator</span><HashChip value={COORDINATOR_ADDRESS} head={10} tail={8} label="coordinator address" /></div>
        <div className="addr brutal-card"><span className="eyebrow">ReputationRegistry</span><HashChip value={REGISTRY_ADDRESS} head={10} tail={8} label="registry address" /></div>
      </section>

      <section className="card brutal-card">
        <div className="card-head">
          <h2>Event log</h2>
          <div className="filters" role="tablist" aria-label="Filter events">
            {FILTERS.map((f) => (
              <button key={f} role="tab" aria-selected={filter === f} className={filter === f ? "on" : ""} onClick={() => setFilter(f)}>
                {f === "all" ? "All" : fnLabel[f]}
              </button>
            ))}
          </div>
        </div>
        <div className="table-wrap tall">
          <table className="table log">
            <thead><tr><th>Block</th><th>Event</th><th>Round</th><th>Detail</th><th>Gas</th><th>When</th><th>Tx hash</th></tr></thead>
            <tbody>
              {events.map((t) => (
                <tr key={t.hash}>
                  <td className="mono">{t.block.toLocaleString("en-US")}</td>
                  <td><span className={`ev ev-${t.fn}`}>{fnLabel[t.fn]}</span></td>
                  <td className="mono">#{String(t.round).padStart(2, "0")}</td>
                  <td>{t.detail}</td>
                  <td className="mono">{fmtGas(t.gas)}</td>
                  <td>{fmtDateTime(t.ts)}</td>
                  <td><HashChip value={t.hash} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
