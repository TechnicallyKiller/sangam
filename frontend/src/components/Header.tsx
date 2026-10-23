import { NavLink, Link } from "react-router-dom";
import { LogOut, Wallet } from "lucide-react";
import { useWallet } from "../lib/wallet-context";
import { useLedger } from "../lib/hooks";
import { CHAIN } from "../services/ledger";
import { truncate } from "../lib/format";
import { Button } from "./ui";

const LINKS = [
  { to: "/", label: "Overview", end: true },
  { to: "/rounds", label: "Rounds" },
  { to: "/participants", label: "Participants" },
  { to: "/audit", label: "Audit" },
];

export function Logo() {
  return (
    <Link to="/" className="logo" aria-label="Sangam home">
      <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden>
        <path d="M2 7c9 0 12 9 14 9" fill="none" stroke="var(--ganga)" strokeWidth="3.2" strokeLinecap="round" />
        <path d="M2 25c9 0 12-9 14-9" fill="none" stroke="var(--yamuna)" strokeWidth="3.2" strokeLinecap="round" />
        <path d="M16 16h14" fill="none" stroke="var(--ink)" strokeWidth="3.2" strokeLinecap="round" />
        <path d="M2 16c6 0 8 0 14 0" fill="none" stroke="var(--saraswati)" strokeWidth="1.6" strokeDasharray="1 4" strokeLinecap="round" />
      </svg>
      <span>Sangam</span>
    </Link>
  );
}

export function Header() {
  const { account, role, openModal, disconnect } = useWallet();
  const { head } = useLedger();
  return (
    <header className="topbar">
      <div className="topbar-in">
        <Logo />
        <nav aria-label="Primary">
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={({ isActive }) => (isActive ? "active" : "")}>{l.label}</NavLink>
          ))}
        </nav>
        <div className="topbar-right">
          <span className="net" title={`Chain ID ${CHAIN.id}`}><i />{CHAIN.name}<em className="mono">#{head.toLocaleString("en-US")}</em></span>
          {account ? (
            <div className="acct">
              <span className="role">{role}</span>
              <span className="mono">{truncate(account.address, 6, 4)}</span>
              <button className="icon-btn" onClick={disconnect} aria-label="Disconnect wallet"><LogOut size={16} /></button>
            </div>
          ) : (
            <Button variant="secondary" icon={<Wallet size={16} />} onClick={openModal}>Connect wallet</Button>
          )}
        </div>
      </div>
    </header>
  );
}
