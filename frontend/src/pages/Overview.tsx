import { useState } from "react";
import { Play } from "lucide-react";
import { useLedger } from "../lib/hooks";
import { useOpenRound } from "../lib/actions";
import { TOTAL_ROUNDS, canOpenRound, fnLabel } from "../services/ledger";
import { Confluence } from "../components/Confluence";
import { AccuracyChart } from "../components/AccuracyChart";
import { PrivacyBadge } from "../components/PrivacyBadge";
import { HashChip } from "../components/HashChip";
import { RoundDrawer } from "../components/RoundDrawer";
import { Button, PageHead, Stat, StatusChip } from "../components/ui";
import { fmtGas, fmtTime } from "../lib/format";

const PHASE: Record<string, string> = {
  training: "Hospitals are training with DP-SGD",
  scoring: "Validators are scoring updates",
  aggregating: "Aggregating the masked sum",
  done: "Round complete",
};

export default function Overview() {
  const { rounds, hospitals, running } = useLedger();
  const openRound = useOpenRound();
  const [drawer, setDrawer] = useState<number | null>(null);
  const current = rounds[rounds.length - 1];
  const lastDone = [...rounds].reverse().find((r) => r.accuracy !== null)!;
  const gas = current.txs.reduce((a, t) => a + t.gas, 0);
  const feed = rounds.flatMap((r) => r.txs).sort((a, b) => b.ts - a.ts).slice(0, 6);
  const exhausted = current.id >= TOTAL_ROUNDS && current.status === "closed";

  return (
    <>
      <PageHead
        title={running ? `Round ${current.id} in progress` : `Round ${current.id} closed`}
        lede={running ? PHASE[current.phase] : "Every hospital's update and every global model is committed on chain. Open the next round to watch the protocol run."}
        actions={
          <Button icon={<Play size={16} />} loading={running} disabled={!running && !canOpenRound() && !exhausted ? true : exhausted} onClick={openRound}>
            {running ? "Round running" : exhausted ? "Training complete" : "Open next round"}
          </Button>
        }
      />

      <section className="stats">
        <Stat label="Global accuracy" value={lastDone.accuracy!.toFixed(2)} unit="%" note={`AUC ${lastDone.auc!.toFixed(2)} · round ${lastDone.id}`} tone="ganga" />
        <Stat label="Training progress" value={`${current.id}`} unit={`/ ${TOTAL_ROUNDS}`} note={`${hospitals.length} hospitals enrolled`} tone="yamuna" />
        <Stat label="Privacy spent" value={<PrivacyBadge spent={current.epsilonSpent} />} note="per hospital, δ = 10⁻⁵" tone="saraswati" />
        <Stat label="Gas this round" value={fmtGas(gas)} note="4 hospitals, hashes only" />
      </section>

      <section className="card confluence-card">
        <div className="card-head">
          <h2>The confluence</h2>
          <div className="head-meta"><StatusChip status={current.status} /><span className="muted">stream width = share of the global model</span></div>
        </div>
        <Confluence round={current} hospitals={hospitals} />
      </section>

      <section className="two-col">
        <div className="card">
          <div className="card-head"><h2>Global model accuracy</h2><span className="muted">Breast Cancer Wisconsin, 4 hospitals</span></div>
          <AccuracyChart rounds={rounds} total={TOTAL_ROUNDS} />
        </div>

        <div className="card brutal-card">
          <div className="card-head"><h2>Latest on chain</h2><span className="live"><i />live</span></div>
          <ul className="feed">
            {feed.map((t) => (
              <li key={t.hash}>
                <time className="mono">{fmtTime(t.ts)}</time>
                <div><b>{fnLabel[t.fn]}</b><span>round {t.round} · {t.detail}</span></div>
                <HashChip value={t.hash} head={4} tail={4} />
              </li>
            ))}
          </ul>
        </div>
      </section>

      {drawer !== null && <RoundDrawer round={rounds.find((r) => r.id === drawer)!} onClose={() => setDrawer(null)} />}
    </>
  );
}
