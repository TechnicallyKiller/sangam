import { ShieldCheck } from "lucide-react";
import { EPSILON_BUDGET } from "../services/ledger";

export function PrivacyBadge({ spent }: { spent: number }) {
  return (
    <span className="privacy" title={`Privacy budget spent per hospital (δ = 1e-5)`}>
      <ShieldCheck size={14} />
      ε {spent.toFixed(2)} <em>/ {EPSILON_BUDGET.toFixed(1)}</em>
    </span>
  );
}
