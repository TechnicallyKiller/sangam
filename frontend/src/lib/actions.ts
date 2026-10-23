import { useCallback } from "react";
import { useWallet } from "./wallet-context";
import { useToast } from "./toast-context";
import { COORDINATOR_ADDRESS, canOpenRound, estimateGas, openRound } from "../services/ledger";

/** Wallet-gated "open round": connect if needed, check role, confirm in the wallet, then submit. */
export function useOpenRound() {
  const { account, role, openModal, confirm } = useWallet();
  const { push } = useToast();
  return useCallback(async () => {
    if (!account) return openModal();
    if (role !== "aggregator") {
      push({ tone: "warn", title: "Aggregator account required", body: "Only the aggregator can open a round. Switch accounts to continue." });
      return;
    }
    if (!canOpenRound()) return;
    const ok = await confirm({ fn: "openRound", title: "Open the next training round", to: COORDINATOR_ADDRESS, gas: estimateGas("openRound") });
    if (ok) void openRound();
  }, [account, role, openModal, confirm, push]);
}
