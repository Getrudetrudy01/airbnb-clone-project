import { useMutation } from "@tanstack/react-query";

import { api, ApiError } from "../api/client";

/** Starts Stripe Checkout for a booking and sends the browser there. */
export function usePayForBooking() {
  return useMutation({
    mutationFn: (bookingId: number) =>
      api<{ checkout_url: string }>("/api/payments/checkout/", { method: "POST", body: { booking: bookingId } }),
    onSuccess: ({ checkout_url }) => window.location.assign(checkout_url),
  });
}

export function paymentErrorMessage(error: unknown) {
  if (error instanceof ApiError && error.status === 503) {
    return "Online payment isn't set up on this server yet. Your booking stays reserved, and your host can confirm it.";
  }
  return error instanceof Error ? error.message : "Payment couldn't start. Try again.";
}
