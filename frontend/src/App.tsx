import { Route, Routes } from "react-router-dom";
import { Header } from "./components/Header";
import { WalletModal } from "./components/WalletModal";
import { ConfirmSheet } from "./components/ConfirmSheet";
import { Toasts } from "./components/Toasts";
import Overview from "./pages/Overview";
import Rounds from "./pages/Rounds";
import Participants from "./pages/Participants";
import Audit from "./pages/Audit";

export default function App() {
  return (
    <>
      <Header />
      <main className="page">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/rounds" element={<Rounds />} />
          <Route path="/participants" element={<Participants />} />
          <Route path="/audit" element={<Audit />} />
        </Routes>
      </main>
      <footer className="foot-bar"><span>Sangam · Maharaja Agrasen Institute of Technology · CSE-AIML</span><span className="mono">Many rivers, one model.</span></footer>
      <WalletModal />
      <ConfirmSheet />
      <Toasts />
    </>
  );
}
