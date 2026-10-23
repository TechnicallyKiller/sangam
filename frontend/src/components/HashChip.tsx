import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { copyText, truncate } from "../lib/format";

export function HashChip({ value, head = 6, tail = 4, label }: { value: string; head?: number; tail?: number; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className="hash"
      title={`${value}\nClick to copy`}
      aria-label={`Copy ${label ?? "hash"} ${value}`}
      onClick={async (e) => {
        e.stopPropagation();
        if (await copyText(value)) {
          setDone(true);
          setTimeout(() => setDone(false), 1400);
        }
      }}
    >
      <span>{truncate(value, head, tail)}</span>
      {done ? <Check size={13} /> : <Copy size={13} />}
    </button>
  );
}
