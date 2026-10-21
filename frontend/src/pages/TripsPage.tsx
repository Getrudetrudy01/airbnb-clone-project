import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { api, fieldErrors } from "../api/client";
import { useBooking, useBookings, useReviews } from "../api/queries";
import type { Booking } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { TripTag } from "../components/TripTag";
import { EmptyState, Notice, Spinner } from "../components/ui";
import { formatMoney, today } from "../lib/format";
import { paymentErrorMessage, usePayForBooking } from "../lib/payments";

type Tab = "upcoming" | "past" | "cancelled";

const TABS: { id: Tab; label: string }[] = [
  { id: "upcoming", label: "Upcoming" },
  { id: "past", label: "Past" },
  { id: "cancelled", label: "Cancelled" },
];

function tabFor(booking: Booking): Tab {
  if (booking.status === "cancelled") return "cancelled";
  return booking.check_out < today() ? "past" : "upcoming";
}

export function TripsPage() {
  const { user } = useAuth();
  const bookings = useBookings();
  const myReviews = useReviews({ author: user?.id }, Boolean(user));
  const [tab, setTab] = useState<Tab>("upcoming");

  // The bookings endpoint also returns bookings on your own listings; trips are the ones you made.
  const trips = (bookings.data?.results ?? []).filter((b) => b.guest === user?.email);
  const reviewedBookings = new Set(myReviews.data?.results.map((r) => r.booking));
  const visible = trips
    .filter((b) => tabFor(b) === tab)
    .sort((a, b) => (tab === "upcoming" ? a.check_in.localeCompare(b.check_in) : b.check_in.localeCompare(a.check_in)));

  return (
    <div className="page">
      <header className="page-head">
        <h1 className="page-title">Your trips</h1>
      </header>

      <div className="tabs" role="tablist" aria-label="Trips">
        {TABS.map((t) => {
          const count = trips.filter((b) => tabFor(b) === t.id).length;
          return (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              className="tab"
              onClick={() => setTab(t.id)}
            >
              {t.label}
              <span className="tab-count">{count}</span>
            </button>
          );
        })}
      </div>

      {bookings.isPending ? (
        <Spinner label="Loading trips" />
      ) : bookings.isError ? (
        <Notice tone="error">{bookings.error.message}</Notice>
      ) : visible.length === 0 ? (
        <EmptyState
          title={
            tab === "upcoming" ? "No upcoming trips" : tab === "past" ? "No past trips yet" : "No cancelled trips"
          }
          action={
            tab === "upcoming" && (
              <Link to="/" className="btn btn--primary">
                Find a place to stay
              </Link>
            )
          }
        >
          {tab === "upcoming" ? "When you book a stay, it shows up here." : undefined}
        </EmptyState>
      ) : (
        <div className="trips">
          {visible.map((booking) => (
            <TripTag key={booking.id} booking={booking}>
              <TripActions booking={booking} reviewed={reviewedBookings.has(booking.id)} />
            </TripTag>
          ))}
        </div>
      )}
    </div>
  );
}

