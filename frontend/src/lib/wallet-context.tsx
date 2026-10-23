import { createContext, ReactNode, useCallback, useContext, useMemo, useState } from "react";
import { Role, roleOf, TxFn } from "../services/ledger";
import { WalletAccount, WalletProvider, requestAccounts, signTransaction } from "../services/wallet";

interface Pending {
  fn: TxFn;
  title: string;
  to: string;
  gas: number;
  resolve: (ok: boolean) => void;
}

interface WalletCtx {
  account: WalletAccount | null;
  role: Role;
  modalOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
  connect: (p: WalletProvider, a: WalletAccount) => void;
  listAccounts: (p: WalletProvider) => Promise<WalletAccount[]>;
  disconnect: () => void;
  pending: Pending | null;
  confirm: (tx: Omit<Pending, "resolve">) => Promise<boolean>;
  settle: (ok: boolean) => void;
  sign: () => Promise<void>;
}

const Ctx = createContext<WalletCtx | null>(null);

export function WalletProviderTree({ children }: { children: ReactNode }) {
  const [account, setAccount] = useState<WalletAccount | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [pending, setPending] = useState<Pending | null>(null);

  const confirm = useCallback(
    (tx: Omit<Pending, "resolve">) => new Promise<boolean>((resolve) => setPending({ ...tx, resolve })),
    [],
  );

  const value = useMemo<WalletCtx>(
    () => ({
      account,
      role: roleOf(account?.address ?? null),
      modalOpen,
      openModal: () => setModalOpen(true),
      closeModal: () => setModalOpen(false),
      connect: (_p, a) => { setAccount(a); setModalOpen(false); },
      listAccounts: requestAccounts,
      disconnect: () => setAccount(null),
      pending,
      confirm,
      settle: (ok) => { pending?.resolve(ok); setPending(null); },
      sign: signTransaction,
    }),
    [account, modalOpen, pending, confirm],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useWallet() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useWallet outside provider");
  return v;
}
