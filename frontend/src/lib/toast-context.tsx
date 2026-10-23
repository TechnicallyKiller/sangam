import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";

export interface Toast { id: number; title: string; body?: string; tone?: "chain" | "ok" | "warn" }
interface ToastCtx { push: (t: Omit<Toast, "id">) => void; toasts: Toast[]; dismiss: (id: number) => void }

const Ctx = createContext<ToastCtx | null>(null);
let seq = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);
  const push = useCallback((t: Omit<Toast, "id">) => {
    const id = seq++;
    setToasts((all) => [...all.slice(-3), { ...t, id }]);
    setTimeout(() => dismiss(id), 5200);
  }, [dismiss]);
  return <Ctx.Provider value={{ push, toasts, dismiss }}>{children}</Ctx.Provider>;
}

export function useToast() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useToast outside provider");
  return v;
}

export function useOnMount(fn: () => void | (() => void)) {
  useEffect(fn, []); // eslint-disable-line react-hooks/exhaustive-deps
}