function TripActions({ booking, reviewed }: { booking: Booking; reviewed: boolean }) {
  const queryClient = useQueryClient();
  const pay = usePayForBooking();
  const [reviewing, setReviewing] = useState(false);

  const cancel = useMutation({
    mutationFn: () => api<Booking>(`/api/bookings/${booking.id}/cancel/`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bookings"] }),
  });

  const confirmCancel = () => {
    const refund = booking.status === "confirmed" ? ` You'll be refunded ${formatMoney(booking.total_price)}.` : "";
    if (window.confirm(`Cancel your stay at ${booking.property_title}?${refund}`)) cancel.mutate();
  };

  const tab = tabFor(booking);
  const canCancel = booking.status !== "cancelled" && booking.check_in > today();

  if (tab === "past" && booking.status === "confirmed") {
    if (reviewed) return <p className="muted small">You reviewed this stay. Thanks.</p>;
    return reviewing ? (
      <ReviewForm booking={booking} onDone={() => setReviewing(false)} />
    ) : (
      <button type="button" className="btn btn--primary btn--sm" onClick={() => setReviewing(true)}>
        Review this stay
      </button>
    );
  }

  return (
    <>
      {pay.isError && <Notice tone="error">{paymentErrorMessage(pay.error)}</Notice>}
      {cancel.isError && <Notice tone="error">{cancel.error.message}</Notice>}
      {booking.status === "pending" && (
        <button type="button" className="btn btn--primary btn--sm" onClick={() => pay.mutate(booking.id)} disabled={pay.isPending}>
          {pay.isPending ? "Opening checkout…" : `Pay ${formatMoney(booking.total_price)}`}
        </button>
      )}
      {canCancel && (
        <button type="button" className="btn btn--danger btn--sm" onClick={confirmCancel} disabled={cancel.isPending}>
          {cancel.isPending ? "Cancelling…" : "Cancel booking"}
        </button>
      )}
    </>
  );
}

function ReviewForm({ booking, onDone }: { booking: Booking; onDone: () => void }) {
  const queryClient = useQueryClient();
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  const submit = useMutation({
    mutationFn: () => api("/api/reviews/", { method: "POST", body: { booking: booking.id, rating, comment } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
      queryClient.invalidateQueries({ queryKey: ["listing", booking.property] });
      onDone();
    },
  });
  const errors = fieldErrors(submit.error);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit.mutate();
  };

  return (
    <form className="review-form" onSubmit={onSubmit}>
      <fieldset className="star-input">
        <legend>Your rating</legend>
        {[1, 2, 3, 4, 5].map((n) => (
          <label key={n} className={n <= rating ? "is-on" : ""}>
            <input type="radio" name={`rating-${booking.id}`} value={n} checked={rating === n} onChange={() => setRating(n)} />
            <span aria-hidden="true">★</span>
            <span className="visually-hidden">
              {n} {n === 1 ? "star" : "stars"}
            </span>
          </label>
        ))}
      </fieldset>
      <label className="visually-hidden" htmlFor={`comment-${booking.id}`}>
        What was your stay like?
      </label>
      <textarea
        id={`comment-${booking.id}`}
        rows={3}
        placeholder="What was your stay like? (optional)"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />
      {submit.isError && <Notice tone="error">{errors.booking ?? errors.rating ?? submit.error.message}</Notice>}
      <div className="review-form-actions">
        <button type="submit" className="btn btn--primary btn--sm" disabled={!rating || submit.isPending}>
          {submit.isPending ? "Posting…" : "Post review"}
        </button>
        <button type="button" className="btn btn--ghost btn--sm" onClick={onDone}>
          Not now
        </button>
      </div>
    </form>
  );
}

/** Where Stripe sends the guest back to after checkout. */
export function BookingPage() {
  const id = Number(useParams().id);
  const [params] = useSearchParams();
  const outcome = params.get("payment");
  const booking = useBooking(id, outcome === "success");

  if (booking.isPending) return <Spinner label="Loading booking" />;
  if (booking.isError) {
    return (
      <div className="page">
        <EmptyState title="Booking not found" action={<Link to="/trips" className="btn btn--primary">Go to your trips</Link>} />
      </div>
    );
  }

  const b = booking.data;
  return (
    <div className="page page--narrow">
      <header className="page-head">
        <h1 className="page-title">
          {b.status === "confirmed" ? "You're booked" : b.status === "cancelled" ? "Booking cancelled" : "Almost there"}
        </h1>
      </header>
      {outcome === "success" && b.status === "pending" && (
        <Notice>Payment received. Confirming with your host… this takes a few seconds.</Notice>
      )}
      {outcome === "success" && b.status === "confirmed" && (
        <Notice tone="success">Payment received. Your stay is confirmed.</Notice>
      )}
      {outcome === "cancelled" && (
        <Notice>Payment wasn't completed. Your reservation is held for an hour, so you can pay from your trips.</Notice>
      )}
      <TripTag booking={b}>
        <Link to="/trips" className="btn btn--ghost btn--sm">
          All trips
        </Link>
      </TripTag>
    </div>
  );
}
