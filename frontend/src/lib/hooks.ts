import { useSyncExternalStore } from "react";
import { ledger } from "../services/ledger";

export function useLedger() {
  return useSyncExternalStore(ledger.subscribe, ledger.get);
}
