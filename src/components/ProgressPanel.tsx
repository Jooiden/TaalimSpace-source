import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
type Progress = {
  completed_lessons: number;
  homework_total: number;
  homework_submitted: number;
  homework_checked: number;
  topics: { topic: string; lessons: number }[];
};
export default function ProgressPanel({
  teacher = false,
}: {
  teacher?: boolean;
}) {
  const { token } = useAuth();
  const [data, setData] = useState<Progress>();
  const [students, setStudents] = useState<
    { student: string; completed_lessons: number; awaiting_review: number }[]
  >([]);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!token) return;
    if (teacher)
      api<typeof students>("/progress/students", {}, token)
        .then(setStudents)
        .catch((e) => setError(String(e)));
    else
      api<Progress>("/progress", {}, token)
        .then(setData)
        .catch((e) => setError(String(e)));
  }, [token, teacher]);
  return (
    <section className="panel spaced">
      <h2>{teacher ? "Ученики и проверка" : "Мой прогресс"}</h2>
      {data && (
        <>
          <p>
            Пройдено уроков: {data.completed_lessons}. Сдано заданий:{" "}
            {data.homework_submitted} из {data.homework_total}. Проверено
            учителем: {data.homework_checked}.
          </p>
          <ul>
            {data.topics.map((t) => (
              <li key={t.topic}>
                {t.topic} — {t.lessons} уроков
              </li>
            ))}
          </ul>
          <p>Количество занятий и сданных работ не означает освоение темы.</p>
        </>
      )}
      {students.map((s, i) => (
        <p key={i}>
          {s.student}: {s.completed_lessons} завершённых уроков,{" "}
          {s.awaiting_review} работ ожидают проверки.
        </p>
      ))}
      <p role="alert">{error}</p>
    </section>
  );
}
