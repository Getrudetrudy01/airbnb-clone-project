import { Link, NavLink } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function Header() {
  const { user, status, logOut } = useAuth();

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link to="/" className="wordmark" aria-label="Keyhouse home">
          <svg viewBox="0 0 32 32" className="wordmark-mark" aria-hidden="true">
            <path d="M10 3h12l6 6v20a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V9z" />
            <circle cx="16" cy="9" r="3" />
          </svg>
          Keyhouse
        </Link>

        <nav className="site-nav" aria-label="Main">
          <NavLink to="/" end>
            Stays
          </NavLink>
          {status === "signed-in" && (
            <>
              <NavLink to="/trips">Trips</NavLink>
              {user?.role === "host" && <NavLink to="/hosting">Hosting</NavLink>}
            </>
          )}
        </nav>

        <div className="site-account">
          {status === "signed-in" && user ? (
            <>
              <span className="site-account-name">{user.first_name || user.email}</span>
              <button type="button" className="btn btn--ghost btn--sm" onClick={logOut}>
                Log out
              </button>
            </>
          ) : status === "signed-out" ? (
            <>
              <Link to="/login" className="btn btn--ghost btn--sm">
                Log in
              </Link>
              <Link to="/register" className="btn btn--primary btn--sm">
                Sign up
              </Link>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
