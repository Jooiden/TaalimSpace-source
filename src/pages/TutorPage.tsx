import { useTimeZone } from "../lib/useTimeZone";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import DashboardLayout from "../components/layout/DashboardLayout";
import RecordingPanel from "../components/ai-summary/RecordingPanel";
import RecordingUpload from "../components/ai-tutor/RecordingUpload";
import TutorChat from "../components/ai-tutor/TutorChat";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { LessonPage } from "../types";
export default function TutorPage() {
  const { dateKey } = useTimeZone();
  const { token, user } = useAuth();
  const [query] = useSearchParams();
  const [refresh, setRefresh] = useState(0);
  const [lessons, setLessons] = useState<LessonPage>();
  const [selected, setSelected] = useState<number | undefined>(
    () => Number(query.get("lesson")) || undefined,
  );
  const [error, setError] = useState("");
  useEffect(() => {
    if (token)
      api<LessonPage>("/lessons", {}, token)
        .then(setLessons)
        .catch((e) => setError(e.message));
  }, [token]);
  return (
    <DashboardLayout teacher={user?.role === "teacher"}>
      <h1>Личный тьютор</h1>
      <p>
        Обсуждайте сегодняшний или любой прошлый урок. Материалы занятий
        сохраняются, переписка — только до ухода со страницы.
      </p>
      {!token && (
        <p className="notice">
          Сейчас доступен локальный пример. <Link to="/login">Войдите</Link>,
          чтобы тьютор видел ваши занятия.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {token && (
        <label>
          Контекст разговора
          <select
            value={selected ?? ""}
            onChange={(e) =>
              setSelected(e.target.value ? Number(e.target.value) : undefined)
            }
          >
            <option value="">Обзор последних 20 уроков</option>
            {lessons?.items.map((l) => (
              <option key={l.id} value={l.id}>
                {dateKey(l.schedule)} · {l.subject} · №{l.id}
              </option>
            ))}
          </select>
        </label>
      )}
      {(selected || !token) && (
        <>
          <RecordingUpload
            lessonId={selected ?? 1}
            onSaved={() => setRefresh((v) => v + 1)}
          />
          <RecordingPanel
            key={selected ?? 1}
            lessonId={selected ?? 1}
            refresh={refresh}
          />
        </>
      )}
      {token && !selected && (
        <p>Для загрузки записи или подробного конспекта выберите урок выше.</p>
      )}
      <TutorChat
        key={selected ?? "personal"}
        lessonId={selected ?? (!token ? 1 : undefined)}
        personal
      />
    </DashboardLayout>
  );
}
