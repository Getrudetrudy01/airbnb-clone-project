import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useDemoAvailable } from "../api/queries";
import { useAuth } from "../auth/AuthContext";
import { Notice } from "./ui";

type DemoRole = "guest" | "host";

/** One-click login as the shared demo guest or host. Hidden when the site has no demo data. */
export function DemoLogin({ next = "/" }: { next?: string }) {
  const available = useDemoAvailable();
  const { logInAsDemo } = useAuth();
  const navigate = useNavigate();
  const [pending, setPending] = useState<DemoRole>();
  const [error, setError] = useState<string>();

  if (!available.data) return null;

  const go = async (role: DemoRole) => {
    setPending(role);
    setError(undefined);
    try {
      await logInAsDemo(role);
      // Without a page to return to, show where the demo has the most to see.
      navigate(role === "host" ? "/hosting" : next !== "/" ? next : "/trips", { replace: true });
    } catch (err) {
      setError((err as Error).message);
      setPending(undefined);
    }
  };

  return (
    <section className="demo-login" aria-labelledby="demo-login-title">
      <h2 id="demo-login-title" className="demo-login-title">
        Just looking around?
      </h2>
      <p className="muted small">Explore with a ready-made account. No sign-up needed.</p>
      {error && <Notice tone="error">{error}</Notice>}
      <div className="demo-login-buttons">
        <button type="button" className="btn btn--ghost" onClick={() => go("guest")} disabled={Boolean(pending)}>
          {pending === "guest" ? "Opening…" : "Explore as a guest"}
        </button>
        <button type="button" className="btn btn--ghost" onClick={() => go("host")} disabled={Boolean(pending)}>
          {pending === "host" ? "Opening…" : "Explore as a host"}
        </button>
      </div>
    </section>
  );
}

/** A one-line prompt on the home page for first-time visitors. */
export function DemoHint() {
  const available = useDemoAvailable();
  const { status, logInAsDemo } = useAuth();
  const navigate = useNavigate();
  const [pending, setPending] = useState(false);

  if (!available.data || status !== "signed-out") return null;

  const go = async () => {
    setPending(true);
    try {
      await logInAsDemo("guest");
      navigate("/trips");
    } catch {
      setPending(false);
    }
  };

  return (
    <p className="demo-hint">
      New here?{" "}
      <button type="button" className="link-button" disabled={pending} onClick={go}>
        {pending ? "Opening the demo…" : "Explore as a demo guest"}
      </button>{" "}
      <span className="muted">to see trips, bookings and reviews.</span>
    </p>
  );
}
