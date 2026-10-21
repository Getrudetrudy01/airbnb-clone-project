import { plural } from "../lib/format";

interface RatingProps {
  average: number | null;
  count: number;
  compact?: boolean;
}

export function Rating({ average, count, compact = false }: RatingProps) {
  if (average === null || count === 0) {
    return <span className="rating rating--new">New</span>;
  }
  const label = `Rated ${average.toFixed(1)} out of 5 from ${plural(count, "review")}`;
  return (
    <span className="rating" aria-label={label} title={label}>
      <span aria-hidden="true" className="rating-star">
        ★
      </span>
      <span className="mono">{average.toFixed(1)}</span>
      {!compact && <span className="rating-count">· {plural(count, "review")}</span>}
    </span>
  );
}

export function Stars({ value }: { value: number }) {
  return (
    <span className="stars" aria-label={`${value} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} aria-hidden="true" className={n <= value ? "stars-on" : "stars-off"}>
          ★
        </span>
      ))}
    </span>
  );
}
