import { useTimeZone } from "../../lib/useTimeZone";
import { useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
type Slot = {
  id: number;
  start_time: string;
  duration_min: number;
  service_title: string;
  price: number;
};
export default function LessonActions({
  id,
  onChange,
}: {
  id: number;
  onChange: () => void;
}) {
  const { formatDate } = useTimeZone();
  const { token } = useAuth();
  const [slots, setSlots] = useState<Slot[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  async function run(path: string, body?: object) {
    setBusy(true);
    try {
      await api(
        path,
        { method: "POST", body: body ? JSON.stringify(body) : undefined },
        token,
      );
      onChange();
      setOpen(false);
      setMessage("Изменения сохранены.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  async function load() {
    try {
      setSlots(await api(`/lessons/${id}/available-slots`, {}, token));
      setOpen(true);
    } catch (e) {
      setMessage(String(e));
    }
  }
  return (
    <div className="spaced">
      <button
        className="button outline small"
        disabled={busy}
        onClick={() => void load()}
      >
        Перенести
      </button>{" "}
      <button
        className="button outline small"
        disabled={busy}
        onClick={() => {
          if (
            confirm("Отменить занятие? Время снова станет доступно для записи.")
          )
            void run(`/lessons/${id}/cancel`);
        }}
      >
        Отменить занятие
      </button>
      {open && (
        <div>
          <p>Выберите ту же услугу и длительность. Цена брони сохраняется.</p>
          {!slots.length && <p>Нет свободного времени.</p>}
          {slots.map((s) => (
            <button
              key={s.id}
              disabled={busy}
              className="button outline small"
              onClick={() =>
                void run(`/lessons/${id}/reschedule`, { slot_id: s.id })
              }
            >
              {s.service_title} · {formatDate(s.start_time)} · {s.duration_min}{" "}
              мин · {s.price} сом
            </button>
          ))}
        </div>
      )}
      <p role="status">{message}</p>
    </div>
  );
}
