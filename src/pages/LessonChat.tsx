import { useTimeZone } from "../lib/useTimeZone";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { UploadFile, FileDownload } from "../components/UploadFile";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
type Message = {
  id: number;
  sender: string;
  sender_id: number;
  kind: string;
  text: string;
  created_at: string;
};
export default function LessonChat() {
  const { id } = useParams();
  const { formatDate } = useTimeZone();
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [kind, setKind] = useState("text");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const cursor = useRef(0);
  useEffect(() => {
    if (!token) return;
    let stopped = false;
    cursor.current = 0;
    setMessages([]);
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const rows = await api<Message[]>(
          `/messages/${id}?after=${cursor.current}`,
          {},
          token,
        );
        if (stopped) return;
        if (rows.length) {
          cursor.current = rows[rows.length - 1].id;
          setMessages((old) => [
            ...old,
            ...rows.filter((r) => !old.some((m) => m.id === r.id)),
          ]);
        }
        setError("");
        timer = setTimeout(load, rows.length === 100 ? 100 : 5000);
      } catch (e) {
        if (!stopped) {
          setError(e instanceof Error ? e.message : "Ошибка чата");
          timer = setTimeout(load, 10000);
        }
      }
    }
    void load();
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [id, token]);
  async function send() {
    setBusy(true);
    setError("");
    try {
      const item = await api<Message>(
        `/messages/${id}`,
        { method: "POST", body: JSON.stringify({ text: draft, kind }) },
        token,
      );
      setMessages((old) =>
        old.some((m) => m.id === item.id)
          ? old
          : [...old, item].sort((a, b) => a.id - b.id),
      );
      setDraft("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка отправки");
    } finally {
      setBusy(false);
    }
  }
  const zoom = [...messages].reverse().find((m) => m.kind === "zoom");
  return (
    <div className="container page-section">
      <h1>Чат урока №{id}</h1>
      <p>
        Обсудите занятие и отправьте ссылку на Zoom. Занятие проходит в Zoom.
      </p>
      {!token ? (
        <p className="notice">
          Чат доступен участникам забронированного урока.{" "}
          <Link to="/login">Войдите в аккаунт</Link> или{" "}
          <Link to="/offers">запишитесь на урок</Link>.
        </p>
      ) : (
        <>
          {zoom && (
            <a
              className="button"
              href={zoom.text}
              target="_blank"
              rel="noopener noreferrer"
            >
              Открыть встречу Zoom
            </a>
          )}
          <div className="panel spaced">
            <h2>Переписка с участником урока</h2>
            <UploadFile path={`/files/lesson/${id}`} />
            {messages.map((m) => (
              <article className="tutor-bubble" key={m.id}>
                <strong>{m.sender}</strong>
                <small> · {formatDate(m.created_at)}</small>
                <p>
                  {m.kind === "zoom" ? (
                    <a href={m.text} target="_blank" rel="noopener noreferrer">
                      {m.text}
                    </a>
                  ) : m.kind === "file" ? (
                    <FileDownload id={m.text} />
                  ) : (
                    m.text
                  )}
                </p>
              </article>
            ))}
            {!messages.length && <p>Сообщений пока нет.</p>}
            {error && <p role="alert">{error}</p>}
            <form
              className="learning-form"
              onSubmit={(e) => {
                e.preventDefault();
                void send();
              }}
            >
              <label>
                Тип сообщения
                <select value={kind} onChange={(e) => setKind(e.target.value)}>
                  <option value="text">Сообщение</option>
                  <option value="zoom">Ссылка на Zoom</option>
                </select>
              </label>
              <label>
                Текст
                <textarea
                  required
                  maxLength={4000}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                />
              </label>
              <button className="button" disabled={busy || !draft.trim()}>
                Отправить
              </button>
            </form>
          </div>
        </>
      )}
      <p>
        Запись делает участник в Zoom. После занятия загрузите файл в разделе
        тьютора.
      </p>
      <Link className="button outline" to={`/tutor?lesson=${id}`}>
        Загрузить запись и разобрать урок с ИИ
      </Link>
    </div>
  );
}
