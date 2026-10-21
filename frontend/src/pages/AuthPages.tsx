import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { ApiError, fieldErrors } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Field, Notice } from "../components/ui";

/** Only follow same-site paths after login, never an arbitrary URL. */
function safeNext(value: string | null) {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : "/";
}

export function LoginPage() {
  const { logIn } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError(undefined);
    try {
      await logIn(email, password);
      navigate(safeNext(params.get("next")), { replace: true });
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? "That email and password don't match an account."
          : (err as Error).message,
      );
      setPending(false);
    }
  };

  return (
    <div className="auth">
      <form className="auth-card" onSubmit={submit} noValidate>
        <h1 className="page-title page-title--sm">Log in</h1>
        <p className="muted">Pick up where you left off with your trips and listings.</p>
        {error && <Notice tone="error">{error}</Notice>}
        <Field label="Email" htmlFor="login-email">
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Password" htmlFor="login-password">
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <button type="submit" className="btn btn--primary btn--block" disabled={pending || !email || !password}>
          {pending ? "Logging in…" : "Log in"}
        </button>
        <p className="auth-switch">
          New to Keyhouse? <Link to={`/register${params.size ? `?${params}` : ""}`}>Create an account</Link>
        </p>
      </form>
    </div>
  );
}

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    role: "guest" as "guest" | "host",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  const set = (key: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setErrors({});
    setError(undefined);
    try {
      const user = await register(form);
      navigate(user.role === "host" ? "/hosting" : safeNext(params.get("next")), { replace: true });
    } catch (err) {
      const byField = fieldErrors(err);
      setErrors(byField);
      if (!Object.keys(byField).some((k) => k in form)) setError((err as Error).message);
      setPending(false);
    }
  };

  return (
    <div className="auth">
      <form className="auth-card auth-card--wide" onSubmit={submit} noValidate>
        <h1 className="page-title page-title--sm">Create an account</h1>
        {error && <Notice tone="error">{error}</Notice>}

        <fieldset className="role-picker">
          <legend>How will you use Keyhouse?</legend>
          {(
            [
              ["guest", "Book stays", "Find places to stay and keep track of your trips."],
              ["host", "Host a place", "List your home, take bookings and get paid."],
            ] as const
          ).map(([value, title, text]) => (
            <label key={value} className={`role-option${form.role === value ? " is-selected" : ""}`}>
              <input
                type="radio"
                name="role"
                value={value}
                checked={form.role === value}
                onChange={() => set("role")(value)}
              />
              <span className="role-title">{title}</span>
              <span className="role-text">{text}</span>
            </label>
          ))}
        </fieldset>

        <div className="field-row">
          <Field label="First name" htmlFor="reg-first" error={errors.first_name}>
            <input id="reg-first" autoComplete="given-name" value={form.first_name} onChange={(e) => set("first_name")(e.target.value)} />
          </Field>
          <Field label="Last name" htmlFor="reg-last" error={errors.last_name}>
            <input id="reg-last" autoComplete="family-name" value={form.last_name} onChange={(e) => set("last_name")(e.target.value)} />
          </Field>
        </div>
        <Field label="Email" htmlFor="reg-email" error={errors.email}>
          <input
            id="reg-email"
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={(e) => set("email")(e.target.value)}
            aria-invalid={Boolean(errors.email)}
          />
        </Field>
        <Field
          label="Password"
          htmlFor="reg-password"
          error={errors.password}
          hint="At least 8 characters. Avoid common words and all-number passwords."
        >
          <input
            id="reg-password"
            type="password"
            autoComplete="new-password"
            required
            value={form.password}
            onChange={(e) => set("password")(e.target.value)}
            aria-invalid={Boolean(errors.password)}
          />
        </Field>
        <p className="muted small">Other people see only your first name and last initial, never your email.</p>
        <button type="submit" className="btn btn--primary btn--block" disabled={pending || !form.email || !form.password}>
          {pending ? "Creating account…" : "Create account"}
        </button>
        <p className="auth-switch">
          Already have an account? <Link to={`/login${params.size ? `?${params}` : ""}`}>Log in</Link>
        </p>
      </form>
    </div>
  );
}
