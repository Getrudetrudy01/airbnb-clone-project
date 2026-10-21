import type { Listing } from "../api/types";

// Postcard colourways for listings without photos. Picked by id so a listing keeps its colour.
const COLOURWAYS = ["pine", "amber", "ink", "sage", "brick"] as const;

interface ListingCoverProps {
  listing: Pick<Listing, "id" | "city" | "country" | "title" | "images">;
  size?: "card" | "hero";
}

export function ListingCover({ listing, size = "card" }: ListingCoverProps) {
  const photo = listing.images[0];
  if (photo) {
    return (
      <div className={`cover cover--${size}`}>
        <img src={photo.image} alt={photo.caption || listing.title} loading="lazy" />
      </div>
    );
  }

  const colourway = COLOURWAYS[listing.id % COLOURWAYS.length];
  return (
    <div className={`cover cover--${size} cover--postcard cover--${colourway}`} role="img" aria-label={listing.title}>
      <svg className="cover-postmark" viewBox="0 0 120 120" aria-hidden="true">
        <circle cx="60" cy="60" r="44" />
        <circle cx="60" cy="60" r="34" />
        <path d="M-40 24 q 15 -10 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0" />
        <path d="M-40 40 q 15 -10 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0" />
        <path d="M-40 56 q 15 -10 30 0 t 30 0 t 30 0 t 30 0 t 30 0 t 30 0" />
      </svg>
      <span className="cover-country">{listing.country}</span>
      <span className="cover-city">{listing.city}</span>
    </div>
  );
}
