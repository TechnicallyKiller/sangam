import { useState } from "react";
import { Play } from "lucide-react";
import { useLedger } from "../lib/hooks";
import { useOpenRound } from "../lib/actions";
import { TOTAL_ROUNDS, canOpenRound } from "../services/ledger";
import { RoundCard } from "../components/RoundCard";
import { RoundDrawer } from "../components/RoundDrawer";
import { AccuracyChart } from "../components/AccuracyChart";
import { Button, PageHead } from "../components/ui";

export default function Rounds() {
  const { rounds, running } = useLedger();
  const openRound = useOpenRound();
  const [selected, setSelected] = useState<number | null>(null);
  const exhausted = rounds[rounds.length - 1].id >= TOTAL_ROUNDS && !running;

  return (
    <>
      <PageHead
        title="Rounds"
        lede="Each card is one training round, as the contract recorded it. Select one to see who committed what, how it was scored, and the exact transactions."
        actions={<Button icon={<Play size={16} />} loading={running} disabled={!running && !canOpenRound()} onClick={openRound}>{exhausted ? "Training complete" : "Open next round"}</Button>}
      />
      <section className="card">
        <div className="card-head"><h2>Accuracy by round</h2><span className="muted">{rounds.filter((r) => r.accuracy).length} of {TOTAL_ROUNDS} rounds</span></div>
        <AccuracyChart rounds={rounds} total={TOTAL_ROUNDS} />
      </section>
      <section className="round-grid">
        {[...rounds].reverse().map((r) => <RoundCard key={r.id} round={r} onOpen={() => setSelected(r.id)} />)}
      </section>
      {selected !== null && <RoundDrawer round={rounds.find((r) => r.id === selected)!} onClose={() => setSelected(null)} />}
    </>
  );
}
