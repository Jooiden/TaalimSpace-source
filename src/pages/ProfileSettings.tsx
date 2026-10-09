import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import DashboardLayout from "../components/layout/DashboardLayout";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { useTimeZone } from "../lib/useTimeZone";
import type { User } from "../types";
const commonZones: Record<string, string> = {
  "Asia/Bishkek": "Бишкек",
  "Asia/Almaty": "Алматы / Астана",
  "Asia/Tashkent": "Ташкент",
  "Europe/Moscow": "Москва",
  "Europe/London": "Лондон",
  UTC: "UTC",
};
export default function ProfileSettings() {
  const { user, token, updateUser } = useAuth();
  const { timeZone } = useTimeZone();
  const [zone, setZone] = useState(timeZone);
  const [birth, setBirth] = useState(user?.birth_date || "");
  const [zones, setZones] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (token)
      api<string[]>("/profile/time-zones", {}, token)
        .then(setZones)
        .catch(() => setMessage("Не удалось загрузить список часовых поясов."));
  }, [token]);
  useEffect(() => {
    setZone(timeZone);
    setBirth(user?.birth_date || "");
  }, [timeZone, user?.birth_date]);
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      updateUser(
        await api<User>(
          "/profile",
          {
            method: "PATCH",
            body: JSON.stringify({
              birth_date: birth || null,
              time_zone: zone,
            }),
          },
          token,
        ),
      );
      setMessage("Настройки сохранены.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setBusy(false);
    }
  }
  return (
    <DashboardLayout teacher={user?.role === "teacher"}>
      <h1>Настройки профиля</h1>
      {!user ? (
        <p>
          <Link to="/login">Войдите</Link>, чтобы сохранить личные настройки.
        </p>
      ) : (
        <form className="panel spaced learning-form" onSubmit={save}>
          <p>
            {user.name} · {user.email}
          </p>
          <label>
            Дата рождения — необязательно
            <input
              type="date"
              value={birth}
              onChange={(e) => setBirth(e.target.value)}
              disabled={busy}
            />
          </label>
          <p className="fine-print">
            Видна только вам. Можно оставить пустой или удалить сохранённую
            дату.
          </p>
          <label>
            Часовой пояс
            <select
              required
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              disabled={busy}
            >
              {[...new Set([zone, ...Object.keys(commonZones), ...zones])]
                .filter((z) => {
                  try {
                    new Intl.DateTimeFormat("ru", { timeZone: z });
                    return true;
                  } catch {
                    return false;
                  }
                })
                .map((z) => (
                  <option key={z} value={z}>
                    {commonZones[z]
                      ? `${commonZones[z]} (${z})`
                      : z.replaceAll("_", " ")}
                  </option>
                ))}
            </select>
          </label>
          <p>
            Время занятий и сроки заданий отображаются в выбранном часовом
            поясе.
          </p>
          <button
            type="button"
            className="button outline small"
            onClick={() =>
              setZone(Intl.DateTimeFormat().resolvedOptions().timeZone)
            }
          >
            Определить по устройству
          </button>
          <button className="button" disabled={busy}>
            {busy ? "Сохраняем…" : "Сохранить настройки"}
          </button>
          {message && <p role="status">{message}</p>}
        </form>
      )}
    </DashboardLayout>
  );
}
