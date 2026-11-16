import { Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";
import { useLedger } from "./lib/hooks";
import { useWallet } from "./lib/wallet-context";
import { useToast } from "./lib/toast-context";
import { openRound, startPolling } from "./services/ledger";
import { Button } from "./components/ui";
import { Header } from "./components/Header";
import { WalletModal } from "./components/WalletModal";
import { Toasts } from "./components/Toasts";
import Overview from "./pages/Overview";
import Rounds from "./pages/Rounds";
import Participants from "./pages/Participants";
import Audit from "./pages/Audit";

export default function App() {
  useEffect(startPolling, []);
  const state = useLedger();
  const { account, openModal } = useWallet();
  const { push } = useToast();
  const [attack, setAttack] = useState("none");
  const [privacy, setPrivacy] = useState(true);
  const begin = async () => {
    if (!account) return openModal();
    try { await openRound({ attack, privacy, newRun: true }); }
    catch (e) { push({ title: "Could not start experiment", tone: "warn", body: e instanceof Error ? e.message : "API unavailable" }); }
  };
  return (
    <>
      <Header />
      <main className="page">
        <section className="run-banner" aria-live="polite">
          <div><b>{state.connection === "live" ? (state.archived ? "Saved experiment · API connected" : "Live experiment · local Ethereum test chain") : state.connection === "saved" ? "Saved experiment · API offline" : state.loading ? "Connecting to the experiment…" : "API unavailable"}</b><p>Four simulated hospitals · actual training and contract receipts · research prototype</p></div>
          <div className="experiment-controls">
            <label>Hospital D <select value={attack} onChange={e => setAttack(e.target.value)} disabled={state.running}><option value="none">Honest</option><option value="label_flip">Label flip</option><option value="sign_flip">Sign flip</option><option value="free_rider">Free rider</option></select></label>
            <label><input type="checkbox" checked={privacy} onChange={e => setPrivacy(e.target.checked)} disabled={state.running}/> DP-SGD</label>
            <Button variant="secondary" disabled={state.running || state.connection !== "live"} onClick={begin}>{state.rounds.length ? "New experiment" : "Start experiment"}</Button>
          </div>
        </section>
        {state.error && <p className="verdict verdict-miss" role="alert">{state.error}</p>}
        {state.rounds.length > 0 ?
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/rounds" element={<Rounds />} />
          <Route path="/participants" element={<Participants />} />
          <Route path="/audit" element={<Audit />} />
        </Routes>
        : <section className="card"><h1>Sangam</h1><p className="lede">Hospitals train a shared model while patient records stay local. Start an experiment to see measured accuracy, contribution scores, and the contract audit trail.</p><p className="hint">{state.running ? "Preparing the model and contracts…" : "The operator can start a new run. All visitors can inspect its results."}</p></section>}
      </main>
      <footer className="foot-bar"><span>Sangam · Maharaja Agrasen Institute of Technology · CSE-AIML</span><span className="mono">Many rivers, one model.</span></footer>
      <WalletModal />
      <Toasts />
    </>
  );
}
