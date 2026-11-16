import { createContext, ReactNode, useContext, useMemo, useState } from "react";
import type { Role } from "../services/ledger";
import type { WalletAccount, WalletProvider } from "../services/wallet";
interface WalletCtx {
  account: WalletAccount | null; role: Role; modalOpen: boolean;
  openModal: () => void; closeModal: () => void;
  connect: (p: WalletProvider, a: WalletAccount) => void; disconnect: () => void;
}
const Ctx = createContext<WalletCtx | null>(null);
export function WalletProviderTree({ children }: { children: ReactNode }) {
  const [account, setAccount] = useState<WalletAccount | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const value = useMemo<WalletCtx>(() => ({
    account, role: account ? "aggregator" : "observer", modalOpen,
    openModal: () => setModalOpen(true), closeModal: () => setModalOpen(false),
    connect: (_p, a) => { setAccount(a); setModalOpen(false); },
    disconnect: () => { sessionStorage.removeItem("sangam-operator"); setAccount(null); },
  }), [account, modalOpen]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
export function useWallet() {
  const c = useContext(Ctx); if (!c) throw new Error("Operator context unavailable"); return c;
}
