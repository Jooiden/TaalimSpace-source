import { useTimeZone } from "../../lib/useTimeZone";
import { useEffect, useState } from "react";
import HomeworkEditor from "./HomeworkEditor";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
type Homework = {
  due_date: string | null;
  id: number;
  lesson_id: number;
  student_name: string;
  subject: string;
  source: string;
  tasks: { task: string; hint: string }[];
  status: string;
  student_answer: string | null;
  teacher_feedback: string | null;
};
export default function HomeworkPanel({
  teacher = false,
}: {
  teacher?: boolean;
}) {
  const { formatDate } = useTimeZone();
  const { token } = useAuth();
  const [items, setItems] = useState<Homework[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  async function load() {
    setLoading(true);
    try {
      setItems(
        await api<Homework[]>(
          `/homework?mode=${teacher ? "teacher" : "student"}`,
          {},
          token,
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, [token, teacher]);
  async function send(item: Homework) {
    setBusy(true);
    setError("");
    try {
      await api(
        `/homework/${item.id}/${teacher ? "feedback" : "submit"}`,
        {
          method: "POST",
          body: JSON.stringify(
            teacher
              ? { feedback: drafts[item.id] }
              : { answer: drafts[item.id] },
          ),
        },
        token,
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section id="practice" className="panel spaced">
      <h2>{teacher ? "Работы учеников" : "Задания и проверка"}</h2>
      {error && <p role="alert">{error}</p>}
      {loading && <p role="status">Загружаем задания…</p>}
      {!loading && !error && !items.length && (
        <p>
          Пока нет домашних заданий. Здесь появятся задания преподавателя и
          практика после разбора урока.
        </p>
      )}
      {items.map((item) => (
        <article key={item.id} className="spaced">
          <h3>
            {item.subject} · урок №{item.lesson_id}
          </h3>
          <p>
            {item.student_name} ·{" "}
            {item.source === "teacher" ? "Задано учителем" : "Практика ИИ"} ·{" "}
            {{
              new: "Новое",
              submitted: "Ожидает учителя",
              checked: "Проверено",
            }[item.status] ?? item.status}
          </p>
          {item.due_date && <p>Срок: {formatDate(item.due_date)}</p>}
          {teacher && !["submitted", "checked"].includes(item.status) && (
            <HomeworkEditor
              id={item.id}
              lessonId={item.lesson_id}
              tasks={item.tasks}
              dueDate={item.due_date}
              onSaved={() => void load()}
            />
          )}
          <ul>
            {item.tasks.map((task, i) => (
              <li key={i}>{task.task}</li>
            ))}
          </ul>
          {item.student_answer && (
            <p>
              <strong>Ответ ученика:</strong> {item.student_answer}
            </p>
          )}
          {item.teacher_feedback && (
            <p>
              <strong>Комментарий учителя:</strong> {item.teacher_feedback}
            </p>
          )}
          {(teacher ? !!item.student_answer : item.status !== "checked") && (
            <div className="learning-form">
              <label>
                {teacher ? "Обратная связь ученику" : "Ваш ответ"}
                <textarea
                  maxLength={10000}
                  value={drafts[item.id] ?? ""}
                  onChange={(e) =>
                    setDrafts({ ...drafts, [item.id]: e.target.value })
                  }
                />
              </label>
              <button
                className="button small"
                disabled={busy || !drafts[item.id]?.trim()}
                onClick={() => void send(item)}
              >
                {teacher ? "Сохранить проверку" : "Отправить учителю"}
              </button>
            </div>
          )}
        </article>
      ))}
    </section>
  );
}
