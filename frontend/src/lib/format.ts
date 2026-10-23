export const truncate = (s: string, a = 6, b = 4) => (s.length <= a + b + 1 ? s : `${s.slice(0, a)}…${s.slice(-b)}`);

export const fmtTime = (ts: number) =>
  new Date(ts).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

export const fmtDateTime = (ts: number) =>
  new Date(ts).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

export const fmtGas = (n: number) => n.toLocaleString("en-US");

export const pct = (x: number, d = 1) => `${(x * 100).toFixed(d)}%`;

export async function copyText(s: string) {
  try {
    await navigator.clipboard.writeText(s);
    return true;
  } catch {
    return false;
  }
}
