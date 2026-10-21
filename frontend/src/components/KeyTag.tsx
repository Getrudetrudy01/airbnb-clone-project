import type { ReactNode } from "react";

interface Row {
  label: string;
  value: ReactNode;
}

interface KeyTagProps {
  /** The big moulded figure, like a room number. */
  figure: ReactNode;
  /** Set when the figure is words rather than a number, so it's sized to fit. */
  figureIsWords?: boolean;
  figureLabel: string;
  rows: Row[];
  /** Changing this replays the swing, so the tag reacts when its contents change. */
  swingKey?: string;
  heading?: string;
}

/**
 * The hanging hotel key tag: Keyhouse's signature element.
 * Purely presentational; the hero uses it to mirror the search as you type.
 */
export function KeyTag({ figure, figureIsWords, figureLabel, rows, swingKey, heading = "Keyhouse · stay" }: KeyTagProps) {
  return (
    <div className="keytag-hanger" aria-hidden="true">
      <span className="keytag-nail" />
      <div className="keytag-swing" key={swingKey}>
        <svg className="keytag-string" viewBox="0 0 40 160" preserveAspectRatio="none">
          <path d="M20 0 C 10 55, 30 105, 20 160" />
        </svg>
        <div className="keytag">
          <span className="keytag-eyelet" />
          <p className="keytag-heading">{heading}</p>
          <p className={`keytag-figure${figureIsWords ? " keytag-figure--words" : ""}`}>{figure}</p>
          <p className="keytag-figure-label">{figureLabel}</p>
          <dl className="keytag-rows">
            {rows.map((row) => (
              <div key={row.label} className="keytag-row">
                <dt>{row.label}</dt>
                <dd>{row.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
