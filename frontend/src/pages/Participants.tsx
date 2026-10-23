import { useState } from "react";
import { useLedger } from "../lib/hooks";
import { Hospital, Round } from "../services/ledger";
import { HashChip } from "../components/HashChip";
import { PrivacyBadge } from "../components/PrivacyBadge";
import { RepBar } from "../components/RepBar";
import { RoundDrawer } from "../components/RoundDrawer";
import { PageHead, StatusChip } from "../components/ui";
import { fmtDateTime, pct } from "../lib/format";

export default function Participants() {
  const { hospitals, rounds, reputation, rewards } = useLedger();
  const [selected, setSelected] = useState<number | null>(null);
  const latest = rounds[rounds.length - 1];
  const flagged = rounds.flatMap((r) => r.updates.filter((u) => u.flagged).map((u) => ({ r, u })));
  const stats = (h: Hospital) => {
    const ups = rounds.flatMap((r: Round) => r.updates.filter((u) => u.hospitalId === h.id && u.score > 0));
    return { n: ups.length, avg: ups.reduce((a, u) => a + u.score, 0) / Math.max(1, ups.length), flags: ups.filter((u) => u.flagged).length };
  };

  return (
    <>
      <PageHead title="Participants" lede="Reputation is a public record. It halves after one poor round and rebuilds slowly, so trust is quick to lose and slow to earn." />

      <section className="card">
        <div className="table-wrap">
          <table className="table roomy">
            <thead><tr><th>Hospital</th><th>Account</th><th>Records</th><th>Reputation</th><th>Mean score</th><th>Reward points</th><th>Privacy</th><th>Status</th></tr></thead>
            <tbody>
              {hospitals.map((h) => {
                const s = stats(h);
                const u = latest.updates.find((x) => x.hospitalId === h.id);
                const rep = reputation[h.id];
                return (
                  <tr key={h.id}>
                    <td><b>{h.name}</b><small className="sub">{h.city}</small></td>
                    <td><HashChip value={h.address} head={6} tail={4} label="address" /></td>
                    <td className="mono">{h.records}</td>
                    <td><div className="rep-cell"><RepBar value={rep} flagged={!!u?.flagged} /><span className="mono">{rep.toFixed(2)}</span></div></td>
                    <td className="mono">{s.avg.toFixed(3)}</td>
                    <td className="mono">{rewards[h.id].toLocaleString("en-US")}</td>
                    <td><PrivacyBadge spent={latest.epsilonSpent} /></td>
                    <td>{u?.excluded ? <StatusChip status="excluded" /> : s.flags ? <span className="chip chip-pending"><i />{s.flags} flagged</span> : <StatusChip status="verified" />}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card brutal-card">
        <div className="card-head"><h2>Flagged updates</h2><span className="muted">scored below half the round median</span></div>
        {flagged.length === 0 ? <p className="empty">No update has been flagged.</p> : (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Round</th><th>Hospital</th><th>Update hash</th><th>Score</th><th>Weight given</th><th>Reputation after</th><th>When</th></tr></thead>
              <tbody>
                {flagged.map(({ r, u }) => (
                  <tr key={`${r.id}-${u.hospitalId}`} className="clickable" onClick={() => setSelected(r.id)}>
                    <td className="mono">#{String(r.id).padStart(2, "0")}</td>
                    <td>{hospitals[u.hospitalId].name}</td>
                    <td><HashChip value={u.updateHash} /></td>
                    <td className="mono t-flagged">{u.score.toFixed(3)}</td>
                    <td className="mono">{pct(u.weight)}</td>
                    <td className="mono">{u.reputationAfter.toFixed(2)}</td>
                    <td>{fmtDateTime(r.openedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {selected !== null && <RoundDrawer round={rounds.find((r) => r.id === selected)!} onClose={() => setSelected(null)} />}
    </>
  );
}
