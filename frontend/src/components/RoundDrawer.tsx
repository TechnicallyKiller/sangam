import { useEffect } from "react";
import { X } from "lucide-react";
import { HOSPITALS, Round, fnLabel } from "../services/ledger";
import { fmtGas, fmtTime, pct } from "../lib/format";
import { HashChip } from "./HashChip";
import { PrivacyBadge } from "./PrivacyBadge";
import { RepBar } from "./RepBar";
import { StatusChip } from "./ui";

export function RoundDrawer({ round, onClose }: { round: Round; onClose: () => void }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);

  const gas = round.txs.reduce((a, t) => a + t.gas, 0);
  return (
    <div className="scrim" onClick={onClose}>
      <aside className="drawer" role="dialog" aria-label={`Round ${round.id} detail`} onClick={(e) => e.stopPropagation()}>
        <header>
          <div>
            <span className="eyebrow">Round</span>
            <h2>#{String(round.id).padStart(2, "0")}</h2>
          </div>
          <StatusChip status={round.status} />
          <button className="icon-btn" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </header>

        <section className="kv brutal">
          <div><span>Started from model</span><HashChip value={round.startModelHash} head={8} tail={6} /></div>
          <div><span>Model CID (IPFS)</span><HashChip value={round.startCid} head={10} tail={6} /></div>
          <div><span>New global model</span>{round.globalModelHash ? <HashChip value={round.globalModelHash} head={8} tail={6} /> : <em>pending</em>}</div>
          <div><span>New model CID</span>{round.globalCid ? <HashChip value={round.globalCid} head={10} tail={6} /> : <em>pending</em>}</div>
          <div><span>Test accuracy · AUC</span><b className="mono">{round.accuracy ? `${round.accuracy.toFixed(2)}% · ${round.auc!.toFixed(2)}%` : "—"}</b></div>
          <div><span>Privacy</span><PrivacyBadge spent={round.epsilonSpent} /></div>
          <div><span>Gas, whole round</span><b className="mono">{fmtGas(gas)}</b></div>
        </section>

        <h3>Hospital updates</h3>
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Hospital</th><th>Update hash</th><th>Score</th><th>Weight</th><th>Reputation</th></tr></thead>
            <tbody>
              {round.updates.length === 0 && <tr><td colSpan={5} className="empty">Waiting for hospitals to commit their updates.</td></tr>}
              {round.updates.map((u) => (
                <tr key={u.hospitalId}>
                  <td>{HOSPITALS[u.hospitalId].name}{u.flagged && <span className="chip chip-flagged tight"><i />Flagged</span>}{u.excluded && !u.flagged && <span className="chip chip-excluded tight"><i />Excluded</span>}</td>
                  <td><HashChip value={u.updateHash} /></td>
                  <td className="mono">{u.score ? u.score.toFixed(3) : "—"}</td>
                  <td className="mono">{u.score ? pct(u.weight) : "—"}</td>
                  <td><div className="rep-cell"><RepBar value={u.reputationAfter} flagged={u.flagged} /><span className="mono">{u.reputationAfter.toFixed(2)}</span></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3>Event trail</h3>
        <ol className="trail">
          {round.txs.map((t) => (
            <li key={t.hash}>
              <time className="mono">{fmtTime(t.ts)}</time>
              <div>
                <b>{fnLabel[t.fn]}</b>
                <span>{t.detail}</span>
              </div>
              <HashChip value={t.hash} />
            </li>
          ))}
        </ol>
        <p className="foot">Weights live on IPFS. The chain holds only hashes, CIDs and scores.</p>
      </aside>
    </div>
  );
}
