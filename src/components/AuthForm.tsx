import { useState, type FormEvent } from "react";
import { ArrowRight, GraduationCap } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { authenticate, DEMO_MODE } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const register = mode === "register";

  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const data = await authenticate(mode, {
        email: String(form.get("email")),
        password: String(form.get("password")),
        ...(register ? { name: String(form.get("name")) } : {}),
      });
      signIn(data);
      navigate("/student");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось войти.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page container">
      <div className="auth-story">
        <GraduationCap size={44} />
        <h1>
          Большие открытия
          <br />
          начинаются здесь.
        </h1>
        <p>
          Твой преподаватель.
          <br />
          Твой темп.
          <br />
          Твоё пространство для роста.
        </p>
        <div className="auth-formula">a² + b² = c²</div>
      </div>
      <section className="panel auth-panel">
        <span className="eyebrow">ДОБРО ПОЖАЛОВАТЬ В TAALIMSPACE</span>
        <h2>{register ? "Создать аккаунт" : "Рады видеть снова"}</h2>
        <p>
          {register
            ? "Начните учиться. Преподавание можно подключить позже."
            : "Войди, чтобы продолжить обучение."}
        </p>
        {DEMO_MODE && (
          <div className="notice">
            Регистрация создаёт настоящий аккаунт. Демо-кабинет доступен
            отдельно, без регистрации.
          </div>
        )}
        <form onSubmit={submit}>
          <fieldset disabled={busy}>
            {register && (
              <>
                <label>
                  Имя
                  <input
                    name="name"
                    required
                    minLength={2}
                    maxLength={100}
                    autoComplete="name"
                    placeholder="Как к вам обращаться?"
                  />
                </label>
              </>
            )}
            <label>
              Email
              <input
                name="email"
                type="email"
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
            </label>
            <label>
              Пароль
              <input
                name="password"
                type="password"
                required
                minLength={10}
                maxLength={128}
                autoComplete={register ? "new-password" : "current-password"}
                placeholder={register ? "Не менее 10 символов" : "Ваш пароль"}
              />
            </label>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <button className="button full" type="submit">
              {busy ? "Подождите…" : register ? "Создать аккаунт" : "Войти"}
              <ArrowRight size={17} />
            </button>
          </fieldset>
        </form>
        {DEMO_MODE && (
          <Link to="/student" className="button outline full">
            Открыть демо-кабинет
          </Link>
        )}
        {!register && <Link to="/forgot-password">Забыли пароль?</Link>}
        <p className="auth-switch">
          {register ? "Уже есть аккаунт?" : "Первый раз здесь?"}{" "}
          <Link to={register ? "/login" : "/register"}>
            {register ? "Войти" : "Зарегистрироваться"}
          </Link>
        </p>
      </section>
    </div>
  );
}
