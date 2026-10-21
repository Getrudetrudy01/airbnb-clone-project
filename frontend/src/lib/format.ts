// Dates travel as "YYYY-MM-DD" strings. They're handled as local calendar days throughout,
// never as UTC timestamps, so a stay never shifts by a day in another time zone.

const pad = (n: number) => String(n).padStart(2, "0");

export function toISODate(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function parseISODate(value: string): Date {
  const [y, m, d] = value.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function addDays(value: string, days: number): string {
  const date = parseISODate(value);
  date.setDate(date.getDate() + days);
  return toISODate(date);
}

export function today(): string {
  return toISODate(new Date());
}

export function nightsBetween(checkIn: string, checkOut: string): number {
  const ms = parseISODate(checkOut).getTime() - parseISODate(checkIn).getTime();
  return Math.round(ms / 86_400_000);
}

const shortDate = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short" });
const longDate = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
const monthYear = new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" });

export const formatShortDate = (value: string) => shortDate.format(parseISODate(value));
export const formatLongDate = (value: string) => longDate.format(parseISODate(value));
export const formatMonth = (date: Date) => monthYear.format(date);

export function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" }).format(new Date(value));
}

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const currencyExact = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** Whole dollars when the amount is whole, cents otherwise. */
export function formatMoney(amount: string | number): string {
  const value = Number(amount);
  return Number.isInteger(value) ? currency.format(value) : currencyExact.format(value);
}

export function plural(count: number, one: string, many = `${one}s`) {
  return `${count} ${count === 1 ? one : many}`;
}
