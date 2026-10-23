import { useEffect } from "react";
import { X } from "lucide-react";
import { useToast } from "../lib/toast-context";
import { fnLabel, onTx } from "../services/ledger";
import { truncate } from "../lib/format";

/** Surfaces every transaction that lands on chain while the viewer is on the page. */
export function Toasts() {
  const { toasts, dismiss, push } = useToast();
  useEffect(() => onTx((e) => push({
    tone: "chain",
    title: `${fnLabel[e.fn]} · round ${e.round}`,
    body: `${e.hospital ? e.hospital + " · " : ""}tx ${truncate(e.hash, 8, 6)}`,
  })), [push]);

  return (
    <div className="toasts" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.tone ?? "ok"}`}>
          <div><b>{t.title}</b>{t.body && <span className="mono">{t.body}</span>}</div>
          <button className="icon-btn" onClick={() => dismiss(t.id)} aria-label="Dismiss"><X size={14} /></button>
        </div>
      ))}
    </div>
  );
}
