import { useCallback } from "react";
import { useWallet } from "./wallet-context";
import { useToast } from "./toast-context";
import { canOpenRound, openRound } from "../services/ledger";

/** Wallet-gated "open round": connect if needed, check role, confirm in the wallet, then submit. */
export function useOpenRound() {
  const { account, role, openModal } = useWallet();
  const { push } = useToast();
  return useCallback(async () => {
    if (!account) return openModal();
    if (role !== "aggregator") {
      push({ tone: "warn", title: "Aggregator account required", body: "Only the aggregator can open a round. Switch accounts to continue." });
      return;
    }
    if (!canOpenRound()) return;
    try { await openRound(); }
    catch (e) { push({ tone: "warn", title: "Could not start training", body: e instanceof Error ? e.message : "API unavailable" }); }
  }, [account, role, openModal, push]);
}
