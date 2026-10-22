import { keepPreviousData, useInfiniteQuery, useQuery } from "@tanstack/react-query";

import { api } from "./client";
import type { Booking, DateRange, Listing, Page, Review } from "./types";

export interface ListingFilters {
  city?: string;
  check_in?: string;
  check_out?: string;
  guests?: string;
  ordering?: string;
  host?: number;
}

export function useListings(filters: ListingFilters) {
  return useInfiniteQuery({
    queryKey: ["listings", filters],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      api<Page<Listing>>("/api/properties/", { params: { ...filters, page: pageParam } }),
    getNextPageParam: (last, pages) => (last.next ? pages.length + 1 : undefined),
    placeholderData: keepPreviousData,
  });
}

export function useHostListings(hostId: number | undefined) {
  return useQuery({
    queryKey: ["listings", "host", hostId],
    queryFn: () => api<Page<Listing>>("/api/properties/", { params: { host: hostId } }),
    enabled: hostId !== undefined,
  });
}

export function useListing(id: number) {
  return useQuery({
    queryKey: ["listing", id],
    queryFn: () => api<Listing>(`/api/properties/${id}/`),
    enabled: Number.isFinite(id),
  });
}

export function useBookedDates(id: number) {
  return useQuery({
    queryKey: ["listing", id, "booked-dates"],
    queryFn: () => api<DateRange[]>(`/api/properties/${id}/booked-dates/`),
  });
}

export function useReviews(params: { property?: number; author?: number }, enabled = true) {
  return useQuery({
    queryKey: ["reviews", params],
    queryFn: () => api<Page<Review>>("/api/reviews/", { params }),
    enabled,
  });
}

export function useDemoAvailable() {
  return useQuery({
    queryKey: ["demo-available"],
    queryFn: () => api<{ available: boolean }>("/api/auth/demo/"),
    staleTime: Infinity,
    select: (data) => data.available,
  });
}

export function useBookings(enabled = true) {
  return useQuery({
    queryKey: ["bookings"],
    queryFn: () => api<Page<Booking>>("/api/bookings/"),
    enabled,
  });
}

export function useBooking(id: number, poll = false) {
  return useQuery({
    queryKey: ["booking", id],
    queryFn: () => api<Booking>(`/api/bookings/${id}/`),
    // After returning from Stripe, the webhook may land a moment later.
    refetchInterval: (query) => (poll && query.state.data?.status === "pending" ? 2000 : false),
  });
}
