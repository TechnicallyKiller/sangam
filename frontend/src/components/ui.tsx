import { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { RoundStatus } from "../services/ledger";

type Variant = "primary" | "secondary" | "chain" | "ghost";

interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({ variant = "primary", loading, icon, children, className = "", disabled, ...rest }: BtnProps) {
  return (
    <button className={`btn btn-${variant} ${className}`} disabled={disabled || loading} {...rest}>
      {loading ? <Loader2 size={16} className="spin" /> : icon}
      {children}
    </button>
  );
}

const STATUS_LABEL: Record<RoundStatus | "flagged" | "verified" | "excluded", string> = {
  open: "Open", aggregated: "Aggregated", closed: "Closed",
  flagged: "Flagged", verified: "Verified", excluded: "Excluded",
};

export function StatusChip({ status }: { status: keyof typeof STATUS_LABEL }) {
  return (
    <span className={`chip chip-${status}`}>
      <i />
      {STATUS_LABEL[status]}
    </span>
  );
}

export function Stat({ label, value, unit, note, tone }: { label: string; value: ReactNode; unit?: string; note?: ReactNode; tone?: "ganga" | "yamuna" | "saraswati" }) {
  return (
    <div className={`stat ${tone ? `stat-${tone}` : ""}`}>
      <span className="eyebrow">{label}</span>
      <div className="stat-value">
        {value}
        {unit && <small>{unit}</small>}
      </div>
      {note && <span className="stat-note">{note}</span>}
    </div>
  );
}

export function PageHead({ title, lede, actions }: { title: string; lede?: string; actions?: ReactNode }) {
  return (
    <header className="page-head">
      <div>
        <h1>{title}</h1>
        {lede && <p className="lede">{lede}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}
