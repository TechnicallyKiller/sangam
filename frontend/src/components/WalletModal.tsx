import { useEffect, useState } from "react";
import { ArrowLeft, Loader2, X } from "lucide-react";
import { useWallet } from "../lib/wallet-context";
import { PROVIDERS, WalletAccount, WalletProvider } from "../services/wallet";
import { roleOf } from "../services/ledger";
import { truncate } from "../lib/format";

const MARK: Record<string, string> = { metamask: "M", walletconnect: "W", coinbase: "C" };

export function WalletModal() {
  const { modalOpen, closeModal, connect, listAccounts } = useWallet();
  const [provider, setProvider] = useState<WalletProvider | null>(null);
  const [accounts, setAccounts] = useState<WalletAccount[] | null>(null);

  useEffect(() => { if (!modalOpen) { setProvider(null); setAccounts(null); } }, [modalOpen]);
  if (!modalOpen) return null;

  const pick = async (p: WalletProvider) => {
    setProvider(p);
    setAccounts(await listAccounts(p));
  };

  return (
    <div className="scrim center" onClick={closeModal}>
      <div className="modal brutal" role="dialog" aria-label="Connect wallet" onClick={(e) => e.stopPropagation()}>
        <header>
          {provider && <button className="icon-btn" onClick={() => { setProvider(null); setAccounts(null); }} aria-label="Back"><ArrowLeft size={18} /></button>}
          <h2>{provider ? `Select an account` : "Connect a wallet"}</h2>
          <button className="icon-btn" onClick={closeModal} aria-label="Close"><X size={18} /></button>
        </header>

        {!provider && (
          <>
            <p className="muted">Sign in with the account that holds your role in the consortium. Reading the chain needs no wallet.</p>
            <ul className="plist">
              {PROVIDERS.map((p) => (
                <li key={p.id}>
                  <button onClick={() => pick(p)}>
                    <span className={`pmark pm-${p.id}`}>{MARK[p.id]}</span>
                    <span><b>{p.name}</b><small>{p.hint}</small></span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}

        {provider && !accounts && (
          <div className="waiting"><Loader2 className="spin" size={22} /><p>Approve the request in {provider.name}…</p></div>
        )}

        {provider && accounts && (
          <ul className="plist">
            {accounts.map((a) => (
              <li key={a.address}>
                <button onClick={() => connect(provider, a)}>
                  <span className="pmark pm-acct" />
                  <span>
                    <b>{a.label}</b>
                    <small className="mono">{truncate(a.address, 8, 6)} · {a.balance.toFixed(3)} POL</small>
                  </span>
                  <em className={`role-tag role-${roleOf(a.address)}`}>{roleOf(a.address)}</em>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
