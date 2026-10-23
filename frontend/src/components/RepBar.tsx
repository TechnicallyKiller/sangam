export function RepBar({ value, flagged }: { value: number; flagged?: boolean }) {
  return (
    <div className="repbar" role="meter" aria-valuemin={0} aria-valuemax={1} aria-valuenow={+value.toFixed(2)}>
      <div style={{ width: `${Math.max(2, value * 100)}%` }} className={flagged ? "is-flagged" : ""} />
    </div>
  );
}
