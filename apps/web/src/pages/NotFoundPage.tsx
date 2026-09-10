import { Link } from "react-router-dom";

type Props = {
  title?: string;
  message?: string;
  homeTo?: string;
};

/** Unknown route — never a blank screen. */
export function NotFoundPage({
  title = "Page not found",
  message = "This link is not part of CFS Designers. Check the URL or go back home.",
  homeTo = "/",
}: Props) {
  return (
    <div className="not-found-page">
      <div className="card not-found-card is-error" role="alert">
        <div className="not-found-icon" aria-hidden>
          !
        </div>
        <p className="not-found-kicker">Error 404</p>
        <h1>{title}</h1>
        <p className="not-found-msg">{message}</p>
        <div className="not-found-actions">
          <Link className="btn-danger" to={homeTo}>
            Go to Dashboard
          </Link>
          <Link className="secondary" to="/login">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

export function AccessDeniedPage({
  title = "Access denied",
  message = "Your role cannot open this page. Payments and partner shares are for finance / partners only.",
}: Props) {
  return (
    <div className="not-found-page">
      <div className="card not-found-card is-error" role="alert">
        <div className="not-found-icon" aria-hidden>
          !
        </div>
        <p className="not-found-kicker">Error 403</p>
        <h1>{title}</h1>
        <p className="not-found-msg">{message}</p>
        <div className="not-found-actions">
          <Link className="btn-danger" to="/">
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
