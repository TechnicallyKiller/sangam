import { Hospital, Round } from "../services/ledger";
import { pct } from "../lib/format";

const W = 980, H = 380, MX = 560, MY = 190;

/** The one rich moment in the product: hospitals flow into a single river; the hidden stream runs beneath. */
export function Confluence({ round, hospitals }: { round: Round; hospitals: Hospital[] }) {
  const upd = (id: number) => round.updates.find((u) => u.hospitalId === id);
  const weights = hospitals.map((h) => upd(h.id)?.weight ?? 0);
  const total = weights.reduce((a, b) => a + b, 0);
  const live = round.status !== "closed";
  const riverW = 8 + 64 * (total || 1);

  return (
    <div className="confluence">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Round ${round.id}: hospital contributions merging into the global model`}>
        <defs>
          <linearGradient id="river" gradientUnits="userSpaceOnUse" x1={MX} x2={W - 150} y1="0" y2="0">
            <stop offset="0" stopColor="var(--ganga)" />
            <stop offset="1" stopColor="var(--yamuna)" />
          </linearGradient>
          <filter id="soft" x="-10%" y="-50%" width="120%" height="200%"><feGaussianBlur stdDeviation="9" /></filter>
        </defs>

        {/* Saraswati: the hidden stream, masked updates that nobody sees */}
        <path d={`M170,${MY + 46} C260,${MY + 100} 360,${MY + 20} ${MX},${MY + 34} S800,${MY + 70} ${W - 30},${MY + 40}`}
          className="saraswati-glow" filter="url(#soft)" />
        <path d={`M170,${MY + 46} C260,${MY + 100} 360,${MY + 20} ${MX},${MY + 34} S800,${MY + 70} ${W - 30},${MY + 40}`}
          className="saraswati" />
        <text x={MX + 130} y={MY + 104} className="sa-label">masked updates · visible to no one</text>

        {hospitals.map((h, i) => {
          const y0 = 62 + i * 84;
          const u = upd(h.id);
          const w = u ? 5 + u.weight * 70 : 4;
          const flagged = u?.flagged;
          const d = `M150,${y0} C330,${y0} 380,${MY} ${MX},${MY}`;
          return (
            <g key={`${round.id}-${h.id}`}>
              <path d={d} className={`stream ${flagged ? "stream-flagged" : ""} ${live && !u ? "stream-wait" : ""}`}
                style={{ stroke: flagged ? undefined : h.color, strokeWidth: w, animationDelay: `${i * 140}ms` }} pathLength={1} />
              <circle cx={150} cy={y0} r={6} fill={flagged ? "var(--flagged)" : h.color} />
              <text x={30} y={y0 - 2} className="h-name">{h.name.split(" ")[0]}</text>
              <text x={30} y={y0 + 15} className="h-sub">
                {u ? (u.score === 0 ? "committed" : (flagged ? "flagged · " : "") + pct(u.weight)) : live ? "training…" : "—"}
              </text>
            </g>
          );
        })}

        <path d={`M${MX},${MY} L${W - 150},${MY}`} className="river" style={{ strokeWidth: riverW }} pathLength={1} key={`river-${round.id}-${round.phase}`} />
        <rect x={W - 150} y={MY - 40} width={150} height={80} className="node" />
        <text x={W - 138} y={MY - 14} className="node-t">GLOBAL MODEL</text>
        <text x={W - 138} y={MY + 8} className="node-v">v{round.id}</text>
        <text x={W - 138} y={MY + 28} className="node-s">
          {round.accuracy ? `${round.accuracy.toFixed(2)}% acc` : round.phase}
        </text>
      </svg>
    </div>
  );
}
