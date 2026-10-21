import { useEffect } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";

import { Header } from "./components/Header";
import { EmptyState, RequireAuth } from "./components/ui";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { HomePage } from "./pages/HomePage";
import { HostingPage, ListingFormPage } from "./pages/HostingPages";
import { ListingPage } from "./pages/ListingPage";
import { BookingPage, TripsPage } from "./pages/TripsPage";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <ScrollToTop />
      <Header />
      <main id="main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/stays/:id" element={<ListingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/trips" element={<RequireAuth><TripsPage /></RequireAuth>} />
          <Route path="/bookings/:id" element={<RequireAuth><BookingPage /></RequireAuth>} />
          <Route path="/hosting" element={<RequireAuth><HostingPage /></RequireAuth>} />
          <Route path="/hosting/listings/:id" element={<RequireAuth><ListingFormPage /></RequireAuth>} />
          <Route
            path="*"
            element={
              <div className="page page--narrow">
                <EmptyState title="This page doesn't exist" action={<Link to="/" className="btn btn--primary">Browse stays</Link>}>
                  Check the address, or start again from the stays list.
                </EmptyState>
              </div>
            }
          />
        </Routes>
      </main>
      <footer className="site-footer">
        <p>Keyhouse · a learning project built with Django and React.</p>
      </footer>
    </>
  );
}
