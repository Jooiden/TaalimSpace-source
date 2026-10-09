import PushSettings from "../components/PushSettings";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
type Item = { id: number; text: string; link: string; read: boolean };
export default function Notifications() {
  const { token } = useAuth();
  const [items, setItems] = useState<Item[]>([]);
  const [error, setError] = useState("");
  const [email, setEmail] = useState(false);
  const [configured, setConfigured] = useState(false);
  async function load() {
    try {
      setItems(await api("/notifications", {}, token));
      const p = await api<{
        email_reminders: boolean;
        email_configured: boolean;
      }>("/notifications/preferences", {}, token);
      setEmail(p.email_reminders);
      setConfigured(p.email_configured);
    } catch (e) {
      setError(String(e));
    }
  }
  useEffect(() => {
    if (token) void load();
  }, [token]);
  return (
    <div className="container page-section">
      <h1>Уведомления</h1>
      {!token ? (
        <Link to="/login">Войти</Link>
      ) : (
        <>
          <PushSettings />
          <label>
            <input
              type="checkbox"
              checked={email}
              disabled={!configured}
              onChange={async (e) => {
                try {
                  await api(
                    "/notifications/preferences",
                    {
                      method: "POST",
                      body: JSON.stringify({
                        email_reminders: e.target.checked,
                      }),
                    },
                    token,
                  );
                  await load();
                } catch (e) {
                  setError(String(e));
                }
              }}
            />
            Напоминания по почте
          </label>
          {!configured && (
            <p>Почтовый сервис ещё не подключён. Напоминания доступны здесь.</p>
          )}
          {!items.length && <p>Ближайших напоминаний нет.</p>}
          {items.map((n) => (
            <article className="panel spaced" key={n.id}>
              <p>{n.text}</p>
              <Link to={n.link}>Открыть</Link>
              {!n.read && (
                <button
                  className="button outline small"
                  onClick={async () => {
                    await api(
                      `/notifications/${n.id}/read`,
                      { method: "POST" },
                      token,
                    );
                    await load();
                  }}
                >
                  Прочитано
                </button>
              )}
            </article>
          ))}
        </>
      )}
      <p role="alert">{error}</p>
    </div>
  );
}
