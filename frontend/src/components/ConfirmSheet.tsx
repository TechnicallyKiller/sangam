import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useWallet } from "../lib/wallet-context";
import { CHAIN, COORDINATOR_ADDRESS } from "../services/ledger";
import { fmtGas, truncate } from "../lib/format";
import { Button } from "./ui";

const GWEI = 30;

export function ConfirmSheet() {
  const { pending, settle, sign, account } = useWallet();
  const [busy, setBusy] = useState(false);
  if (!pending) return null;
  const fee = (pending.gas * GWEI) / 1e9;

  return (
    <div className="scrim center" onClick={() => !busy && settle(false)}>
      <div className="modal sheet" role="dialog" aria-label="Confirm transaction" onClick={(e) => e.stopPropagation()}>
        <header><h2>Confirm transaction</h2><span className="net"><i />{CHAIN.name}</span></header>
        <p className="sheet-title">{pending.title}</p>
        <dl className="sheet-kv">
          <div><dt>From</dt><dd className="mono">{account ? truncate(account.address, 8, 6) : "—"}</dd></div>
          <div><dt>Contract</dt><dd className="mono">{truncate(pending.to || COORDINATOR_ADDRESS, 8, 6)}</dd></div>
          <div><dt>Function</dt><dd className="mono">{pending.fn}()</dd></div>
          <div><dt>Gas estimate</dt><dd className="mono">{fmtGas(pending.gas)}</dd></div>
          <div><dt>Network fee</dt><dd className="mono">≈ {fee.toFixed(5)} {CHAIN.symbol}</dd></div>
        </dl>
        <div className="sheet-actions">
          <Button variant="secondary" disabled={busy} onClick={() => settle(false)}>Reject</Button>
          <Button
            variant="chain"
            loading={busy}
            onClick={async () => { setBusy(true); await sign(); setBusy(false); settle(true); }}
          >
            {busy ? "Signing" : "Confirm"}
          </Button>
        </div>
        {busy && <p className="muted center-t"><Loader2 size={14} className="spin" /> Waiting for the network…</p>}
      </div>
    </div>
  );
}
