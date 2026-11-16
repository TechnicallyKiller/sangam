import { useState } from "react";
import { X } from "lucide-react";
import { useWallet } from "../lib/wallet-context";
import { authenticate } from "../services/ledger";
import { Button } from "./ui";
export function WalletModal() {
  const { modalOpen, closeModal, connect } = useWallet();
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!modalOpen) return null;
  return <div className="scrim center" onClick={closeModal}>
    <form className="modal brutal" role="dialog" aria-modal="true" aria-label="Operator access" onClick={e => e.stopPropagation()} onSubmit={async e => {
      e.preventDefault(); setBusy(true); setError("");
      try {
        await authenticate(token);
        connect({ id: "operator", name: "Operator", hint: "Private access" }, { address: "operator", label: "Experiment operator", balance: 0 });
        setToken("");
      } catch (e) { setError(e instanceof Error ? e.message : "Could not connect to the API."); }
      finally { setBusy(false); }
    }}>
      <header><h2>Operator access</h2><button className="icon-btn" type="button" onClick={closeModal} aria-label="Close"><X size={18}/></button></header>
      <p className="muted">Reading results is public. Enter the private operator token to run training. Transactions execute on the labelled local test chain.</p>
      <label>Operator token<input type="password" autoComplete="off" value={token} onChange={e => setToken(e.target.value)} required style={{ width: "100%", padding: 12, marginTop: 8 }} /></label>
      {error && <p role="alert" className="t-flagged">{error}</p>}
      <Button type="submit" loading={busy}>Authorize</Button>
    </form>
  </div>;
}
