import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useLocation, useParams, useSearchParams } from "react-router-dom";

import { api, fieldErrors } from "../api/client";
import { useBookedDates, useListing, useReviews } from "../api/queries";
import type { Booking, DateRange, Listing } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ListingCover } from "../components/ListingCover";
import { RangeCalendar, type Range } from "../components/RangeCalendar";
import { Rating, Stars } from "../components/Rating";
import { EmptyState, Notice, Spinner } from "../components/ui";
import { formatMoney, formatShortDate, formatTimestamp, nightsBetween, plural, today } from "../lib/format";
import { paymentErrorMessage, usePayForBooking } from "../lib/payments";

export function ListingPage() {
  const id = Number(useParams().id);
  const listing = useListing(id);
  const reviews = useReviews({ property: id });

  if (listing.isPending) return <Spinner label="Loading stay" />;
  if (listing.isError) {
    return (
      <div className="page">
        <EmptyState title="This stay isn't available" action={<Link className="btn btn--primary" to="/">Browse stays</Link>}>
          It may have been removed by its host.
        </EmptyState>
      </div>
    );
  }

  const stay = listing.data;
  const extraPhotos = stay.images.slice(1, 3);

  return (
    <div className="page listing">
      <Link to="/" className="back-link">
        ← All stays
      </Link>

      <header className="listing-head">
        <p className="eyebrow">
          {stay.city}, {stay.country}
        </p>
        <h1 className="page-title">{stay.title}</h1>
        <div className="listing-meta">
          <Rating average={stay.average_rating} count={stay.review_count} />
          <span className="dot" aria-hidden="true">·</span>
          <span>Hosted by {stay.host.name}</span>
          <span className="dot" aria-hidden="true">·</span>
          <span>Up to {plural(stay.max_guests, "guest")}</span>
        </div>
      </header>

      <div className={`gallery gallery--${Math.min(stay.images.length, 3) || 1}`}>
        <ListingCover listing={stay} size="hero" />
        {extraPhotos.map((photo) => (
          <div key={photo.id} className="cover cover--hero">
            <img src={photo.image} alt={photo.caption || stay.title} loading="lazy" />
          </div>
        ))}
      </div>

      <div className="listing-columns">
          <section className="listing-section listing-about">
            <h2 className="section-title section-title--sm">About this place</h2>
            <p className="listing-description">{stay.description}</p>
            <dl className="facts">
              <div>
                <dt>Address</dt>
                <dd>{stay.address}</dd>
              </div>
              <div>
                <dt>Sleeps</dt>
                <dd>{plural(stay.max_guests, "guest")}</dd>
              </div>
              <div>
                <dt>Nightly price</dt>
                <dd className="mono">{formatMoney(stay.price_per_night)}</dd>
              </div>
            </dl>
          </section>

          <section className="listing-section listing-reviews" aria-labelledby="reviews-title">
            <div className="reviews-head">
              <h2 id="reviews-title" className="section-title section-title--sm">
                Reviews
              </h2>
              <Rating average={stay.average_rating} count={stay.review_count} />
            </div>
            {reviews.isPending ? (
              <Spinner label="Loading reviews" />
            ) : !reviews.data?.results.length ? (
              <p className="muted">No reviews yet. Guests can review a stay after they check out.</p>
            ) : (
              <ul className="reviews">
                {reviews.data.results.map((review) => (
                  <li key={review.id} className="review">
                    <div className="review-head">
                      <span className="review-author">{review.author.name}</span>
                      <span className="review-date">{formatTimestamp(review.created_at)}</span>
                    </div>
                    <Stars value={review.rating} />
                    {review.comment && <p className="review-comment">{review.comment}</p>}
                  </li>
                ))}
              </ul>
            )}
          </section>

        <aside className="listing-aside" aria-label="Book this stay">
          <BookingPanel listing={stay} />
        </aside>
      </div>
    </div>
  );
}

function initialRange(params: URLSearchParams): Range {
  const start = params.get("check_in") ?? undefined;
  const end = params.get("check_out") ?? undefined;
  if (start && end && start >= today() && end > start) return { start, end };
  return {};
}

function overlapsBooked(range: Range, booked: DateRange[]) {
  if (!range.start || !range.end) return false;
  return booked.some((b) => b.check_in < range.end! && b.check_out > range.start!);
}

