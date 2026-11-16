import { ShieldCheck } from "lucide-react";
import { EPSILON_BUDGET } from "../services/ledger";
import { useLedger } from "../lib/hooks";

export function PrivacyBadge({ spent }: { spent: number }) {
  const { privacy } = useLedger();
  if (!privacy) return <span className="privacy">DP off</span>;
  return (
    <span className="privacy" title={`Privacy budget spent per hospital (δ = 1e-5)`}>
      <ShieldCheck size={14} />
      ε {spent.toFixed(2)} <em>/ {EPSILON_BUDGET.toFixed(1)}</em>
    </span>
  );
}
