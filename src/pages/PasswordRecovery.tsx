import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
export default function PasswordRecovery({
  reset = false,
}: {
  reset?: boolean;
}) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [complete, setComplete] = useState(false);
  const [resetToken] = useState(() => window.location.hash.slice(1));
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setMessage("");
    setError("");
    if (reset && f.get("password") !== f.get("confirmation")) {
      setError("Пароли не совпадают.");
      return;
    }
    setBusy(true);
    try {
      const r = await api<{ message: string }>(
        reset ? "/auth/reset-password" : "/auth/forgot-password",
        {
          method: "POST",
          body: JSON.stringify(
            reset
              ? { token: resetToken, password: f.get("password") }
              : { email: f.get("email") },
          ),
        },
      );
      setMessage(r.message);
      if (reset) {
        setComplete(true);
        history.replaceState(null, "", window.location.pathname);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="container page-section">
      <section className="panel">
        <h1>{reset ? "Новый пароль" : "Восстановление пароля"}</h1>
        {reset && !resetToken && (
          <p role="alert">
            Откройте полную ссылку из письма или запросите новую.
          </p>
        )}
        {!complete && (!reset || resetToken) && (
          <form className="learning-form" onSubmit={submit}>
            {reset ? (
              <>
                <label>
                  Новый пароль
                  <input
                    name="password"
                    type="password"
                    minLength={10}
                    maxLength={128}
                    required
                    autoComplete="new-password"
                  />
                </label>
                <label>
                  Повторите пароль
                  <input
                    name="confirmation"
                    type="password"
                    minLength={10}
                    maxLength={128}
                    required
                    autoComplete="new-password"
                  />
                </label>
                <p>
                  Не менее 10 символов. Ссылка действует 30 минут и используется
                  один раз.
                </p>
              </>
            ) : (
              <label>
                Почта аккаунта
                <input
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                />
              </label>
            )}
            <button className="button" disabled={busy}>
              {busy
                ? "Подождите…"
                : reset
                  ? "Сохранить пароль"
                  : "Отправить ссылку"}
            </button>
          </form>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <p role="status">{message}</p>
        <Link to="/login">Вернуться ко входу</Link>
      </section>
    </div>
  );
}
