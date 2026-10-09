import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import {
  downloadRecording,
  mediaQuery,
  stages,
  type Recording,
} from "../../lib/recordings";

export default function RecordingPanel({
  lessonId,
  refresh = 0,
}: {
  lessonId: number;
  refresh?: number;
}) {
  const { token } = useAuth();
  const [rows, setRows] = useState<Recording[]>([]);
  const [error, setError] = useState("");
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let stopped = false;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const started = Date.now();
    async function load() {
      try {
        const result = await api<Recording[]>(
          `/recordings/lesson/${lessonId}?${mediaQuery(token)}`,
          { signal: controller.signal },
          token,
        );
        if (stopped) return;
        setRows(result);
        setError("");
        if (
          result.some((row) => ["queued", "processing"].includes(row.status)) &&
          Date.now() - started < 20 * 60000
        )
          timer = setTimeout(load, 5000);
      } catch (e) {
        if (!stopped)
          setError(
            e instanceof Error ? e.message : "Не удалось загрузить записи.",
          );
      }
    }
    void load();
    return () => {
      stopped = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [lessonId, refresh, tick, token]);

  async function retry(row: Recording) {
    try {
      await api(
        `/recordings/${row.id}/retry?${mediaQuery(token)}`,
        { method: "POST" },
        token,
      );
      setTick((v) => v + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось повторить.");
    }
  }
  async function download(row: Recording, kind: "file" | "transcript") {
    try {
      await downloadRecording(row.id, kind, token, row.filename);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка скачивания.");
    }
  }
  return (
    <section className="panel recording-panel">
      <div className="section-heading compact">
        <h2>Записи и итоги урока</h2>
        <button
          className="button outline small"
          onClick={() => setTick((v) => v + 1)}
        >
          Обновить
        </button>
      </div>
      {error && (
        <p role="alert" className="notice">
          {error}
        </p>
      )}
      {!rows.length && !error && (
        <p className="muted">
          После загрузки и обработки здесь появятся запись, транскрипт и
          карточка урока.
        </p>
      )}
      {rows.map((row) => (
        <article className="recording-result" key={row.id}>
          <div className="section-heading compact">
            <strong>{row.card?.topic || "Запись урока"}</strong>
            <span className="tag">
              {row.status === "failed"
                ? "Нужен повтор"
                : stages[row.stage] || row.stage}
            </span>
          </div>
          <p className="muted">
            {new Date(row.created_at).toLocaleString("ru-RU")}
            {row.duration ? ` · ${Math.ceil(row.duration / 60)} мин` : ""}
          </p>
          <div className="recording-actions">
            <button
              className="button outline small"
              onClick={() => void download(row, "file")}
            >
              Скачать исходный файл
            </button>
            {row.transcript && (
              <button
                className="button outline small"
                onClick={() => void download(row, "transcript")}
              >
                Транскрипт .txt
              </button>
            )}
          </div>
          {row.error && (
            <p className="notice" role="alert">
              {row.error}
            </p>
          )}
          {row.status === "failed" && (
            <button className="button small" onClick={() => void retry(row)}>
              Повторить обработку
            </button>
          )}
          {row.card && (
            <>
              <h3>Конспект</h3>
              <p className="lesson-summary-text">{row.card.summary}</p>
              <h3>Пройденные темы</h3>
              <ul>
                {row.card.topics_covered.map((topic, i) => (
                  <li key={i}>{topic}</li>
                ))}
              </ul>
              {row.card.insufficient_evidence && (
                <p className="notice">{row.card.insufficient_evidence}</p>
              )}
              {(["understood", "difficult"] as const).map(
                (kind) =>
                  row.card![kind].length > 0 && (
                    <div key={kind}>
                      <h3>
                        {kind === "understood"
                          ? "Что получилось"
                          : "Что вызвало затруднения"}
                      </h3>
                      {row.card![kind].map((finding, i) => (
                        <p key={i}>
                          <strong>{finding.topic}</strong>
                          <br />
                          Основание: «{finding.evidence}»
                        </p>
                      ))}
                    </div>
                  ),
              )}
              <h3>Повторить</h3>
              <ul>
                {row.card.review_before_next.map((topic, i) => (
                  <li key={i}>{topic}</li>
                ))}
              </ul>
              <h3>Домашнее задание преподавателя</h3>
              {!row.card.teacher_homework.length && (
                <p>В записи не найдено назначенного задания.</p>
              )}
              <ul>
                {row.card.teacher_homework.map((task, i) => (
                  <li key={i}>{task.task}</li>
                ))}
              </ul>
              <h3>Дополнительная практика · предложено ИИ</h3>
              <ul>
                {row.card.extra_practice.map((task, i) => (
                  <li key={i}>
                    {task.task}
                    {task.hint && (
                      <details>
                        <summary>Подсказка</summary>
                        {task.hint}
                      </details>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
          {row.transcript && (
            <details>
              <summary>Текст урока</summary>
              <p className="lesson-summary-text">{row.transcript}</p>
            </details>
          )}
        </article>
      ))}
    </section>
  );
}
