import { useMemo, useState } from "react";
import { Round } from "../services/ledger";

const W = 720, H = 280, M = { l: 44, r: 16, t: 16, b: 32 };


export function AccuracyChart({ rounds, total }: { rounds: Round[]; total: number }) {
  const done = rounds.filter((r) => r.accuracy !== null);
  const [hover, setHover] = useState<number | null>(null);
  const min = 0, max = 100;
  const x = (id: number) => M.l + ((id - 1) / (total - 1)) * (W - M.l - M.r);
  const y = (v: number) => M.t + (1 - (v - min) / (max - min)) * (H - M.t - M.b);

  const line = useMemo(() => done.map((r, i) => `${i ? "L" : "M"}${x(r.id).toFixed(1)},${y(r.accuracy!).toFixed(1)}`).join(" "), [done]);
  const area = done.length ? `${line} L${x(done[done.length - 1].id)},${H - M.b} L${x(done[0].id)},${H - M.b} Z` : "";
  const hov = done.find((r) => r.id === hover);

  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Global model test accuracy per round" onMouseLeave={() => setHover(null)}>
        {[0, 25, 50, 75, 100].map((v) => (
          <g key={v}>
            <line x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} className="grid" />
            <text x={M.l - 8} y={y(v) + 4} textAnchor="end" className="tick">{v}%</text>
          </g>
        ))}
        {[1, 5, 10, 15, 20, 25, 30].map((v) => (
          <text key={v} x={x(v)} y={H - 10} textAnchor="middle" className="tick">{v}</text>
        ))}
        <path d={area} className="area" />
        <path d={line} className="line-main" />
        {done.map((r) => (
          <g key={r.id} onMouseEnter={() => setHover(r.id)}>
            <rect x={x(r.id) - 10} y={M.t} width={20} height={H - M.t - M.b} fill="transparent" />
            <circle cx={x(r.id)} cy={y(r.accuracy!)} r={hover === r.id ? 5 : 2.8} className="dot" />
          </g>
        ))}
        {hov && (
          <g transform={`translate(${Math.min(x(hov.id) + 12, W - 150)},${Math.max(y(hov.accuracy!) - 52, 8)})`}>
            <rect width="138" height="44" className="tip" />
            <text x="10" y="18" className="tip-t">Round {hov.id}</text>
            <text x="10" y="35" className="tip-v">{hov.accuracy!.toFixed(2)}% · AUC {hov.auc!.toFixed(2)}</text>
          </g>
        )}
        <text x={M.l} y={H - 0} className="tick" opacity="0">.</text>
      </svg>
      <figcaption>
        <span><i className="key key-main" />Measured Sangam accuracy</span>
      </figcaption>
    </figure>
  );
}
