import { useTimeZone } from "../../lib/useTimeZone";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Lesson } from "../../types";
import TestPayment from "../booking/TestPayment";
import ProgressPanel from "../ProgressPanel";
import HomeworkEditor from "../lesson-card/HomeworkEditor";
import LessonActions from "../booking/LessonActions";
import TeacherServices from "../booking/TeacherServices";
type Item = Lesson & { status: string; student: string; reviewed: boolean };
export default function LiveDashboard({
  teacher = false,
  section = "overview",
}: {
  teacher?: boolean;
  section?: "overview" | "lessons";
}) {
  const { timeZone, formatDate, dateKey } = useTimeZone();
  const { token, user } = useAuth();
  const [lessons, setLessons] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [ratings, setRatings] = useState<Record<number, string>>({});
  const [reviews, setReviews] = useState<Record<number, string>>({});
  const [plan, setPlan] = useState<{
    lesson_id: number;
    blocks: { title: string; minutes: number }[];
    suggestions: string;
  }>();
  async function load() {
    setLoading(true);
    try {
      const result = await api<{ items: Item[] }>(
        `/lessons?mode=${teacher ? "teacher" : "student"}`,
        {},
        token,
      );
      setLessons(result.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, [token, teacher]);
  async function action(path: string, body?: object) {
    setBusy(true);
    setError("");
    try {
      await api(
        path,
        { method: "POST", ...(body ? { body: JSON.stringify(body) } : {}) },
        token,
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  async function prepare(id: number) {
    setBusy(true);
    setError("");
    try {
      setPlan(
        await api(
          "/teacher/lesson-plan",
          { method: "POST", body: JSON.stringify({ lesson_id: id }) },
          token,
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  const completed = lessons.filter((l) => l.status === "completed").length;
  const today = lessons.filter(
    (l) =>
      l.status === "booked" &&
      dateKey(l.schedule) === dateKey(new Date().toISOString()),
  );
  return (
    <>
      <h1>
        {section === "lessons" ? "Мои занятия" : `Здравствуйте, ${user?.name}`}
      </h1>
      <p>
        Часовой пояс: {timeZone}. <Link to="/settings">Изменить</Link>
      </p>
      {!loading && (
        <p>
          {completed} завершённых уроков ·{" "}
          {lessons.filter((l) => l.status === "booked").length} предстоящих
        </p>
      )}
      <p className="notice">
        Тестирование без оплаты. Бронирования не означают оплаченный доход.
      </p>
      {today.length > 0 && (
        <section className="panel">
          <h2>Сегодня</h2>
          {today.map((l) => (
            <p key={l.id}>
              {l.subject} ·{" "}
              {new Date(l.schedule).toLocaleTimeString("ru-RU", {
                hour: "2-digit",
                minute: "2-digit",
                timeZone,
              })}{" "}
              · <Link to={`/lessons/${l.id}/chat`}>Чат и Zoom</Link>
            </p>
          ))}
        </section>
      )}
      {error && (
        <p role="alert" className="notice">
          {error}
        </p>
      )}
      {section === "overview" && teacher && <TeacherServices />}
      {section === "overview" && (
        <div className="recording-actions">
          <Link
            className="button outline"
            to={teacher ? "/teacher/lessons" : "/student/lessons"}
          >
            Все занятия
          </Link>
          <Link
            className="button outline"
            to={teacher ? "/teacher/homework" : "/student/homework"}
          >
            Домашние задания
          </Link>
        </div>
      )}
      {section === "lessons" && (
        <section id="lessons">
          <h2>Все мои занятия</h2>
          {loading && <p role="status">Загружаем занятия…</p>}
          {!loading && !error && !lessons.length && (
            <p>
              Занятий пока нет. <Link to="/offers">Выбрать преподавателя</Link>
            </p>
          )}
          {lessons.map((l) => (
            <article className="panel spaced" key={l.id}>
              <h3>
                {l.subject} · урок №{l.id}
              </h3>
              <p>
                {teacher ? l.student : l.teacher} · {formatDate(l.schedule)} ·{" "}
                {l.duration} мин
              </p>
              <p>
                {l.status === "completed"
                  ? "Завершён"
                  : l.status === "cancelled"
                    ? "Отменён"
                    : "Запланирован"}
              </p>
              <div className="recording-actions">
                <Link
                  className="button outline small"
                  to={`/lessons/${l.id}/chat`}
                >
                  Чат и Zoom
                </Link>
                <Link
                  className="button outline small"
                  to={`/tutor?lesson=${l.id}`}
                >
                  Запись, конспект и тьютор
                </Link>
                {teacher && l.status !== "cancelled" && (
                  <>
                    <button
                      className="button small"
                      disabled={busy}
                      onClick={() => void prepare(l.id)}
                    >
                      ИИ-план урока
                    </button>
                    {l.status !== "completed" && (
                      <button
                        className="button outline small"
                        disabled={busy || new Date(l.schedule) > new Date()}
                        onClick={() => void action(`/lessons/${l.id}/complete`)}
                      >
                        Отметить завершённым
                      </button>
                    )}
                  </>
                )}
              </div>
              {!teacher && l.status === "completed" && !l.reviewed && (
                <form
                  className="learning-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void action("/reviews", {
                      lesson_id: l.id,
                      rating: Number(ratings[l.id] ?? 5),
                      text: reviews[l.id],
                    });
                  }}
                >
                  <label>
                    Оценка учителю
                    <select
                      value={ratings[l.id] ?? "5"}
                      onChange={(e) =>
                        setRatings({ ...ratings, [l.id]: e.target.value })
                      }
                    >
                      {[5, 4, 3, 2, 1].map((n) => (
                        <option key={n}>{n}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Отзыв
                    <textarea
                      required
                      maxLength={2000}
                      value={reviews[l.id] ?? ""}
                      onChange={(e) =>
                        setReviews({ ...reviews, [l.id]: e.target.value })
                      }
                    />
                  </label>
                  <button
                    className="button small"
                    disabled={busy || !reviews[l.id]?.trim()}
                  >
                    Оценить урок
                  </button>
                </form>
              )}
              {l.status === "booked" && (
                <LessonActions id={l.id} onChange={() => void load()} />
              )}
              {teacher && l.status !== "cancelled" && (
                <HomeworkEditor lessonId={l.id} />
              )}
              {!teacher && l.status !== "cancelled" && (
                <TestPayment lessonId={l.id} />
              )}
              {l.reviewed && <p>Оценка ученика сохранена.</p>}
            </article>
          ))}
        </section>
      )}
      {plan && (
        <section className="panel spaced">
          <h2>Черновик плана · урок №{plan.lesson_id}</h2>
          {plan.blocks.map((b, i) => (
            <p key={i}>
              {b.title} — {b.minutes} мин
            </p>
          ))}
          <p style={{ whiteSpace: "pre-wrap" }}>{plan.suggestions}</p>
          <p>Проверьте и адаптируйте рекомендации перед занятием.</p>
        </section>
      )}
      {section === "overview" && <ProgressPanel teacher={teacher} />}
    </>
  );
}
