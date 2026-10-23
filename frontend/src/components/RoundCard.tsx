import { Round } from "../services/ledger";
import { fmtDateTime } from "../lib/format";
import { HashChip } from "./HashChip";
import { StatusChip } from "./ui";

export function RoundCard({ round, onOpen }: { round: Round; onOpen: () => void }) {
  const flagged = round.updates.filter((u) => u.flagged).length;
  return (
    <article className="round-card" role="button" tabIndex={0} onClick={onOpen} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onOpen()} aria-label={`Open round ${round.id}`}>
      <div className="rc-top">
        <span className="rc-num">#{String(round.id).padStart(2, "0")}</span>
        <StatusChip status={round.status} />
      </div>
      <div className="rc-acc">
        {round.accuracy ? <>{round.accuracy.toFixed(2)}<small>%</small></> : <span className="rc-wait">{round.phase}…</span>}
      </div>
      <dl className="rc-meta">
        <div><dt>Updates</dt><dd>{round.updates.length}/4</dd></div>
        <div><dt>Flagged</dt><dd className={flagged ? "t-flagged" : ""}>{flagged}</dd></div>
        <div><dt>Opened</dt><dd>{fmtDateTime(round.openedAt)}</dd></div>
      </dl>
      {round.globalModelHash && (
        <div className="rc-hash"><HashChip value={round.globalModelHash} label="global model hash" /></div>
      )}
    </article>
  );
}
