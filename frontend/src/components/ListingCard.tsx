import { Link } from "react-router-dom";

import type { Listing } from "../api/types";
import { formatMoney } from "../lib/format";
import { ListingCover } from "./ListingCover";
import { Rating } from "./Rating";

export function ListingCard({ listing, search = "" }: { listing: Listing; search?: string }) {
  return (
    <article className="card">
      <Link to={`/stays/${listing.id}${search}`} className="card-link">
        <ListingCover listing={listing} />
        <div className="card-body">
          <div className="card-topline">
            <span className="card-place">
              {listing.city}, {listing.country}
            </span>
            <Rating average={listing.average_rating} count={listing.review_count} compact />
          </div>
          <h3 className="card-title">{listing.title}</h3>
          <p className="card-meta">
            <span className="mono">{formatMoney(listing.price_per_night)}</span> night
            <span className="dot" aria-hidden="true">·</span>
            Up to {listing.max_guests} {listing.max_guests === 1 ? "guest" : "guests"}
          </p>
        </div>
      </Link>
    </article>
  );
}

export function ListingCardSkeleton() {
  return (
    <div className="card card--skeleton" aria-hidden="true">
      <div className="cover cover--card skeleton" />
      <div className="card-body">
        <div className="skeleton skeleton-line" style={{ width: "45%" }} />
        <div className="skeleton skeleton-line skeleton-line--lg" style={{ width: "80%" }} />
        <div className="skeleton skeleton-line" style={{ width: "55%" }} />
      </div>
    </div>
  );
}
