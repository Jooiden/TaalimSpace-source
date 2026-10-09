import { useTimeZone } from "../../lib/useTimeZone";
import { useState, type FormEvent } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
export default function HomeworkEditor({
  lessonId,
  id,
  tasks = [],
  dueDate,
  onSaved,
}: {
  lessonId: number;
  id?: number;
  tasks?: { task: string }[];
  dueDate?: string | null;
  onSaved?: () => void;
}) {
  const { toInput, fromInput } = useTimeZone();
  const { token } = useAuth();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    try {
      await api(
        "/homework" + (id ? `/${id}` : ""),
        {
          method: id ? "PATCH" : "POST",
          body: JSON.stringify({
            lesson_id: lessonId,
            tasks: String(f.get("tasks"))
              .split("\n")
              .map((t) => t.trim())
              .filter(Boolean)
              .map((task) => ({ task, hint: "" })),
            due_date: f.get("due") ? fromInput(String(f.get("due"))) : null,
          }),
        },
        token,
      );
      setMessage("Задание сохранено.");
      onSaved?.();
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="spaced">
      <summary>{id ? "Изменить задание" : "Задать домашнюю работу"}</summary>
      <form className="learning-form" onSubmit={save}>
        <label>
          Задания, каждое с новой строки
          <textarea
            name="tasks"
            required
            maxLength={20000}
            defaultValue={tasks.map((t) => t.task).join("\n")}
          />
        </label>
        <label>
          Сдать до (ваше местное время)
          <input
            name="due"
            type="datetime-local"
            defaultValue={dueDate ? toInput(dueDate) : ""}
          />
        </label>
        <button className="button small" disabled={busy}>
          Сохранить задание
        </button>
      </form>
      <p role="status">{message}</p>
    </details>
  );
}
