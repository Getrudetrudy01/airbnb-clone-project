export type Role = "guest" | "host" | "admin";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  /** One of the shared demo accounts: browsing and booking only. */
  is_demo: boolean;
  date_joined: string;
}

export interface PublicUser {
  id: number;
  name: string;
}

export interface ListingImage {
  id: number;
  image: string;
  caption: string;
  created_at: string;
}

export interface Listing {
  id: number;
  host: PublicUser;
  title: string;
  description: string;
  address: string;
  city: string;
  country: string;
  price_per_night: string;
  max_guests: number;
  images: ListingImage[];
  average_rating: number | null;
  review_count: number;
  created_at: string;
  updated_at: string;
}

export type ListingInput = Pick<
  Listing,
  "title" | "description" | "address" | "city" | "country" | "price_per_night" | "max_guests"
>;

export type BookingStatus = "pending" | "confirmed" | "cancelled";

export interface Booking {
  id: number;
  property: number;
  property_title: string;
  /** The guest's email; only ever visible to the guest and the host. */
  guest: string;
  check_in: string;
  check_out: string;
  nights: number;
  guests: number;
  total_price: string;
  status: BookingStatus;
  created_at: string;
}

export interface Review {
  id: number;
  booking: number;
  property: number;
  author: PublicUser;
  rating: number;
  comment: string;
  created_at: string;
}

export interface DateRange {
  check_in: string;
  check_out: string;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
