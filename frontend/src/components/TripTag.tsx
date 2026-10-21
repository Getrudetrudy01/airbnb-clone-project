import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import type { Booking } from "../api/types";
import { formatLongDate, formatMoney, plural } from "../lib/format";

const STATUS_LABEL: Record<Booking["status"], string> = {
  pending: "Awaiting payment",
  confirmed: "Confirmed",
  cancelled: "Cancelled",
};

interface TripTagProps {
  booking: Booking;
  /** Shown above the dates, e.g. the guest's email on the host's view. */
  eyebrow?: string;
  children?: ReactNode;
}

/** A booking as a luggage tag: the stub carries the nights, the body carries the details. */
export function TripTag({ booking, eyebrow, children }: TripTagProps) {
  return (
    <article className={`triptag triptag--${booking.status}`}>
      <div className="triptag-stub">
        <span className="triptag-eyelet" aria-hidden="true" />
        <span className="triptag-figure">{booking.nights}</span>
        <span className="triptag-figure-label">{booking.nights === 1 ? "night" : "nights"}</span>
      </div>

      <div className="triptag-body">
        <div className="triptag-head">
          <div>
            {eyebrow && <p className="triptag-eyebrow">{eyebrow}</p>}
            <h3 className="triptag-title">
              <Link to={`/stays/${booking.property}`}>{booking.property_title}</Link>
            </h3>
          </div>
          <span className={`status status--${booking.status}`}>{STATUS_LABEL[booking.status]}</span>
        </div>

        <dl className="triptag-facts">
          <div>
            <dt>Check-in</dt>
            <dd>{formatLongDate(booking.check_in)}</dd>
          </div>
          <div>
            <dt>Check-out</dt>
            <dd>{formatLongDate(booking.check_out)}</dd>
          </div>
          <div>
            <dt>Guests</dt>
            <dd>{plural(booking.guests, "guest")}</dd>
          </div>
          <div>
            <dt>Total</dt>
            <dd>{formatMoney(booking.total_price)}</dd>
          </div>
        </dl>

        {children && <div className="triptag-actions">{children}</div>}
      </div>
    </article>
  );
}