function BookingPanel({ listing }: { listing: Listing }) {
  const { user, status } = useAuth();
  const location = useLocation();
  const [params] = useSearchParams();
  const queryClient = useQueryClient();
  const booked = useBookedDates(listing.id);

  const [range, setRange] = useState<Range>(() => initialRange(params));
  const [guests, setGuests] = useState(() =>
    Math.min(Math.max(Number(params.get("guests")) || 1, 1), listing.max_guests),
  );
  const [reserved, setReserved] = useState<Booking>();

  const reserve = useMutation({
    mutationFn: () =>
      api<Booking>("/api/bookings/", {
        method: "POST",
        body: { property: listing.id, check_in: range.start, check_out: range.end, guests },
      }),
    onSuccess: (booking) => {
      setReserved(booking);
      queryClient.invalidateQueries({ queryKey: ["listing", listing.id, "booked-dates"] });
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
    },
  });
  const pay = usePayForBooking();

  const bookedRanges = booked.data ?? [];
  // Dates carried over from the search may have been taken since.
  const effectiveRange = overlapsBooked(range, bookedRanges) ? {} : range;
  const nights = effectiveRange.start && effectiveRange.end ? nightsBetween(effectiveRange.start, effectiveRange.end) : 0;
  const total = nights * Number(listing.price_per_night);
  const isOwnListing = user?.id === listing.host.id;
  const errors = fieldErrors(reserve.error);

  return (
    <div className="bookingtag">
      <span className="bookingtag-eyelet" aria-hidden="true" />
      <p className="bookingtag-price">
        <span className="mono">{formatMoney(listing.price_per_night)}</span> <span className="muted">night</span>
      </p>

      {reserved ? (
        <div className="bookingtag-done">
          <p className="bookingtag-done-title">Reserved</p>
          <p>
            {formatShortDate(reserved.check_in)} – {formatShortDate(reserved.check_out)} ·{" "}
            {plural(reserved.guests, "guest")} · <span className="mono">{formatMoney(reserved.total_price)}</span>
          </p>
          <p className="muted">Pay now to confirm your stay. Unpaid reservations are released after an hour.</p>
          {pay.isError && <Notice tone="error">{paymentErrorMessage(pay.error)}</Notice>}
          <button
            type="button"
            className="btn btn--primary btn--block"
            onClick={() => pay.mutate(reserved.id)}
            disabled={pay.isPending}
          >
            {pay.isPending ? "Opening secure checkout…" : `Pay ${formatMoney(reserved.total_price)}`}
          </button>
          <Link to="/trips" className="btn btn--ghost btn--block">
            Go to your trips
          </Link>
        </div>
      ) : (
        <>
          {booked.isPending ? (
            <Spinner label="Loading availability" />
          ) : (
            <RangeCalendar value={effectiveRange} onChange={setRange} booked={bookedRanges} />
          )}

          <div className="guest-stepper">
            <span id="guests-label">Guests</span>
            <div className="stepper" role="group" aria-labelledby="guests-label">
              <button
                type="button"
                onClick={() => setGuests((g) => Math.max(1, g - 1))}
                disabled={guests <= 1}
                aria-label="Fewer guests"
              >
                −
              </button>
              <output aria-live="polite">{guests}</output>
              <button
                type="button"
                onClick={() => setGuests((g) => Math.min(listing.max_guests, g + 1))}
                disabled={guests >= listing.max_guests}
                aria-label="More guests"
              >
                +
              </button>
            </div>
          </div>

          {nights > 0 && (
            <dl className="breakdown">
              <div>
                <dt>
                  {formatMoney(listing.price_per_night)} × {plural(nights, "night")}
                </dt>
                <dd className="mono">{formatMoney(total)}</dd>
              </div>
              <div className="breakdown-total">
                <dt>Total</dt>
                <dd className="mono">{formatMoney(total)}</dd>
              </div>
            </dl>
          )}

          {reserve.isError && <Notice tone="error">{errors.guests ?? reserve.error.message}</Notice>}

          {isOwnListing ? (
            <>
              <p className="muted">This is your listing.</p>
              <Link to={`/hosting/listings/${listing.id}`} className="btn btn--ghost btn--block">
                Edit listing
              </Link>
            </>
          ) : status === "signed-in" ? (
            <button
              type="button"
              className="btn btn--primary btn--block"
              disabled={!nights || reserve.isPending}
              onClick={() => reserve.mutate()}
            >
              {reserve.isPending ? "Reserving…" : nights ? `Reserve ${plural(nights, "night")}` : "Choose your dates"}
            </button>
          ) : (
            <Link
              to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
              className="btn btn--primary btn--block"
            >
              Log in to book
            </Link>
          )}
          <p className="bookingtag-note">You won't be charged until you confirm payment.</p>
        </>
      )}
    </div>
  );
}
