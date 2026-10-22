import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api, fieldErrors } from "../api/client";
import { useBookings, useHostListings, useListing } from "../api/queries";
import type { Booking, Listing, ListingInput } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ListingCover } from "../components/ListingCover";
import { Rating } from "../components/Rating";
import { TripTag } from "../components/TripTag";
import { EmptyState, Field, Notice, Spinner } from "../components/ui";
import { formatMoney, today } from "../lib/format";

function NotAHost() {
  return (
    <div className="page page--narrow">
      <EmptyState title="Hosting needs a host account">
        Your account is set up for booking stays. To list a place, sign up again with “Host a place” selected.
      </EmptyState>
    </div>
  );
}

export function HostingPage() {
  const { user } = useAuth();
  const listings = useHostListings(user?.id);
  const bookings = useBookings(user?.role === "host");

  if (user?.role !== "host") return <NotAHost />;

  const myListingIds = new Set(listings.data?.results.map((l) => l.id));
  const received = (bookings.data?.results ?? []).filter(
    (b) => myListingIds.has(b.property) && b.guest !== user.email && b.status !== "cancelled" && b.check_out >= today(),
  );
  const requests = received.filter((b) => b.status === "pending");
  const upcoming = received.filter((b) => b.status === "confirmed").sort((a, b) => a.check_in.localeCompare(b.check_in));

  return (
    <div className="page">
      <header className="page-head page-head--split">
        <h1 className="page-title">Hosting</h1>
        {!user.is_demo && (
          <Link to="/hosting/listings/new" className="btn btn--primary">
            List a new place
          </Link>
        )}
      </header>

      {user.is_demo && (
        <Notice>
          You're exploring the shared demo host account. You can confirm and decline bookings, but editing listings is
          turned off so the demo stays the same for everyone. <Link to="/register">Create a host account</Link> to list
          your own place.
        </Notice>
      )}

      <section className="host-section" aria-labelledby="requests-title">
        <h2 id="requests-title" className="section-title section-title--sm">
          Waiting on payment <span className="tab-count">{requests.length}</span>
        </h2>
        <p className="muted small">
          Guests have reserved these dates but haven't paid yet. Confirm one if the guest is paying you another way.
        </p>
        {bookings.isPending || listings.isPending ? (
          <Spinner />
        ) : requests.length === 0 ? (
          <p className="muted">Nothing waiting right now.</p>
        ) : (
          <div className="trips">
            {requests.map((b) => (
              <TripTag key={b.id} booking={b} eyebrow={`Guest: ${b.guest}`}>
                <HostActions booking={b} />
              </TripTag>
            ))}
          </div>
        )}
      </section>

      <section className="host-section" aria-labelledby="upcoming-title">
        <h2 id="upcoming-title" className="section-title section-title--sm">
          Upcoming guests <span className="tab-count">{upcoming.length}</span>
        </h2>
        {upcoming.length === 0 ? (
          <p className="muted">No confirmed guests yet.</p>
        ) : (
          <div className="trips">
            {upcoming.map((b) => (
              <TripTag key={b.id} booking={b} eyebrow={`Guest: ${b.guest}`}>
                <HostActions booking={b} />
              </TripTag>
            ))}
          </div>
        )}
      </section>

      <section className="host-section" aria-labelledby="listings-title">
        <h2 id="listings-title" className="section-title section-title--sm">
          Your listings <span className="tab-count">{listings.data?.count ?? 0}</span>
        </h2>
        {listings.isPending ? (
          <Spinner />
        ) : !listings.data?.results.length ? (
          <EmptyState
            title="You haven't listed a place yet"
            action={
              <Link to="/hosting/listings/new" className="btn btn--primary">
                List a new place
              </Link>
            }
          >
            Add the basics now. You can add photos straight after.
          </EmptyState>
        ) : (
          <div className="host-listings">
            {listings.data.results.map((listing) => (
              <Link key={listing.id} to={`/hosting/listings/${listing.id}`} className="host-listing">
                <ListingCover listing={listing} />
                <div>
                  <p className="host-listing-title">{listing.title}</p>
                  <p className="muted small">
                    {listing.city} · <span className="mono">{formatMoney(listing.price_per_night)}</span> night ·{" "}
                    {listing.images.length} {listing.images.length === 1 ? "photo" : "photos"}
                  </p>
                  <Rating average={listing.average_rating} count={listing.review_count} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function HostActions({ booking }: { booking: Booking }) {
  const queryClient = useQueryClient();
  const act = useMutation({
    mutationFn: (action: "confirm" | "cancel") =>
      api<Booking>(`/api/bookings/${booking.id}/${action}/`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bookings"] }),
  });
  const canCancel = booking.check_in > today();

  return (
    <>
      {act.isError && <Notice tone="error">{act.error.message}</Notice>}
      {booking.status === "pending" && (
        <button type="button" className="btn btn--primary btn--sm" onClick={() => act.mutate("confirm")} disabled={act.isPending}>
          Confirm booking
        </button>
      )}
      {canCancel && (
        <button
          type="button"
          className="btn btn--danger btn--sm"
          disabled={act.isPending}
          onClick={() => {
            const refund = booking.status === "confirmed" ? " The guest will be refunded in full." : "";
            if (window.confirm(`Cancel this booking?${refund}`)) act.mutate("cancel");
          }}
        >
          {booking.status === "pending" ? "Decline" : "Cancel booking"}
        </button>
      )}
    </>
  );
}

// --- Create / edit ----------------------------------------------------------------

const EMPTY: ListingInput = {
  title: "",
  description: "",
  address: "",
  city: "",
  country: "",
  price_per_night: "",
  max_guests: 2,
};

export function ListingFormPage() {
  const { user } = useAuth();
  const { id } = useParams();
  const isNew = id === "new";
  const listing = useListing(isNew ? NaN : Number(id));

  if (user?.role !== "host") return <NotAHost />;
  if (!isNew && listing.isPending) return <Spinner />;
  if (!isNew && (listing.isError || listing.data?.host.id !== user.id)) {
    return (
      <div className="page page--narrow">
        <EmptyState title="Listing not found" action={<Link to="/hosting" className="btn btn--primary">Back to hosting</Link>} />
      </div>
    );
  }
  if (user.is_demo) {
    return (
      <div className="page page--narrow">
        <EmptyState
          title="Editing is off for the demo host"
          action={
            <Link to="/register" className="btn btn--primary">
              Create a host account
            </Link>
          }
        >
          The demo accounts are shared, so listings stay the same for everyone. Create your own host account to try
          listing a place and uploading photos.
        </EmptyState>
      </div>
    );
  }
  // Keyed so the form resets when switching from "new" to the created listing.
  return <ListingForm key={id} listing={isNew ? undefined : listing.data} />;
}

function ListingForm({ listing }: { listing?: Listing }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ListingInput>(() =>
    listing
      ? {
          title: listing.title,
          description: listing.description,
          address: listing.address,
          city: listing.city,
          country: listing.country,
          price_per_night: listing.price_per_night,
          max_guests: listing.max_guests,
        }
      : EMPTY,
  );
  const [saved, setSaved] = useState(false);

  const save = useMutation({
    mutationFn: () =>
      listing
        ? api<Listing>(`/api/properties/${listing.id}/`, { method: "PATCH", body: { ...form } })
        : api<Listing>("/api/properties/", { method: "POST", body: { ...form } }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.setQueryData(["listing", result.id], result);
      if (listing) setSaved(true);
      else navigate(`/hosting/listings/${result.id}?created=1`, { replace: true });
    },
  });

  const remove = useMutation({
    mutationFn: () => api(`/api/properties/${listing!.id}/`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      navigate("/hosting", { replace: true });
    },
  });

  const errors = fieldErrors(save.error);
  const set = <K extends keyof ListingInput>(key: K, value: ListingInput[K]) => {
    setSaved(false);
    setForm((f) => ({ ...f, [key]: value }));
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    save.mutate();
  };

  const justCreated = new URLSearchParams(window.location.search).has("created");

  return (
    <div className="page page--narrow">
      <Link to="/hosting" className="back-link">
        ← Hosting
      </Link>
      <header className="page-head">
        <h1 className="page-title">{listing ? "Edit listing" : "List a new place"}</h1>
        {listing && (
          <Link to={`/stays/${listing.id}`} className="small">
            View as a guest →
          </Link>
        )}
      </header>

      {justCreated && listing && <Notice tone="success">Listing published. Add a few photos so guests can see the place.</Notice>}

      <form className="form-card" onSubmit={submit} noValidate>
        <Field label="Title" htmlFor="l-title" error={errors.title} hint="What makes it distinct, e.g. “Tiled flat above the tram line”.">
          <input id="l-title" value={form.title} onChange={(e) => set("title", e.target.value)} maxLength={200} />
        </Field>
        <Field label="Description" htmlFor="l-desc" error={errors.description} hint="The space, the neighbourhood, and anything guests should know before booking.">
          <textarea id="l-desc" rows={6} value={form.description} onChange={(e) => set("description", e.target.value)} />
        </Field>
        <Field label="Street address" htmlFor="l-address" error={errors.address}>
          <input id="l-address" autoComplete="street-address" value={form.address} onChange={(e) => set("address", e.target.value)} />
        </Field>
        <div className="field-row">
          <Field label="City" htmlFor="l-city" error={errors.city}>
            <input id="l-city" autoComplete="address-level2" value={form.city} onChange={(e) => set("city", e.target.value)} />
          </Field>
          <Field label="Country" htmlFor="l-country" error={errors.country}>
            <input id="l-country" autoComplete="country-name" value={form.country} onChange={(e) => set("country", e.target.value)} />
          </Field>
        </div>
        <div className="field-row">
          <Field label="Price per night (USD)" htmlFor="l-price" error={errors.price_per_night}>
            <input
              id="l-price"
              type="number"
              inputMode="decimal"
              min={1}
              step="0.01"
              value={form.price_per_night}
              onChange={(e) => set("price_per_night", e.target.value)}
            />
          </Field>
          <Field label="Maximum guests" htmlFor="l-guests" error={errors.max_guests}>
            <input
              id="l-guests"
              type="number"
              min={1}
              max={50}
              value={form.max_guests}
              onChange={(e) => set("max_guests", Number(e.target.value))}
            />
          </Field>
        </div>

        {/* Errors tied to a field show under that field; anything else (e.g. "detail") shows here. */}
        {save.isError && !Object.keys(errors).some((key) => key in form) && (
          <Notice tone="error">{save.error.message}</Notice>
        )}
        {saved && <Notice tone="success">Changes saved.</Notice>}

        <div className="form-actions">
          <button type="submit" className="btn btn--primary" disabled={save.isPending}>
            {save.isPending ? "Saving…" : listing ? "Save changes" : "Publish listing"}
          </button>
        </div>
      </form>

      {listing && <PhotoManager listing={listing} />}

      {listing && (
        <section className="danger-zone">
          <h2 className="section-title section-title--sm">Delete listing</h2>
          <p className="muted small">This removes the listing and all of its bookings and reviews. It can't be undone.</p>
          {remove.isError && <Notice tone="error">{remove.error.message}</Notice>}
          <button
            type="button"
            className="btn btn--danger"
            disabled={remove.isPending}
            onClick={() => window.confirm(`Delete “${listing.title}”? This can't be undone.`) && remove.mutate()}
          >
            {remove.isPending ? "Deleting…" : "Delete listing"}
          </button>
        </section>
      )}
    </div>
  );
}

function PhotoManager({ listing }: { listing: Listing }) {
  const queryClient = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["listing", listing.id] });
    queryClient.invalidateQueries({ queryKey: ["listings"] });
  };

  const upload = useMutation({
    mutationFn: async (files: File[]) => {
      for (const file of files) {
        const body = new FormData();
        body.append("image", file);
        await api(`/api/properties/${listing.id}/images/`, { method: "POST", body });
      }
    },
    onSettled: refresh,
  });

  const remove = useMutation({
    mutationFn: (imageId: number) => api(`/api/properties/${listing.id}/images/${imageId}/`, { method: "DELETE" }),
    onSettled: refresh,
  });

  const addFiles = (list: FileList | null) => {
    const files = Array.from(list ?? []).filter((f) => f.type.startsWith("image/"));
    if (files.length) upload.mutate(files);
  };

  return (
    <section className="photos" aria-labelledby="photos-title">
      <h2 id="photos-title" className="section-title section-title--sm">
        Photos
      </h2>
      <p className="muted small">The first photo is the cover. JPEG or PNG, up to 5 MB each.</p>

      <div className="photo-grid">
        {listing.images.map((image, i) => (
          <figure key={image.id} className="photo">
            <img src={image.image} alt={image.caption || `Photo ${i + 1}`} />
            {i === 0 && <span className="photo-badge">Cover</span>}
            <button
              type="button"
              className="photo-remove"
              onClick={() => remove.mutate(image.id)}
              disabled={remove.isPending}
              aria-label={`Remove photo ${i + 1}`}
            >
              Remove
            </button>
          </figure>
        ))}

        <button
          type="button"
          className={`dropzone${dragging ? " is-dragging" : ""}`}
          onClick={() => input.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            addFiles(e.dataTransfer.files);
          }}
          disabled={upload.isPending}
        >
          <span className="dropzone-plus" aria-hidden="true">+</span>
          {upload.isPending ? "Uploading…" : "Add photos"}
          <span className="small muted">or drop them here</span>
        </button>
        <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden onChange={(e) => addFiles(e.target.files)} />
      </div>
      {upload.isError && <Notice tone="error">{upload.error.message}</Notice>}
      {remove.isError && <Notice tone="error">{remove.error.message}</Notice>}
    </section>
  );
}
