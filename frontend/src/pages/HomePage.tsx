import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";

import { useListings, type ListingFilters } from "../api/queries";
import { KeyTag } from "../components/KeyTag";
import { ListingCard, ListingCardSkeleton } from "../components/ListingCard";
import { EmptyState, Notice } from "../components/ui";
import { addDays, formatShortDate, nightsBetween, plural, today } from "../lib/format";

const SORTS = [
  { value: "", label: "Newest" },
  { value: "price_per_night", label: "Price: low to high" },
  { value: "-price_per_night", label: "Price: high to low" },
  { value: "-average_rating", label: "Highest rated" },
];

const FILTER_KEYS = ["city", "check_in", "check_out", "guests", "ordering"] as const;

function readFilters(params: URLSearchParams): ListingFilters {
  const filters: ListingFilters = {};
  for (const key of FILTER_KEYS) {
    const value = params.get(key);
    if (value) filters[key] = value;
  }
  return filters;
}

export function HomePage() {
  const [params, setParams] = useSearchParams();
  const filters = readFilters(params);

  // The form is a draft until submitted; the tag mirrors the draft live.
  const [draft, setDraft] = useState({
    city: filters.city ?? "",
    check_in: filters.check_in ?? "",
    check_out: filters.check_out ?? "",
    guests: filters.guests ?? "",
  });
  const [formError, setFormError] = useState<string>();

  const listings = useListings(filters);
  const results = listings.data?.pages.flatMap((page) => page.results) ?? [];
  const count = listings.data?.pages[0]?.count;

  const draftNights =
    draft.check_in && draft.check_out && draft.check_out > draft.check_in
      ? nightsBetween(draft.check_in, draft.check_out)
      : null;

  const update = (key: keyof typeof draft, value: string) => {
    setFormError(undefined);
    setDraft((current) => {
      const next = { ...current, [key]: value };
      // Keep check-out after check-in as people change dates.
      if (key === "check_in" && value && (!next.check_out || next.check_out <= value)) {
        next.check_out = addDays(value, 1);
      }
      return next;
    });
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (Boolean(draft.check_in) !== Boolean(draft.check_out)) {
      setFormError("Add both a check-in and a check-out date, or leave both empty.");
      return;
    }
    const next = new URLSearchParams();
    for (const [key, value] of Object.entries(draft)) if (value.trim()) next.set(key, value.trim());
    if (filters.ordering) next.set("ordering", filters.ordering);
    setParams(next);
    document.getElementById("results")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const setOrdering = (ordering: string) => {
    const next = new URLSearchParams(params);
    if (ordering) next.set("ordering", ordering);
    else next.delete("ordering");
    setParams(next, { replace: true });
  };

  const clearSearch = () => {
    setDraft({ city: "", check_in: "", check_out: "", guests: "" });
    setParams(new URLSearchParams());
  };

  const hasSearch = Boolean(filters.city || filters.check_in || filters.guests);
  // Carry dates and guests into the listing page so the booking panel starts filled in.
  const carry = new URLSearchParams();
  for (const key of ["check_in", "check_out", "guests"] as const) if (filters[key]) carry.set(key, filters[key]!);
  const carryQuery = carry.size ? `?${carry}` : "";

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <h1 className="hero-title">
            Book a place
            <br />
            to stay
          </h1>
          <p className="hero-lede">
            Search homes by city, dates and number of guests. Every stay shows the nightly price and the full total
            before you book.
          </p>

          <form className="search" onSubmit={submit} aria-label="Search stays">
            <div className="search-field search-field--where">
              <label htmlFor="search-city">Where</label>
              <input
                id="search-city"
                type="search"
                placeholder="Any city"
                value={draft.city}
                onChange={(e) => update("city", e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="search-field">
              <label htmlFor="search-in">Check-in</label>
              <input
                id="search-in"
                type="date"
                min={today()}
                value={draft.check_in}
                onChange={(e) => update("check_in", e.target.value)}
              />
            </div>
            <div className="search-field">
              <label htmlFor="search-out">Check-out</label>
              <input
                id="search-out"
                type="date"
                min={draft.check_in ? addDays(draft.check_in, 1) : today()}
                value={draft.check_out}
                onChange={(e) => update("check_out", e.target.value)}
              />
            </div>
            <div className="search-field search-field--guests">
              <label htmlFor="search-guests">Guests</label>
              <select id="search-guests" value={draft.guests} onChange={(e) => update("guests", e.target.value)}>
                <option value="">Any</option>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                  <option key={n} value={n}>
                    {n}
                    {n === 8 ? "+" : ""}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn btn--primary search-submit">
              Search
            </button>
          </form>
          {formError && <Notice tone="error">{formError}</Notice>}
        </div>

        <div className="hero-tag">
          <KeyTag
            swingKey={`${draft.city}|${draft.check_in}|${draft.check_out}|${draft.guests}`}
            figure={
              draftNights ?? (
                <>
                  Your
                  <br />
                  stay
                </>
              )
            }
            figureIsWords={draftNights === null}
            figureLabel={draftNights === null ? "Add your dates" : draftNights === 1 ? "Night" : "Nights"}
            rows={[
              { label: "Where", value: draft.city.trim() || "Anywhere" },
              { label: "In", value: draft.check_in ? formatShortDate(draft.check_in) : "—" },
              { label: "Out", value: draft.check_out ? formatShortDate(draft.check_out) : "—" },
              { label: "Guests", value: draft.guests || "Any" },
            ]}
          />
        </div>
      </section>

      <section className="results" id="results" aria-labelledby="results-title">
        <div className="results-head">
          <div>
            <h2 id="results-title" className="section-title">
              {filters.city ? `Stays in ${filters.city}` : "All stays"}
            </h2>
            <p className="results-sub">
              {count === undefined
                ? "Looking for stays…"
                : filters.check_in && filters.check_out
                  ? `${plural(count, "stay")} free ${formatShortDate(filters.check_in)} – ${formatShortDate(filters.check_out)}`
                  : plural(count, "stay")}
            </p>
          </div>
          <div className="results-tools">
            {hasSearch && (
              <button type="button" className="btn btn--ghost btn--sm" onClick={clearSearch}>
                Clear search
              </button>
            )}
            <label className="sort">
              <span>Sort</span>
              <select value={filters.ordering ?? ""} onChange={(e) => setOrdering(e.target.value)}>
                {SORTS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {listings.isError ? (
          <Notice tone="error">{listings.error.message}</Notice>
        ) : listings.isPending ? (
          <div className="grid">
            {Array.from({ length: 8 }, (_, i) => (
              <ListingCardSkeleton key={i} />
            ))}
          </div>
        ) : results.length === 0 ? (
          <EmptyState
            title={filters.city ? `No stays in ${filters.city} for this search` : "No stays match this search"}
            action={
              <button type="button" className="btn btn--primary" onClick={clearSearch}>
                Show all stays
              </button>
            }
          >
            Try other dates, fewer guests, or a nearby city.
          </EmptyState>
        ) : (
          <>
            <div className={`grid${listings.isPlaceholderData ? " is-refreshing" : ""}`}>
              {results.map((listing) => (
                <ListingCard key={listing.id} listing={listing} search={carryQuery} />
              ))}
            </div>
            {listings.hasNextPage && (
              <div className="results-more">
                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={() => listings.fetchNextPage()}
                  disabled={listings.isFetchingNextPage}
                >
                  {listings.isFetchingNextPage ? "Loading…" : "Show more stays"}
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
}
