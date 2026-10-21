import { useMemo, useState } from "react";

import type { DateRange } from "../api/types";
import { addDays, formatLongDate, formatMonth, parseISODate, toISODate, today } from "../lib/format";

export interface Range {
  start?: string;
  end?: string;
}

interface RangeCalendarProps {
  value: Range;
  onChange: (range: Range) => void;
  booked: DateRange[];
}

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];

/** Nights that are taken. Check-out days stay free, so the next guest can arrive that day. */
function bookedNights(ranges: DateRange[]) {
  const nights = new Set<string>();
  for (const { check_in, check_out } of ranges) {
    for (let day = check_in; day < check_out; day = addDays(day, 1)) nights.add(day);
  }
  return nights;
}

function monthGrid(month: Date) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const leading = (first.getDay() + 6) % 7; // Monday-first
  const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const cells: (string | null)[] = Array(leading).fill(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(toISODate(new Date(month.getFullYear(), month.getMonth(), d)));
  return cells;
}

export function RangeCalendar({ value, onChange, booked }: RangeCalendarProps) {
  const nights = useMemo(() => bookedNights(booked), [booked]);
  const firstDay = today();
  const [month, setMonth] = useState(() => {
    const anchor = parseISODate(value.start ?? firstDay);
    return new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  });
  const [hovered, setHovered] = useState<string>();

  const choosingEnd = Boolean(value.start && !value.end);

  const rangeIsFree = (start: string, end: string) => {
    for (let day = start; day < end; day = addDays(day, 1)) if (nights.has(day)) return false;
    return true;
  };

  const canStart = (day: string) => day >= firstDay && !nights.has(day);
  const canEnd = (day: string) => Boolean(value.start && day > value.start && rangeIsFree(value.start, day));
  const isSelectable = (day: string) => canStart(day) || (choosingEnd && canEnd(day));

  const select = (day: string) => {
    if (choosingEnd && canEnd(day)) onChange({ start: value.start, end: day });
    else if (canStart(day)) onChange({ start: day, end: undefined });
  };

  const previewEnd = choosingEnd && hovered && canEnd(hovered) ? hovered : value.end;
  const inRange = (day: string) => Boolean(value.start && previewEnd && day > value.start && day < previewEnd);

  const thisMonth = new Date(parseISODate(firstDay).getFullYear(), parseISODate(firstDay).getMonth(), 1);
  const atFirstMonth = month <= thisMonth;
  const shiftMonth = (delta: number) => setMonth(new Date(month.getFullYear(), month.getMonth() + delta, 1));

  return (
    <div className="calendar">
      <div className="calendar-head">
        <button
          type="button"
          className="calendar-nav"
          onClick={() => shiftMonth(-1)}
          disabled={atFirstMonth}
          aria-label="Previous month"
        >
          ‹
        </button>
        <p className="calendar-month" aria-live="polite">
          {formatMonth(month)}
        </p>
        <button type="button" className="calendar-nav" onClick={() => shiftMonth(1)} aria-label="Next month">
          ›
        </button>
      </div>

      <div className="calendar-grid" role="grid" onMouseLeave={() => setHovered(undefined)}>
        {WEEKDAYS.map((d) => (
          <span key={d} className="calendar-weekday" role="columnheader">
            {d}
          </span>
        ))}
        {monthGrid(month).map((day, i) => {
          if (!day) return <span key={`blank-${i}`} />;
          const taken = nights.has(day);
          const selectable = isSelectable(day);
          const isStart = day === value.start;
          const isEnd = day === previewEnd;
          const classes = [
            "calendar-day",
            taken && "is-taken",
            day < firstDay && "is-past",
            inRange(day) && "is-in-range",
            isStart && "is-start",
            isEnd && "is-end",
          ]
            .filter(Boolean)
            .join(" ");
          const state = taken ? ", booked" : !selectable ? ", unavailable" : "";
          return (
            <button
              key={day}
              type="button"
              className={classes}
              disabled={!selectable}
              onClick={() => select(day)}
              onMouseEnter={() => setHovered(day)}
              onFocus={() => setHovered(day)}
              aria-pressed={isStart || isEnd}
              aria-label={`${formatLongDate(day)}${state}`}
            >
              {parseISODate(day).getDate()}
            </button>
          );
        })}
      </div>

      <p className="calendar-help">
        {!value.start
          ? "Choose your check-in day."
          : !value.end
            ? "Now choose your check-out day."
            : "Dates set. Pick a new day to start again."}
        {nights.size > 0 && <span className="calendar-legend"> Struck-through days are booked.</span>}
      </p>
    </div>
  );
}
