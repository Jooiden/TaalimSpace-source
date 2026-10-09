import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { api, DEMO_MODE } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type Message = { role: "user" | "assistant"; content: string };

export default function TutorChat({
  lessonId,
  personal = false,
}: {
  lessonId?: number;
  personal?: boolean;
}) {
  const { token } = useAuth();
  const demo = DEMO_MODE && !token;
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const controller = useRef<AbortController | null>(null);
  const log = useRef<HTMLDivElement>(null);
  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [messages, busy]);

  async function send() {
    const message = draft.trim();
    if (!message || controller.current) return;
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError("");
    try {
      const result = await api<{ reply: string }>(
        demo
          ? "/tutor/demo/chat"
          : personal && !lessonId
            ? "/tutor/personal"
            : "/tutor/chat",
        {
          method: "POST",
          signal: request.signal,
          body: JSON.stringify({
            message,
            history: messages.slice(-10),
            ...(lessonId ? { lesson_id: lessonId } : {}),
          }),
        },
        token,
      );
      setMessages((previous) => [
        ...previous,
        { role: "user", content: message },
        { role: "assistant", content: result.reply },
      ]);
      setDraft("");
    } catch (e) {
      if (!request.signal.aborted)
        setError(
          e instanceof TypeError
            ? "Сервер недоступен. Проверьте, запущен ли backend на порту 8000."
            : e instanceof Error
              ? e.message
              : "Не удалось получить ответ.",
        );
    } finally {
      controller.current = null;
      setBusy(false);
    }
  }

  return (
    <section
      id="tutor"
      className="panel tutor-chat"
      aria-labelledby="tutor-title"
    >
      <div className="section-heading compact">
        <h2 id="tutor-title">
          <Sparkles size={21} /> AI-тьютор
        </h2>
        <button
          type="button"
          className="button outline small"
          disabled={busy || !messages.length}
          onClick={() => {
            setMessages([]);
            setError("");
          }}
        >
          Новый диалог
        </button>
      </div>
      <p className="muted">
        {demo
          ? "Groq · материалы выбранной локальной записи; без записи — демонстрационный пример."
          : lessonId
            ? "Разберём тему выбранного урока вместе."
            : "Обзор ваших последних 20 уроков. Для подробностей выберите нужное занятие."}{" "}
        История хранится только до ухода со страницы.
      </p>
      <div
        className="tutor-messages"
        role="log"
        aria-live="polite"
        aria-label="Диалог с тьютором"
        ref={log}
      >
        {!messages.length && (
          <div className="tutor-bubble assistant">
            Привет! Напиши, что непонятно, или покажи своё решение — разберём
            его по шагам.
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`tutor-bubble ${message.role}`}>
            <strong>{message.role === "user" ? "Вы" : "AI-тьютор"}</strong>
            <ReactMarkdown
              remarkPlugins={[remarkMath]}
              rehypePlugins={[
                [rehypeKatex, { trust: false, strict: "ignore" }],
              ]}
              components={{ img: () => null }}
            >
              {message.content
                .replace(
                  /\\\[([\s\S]*?)\\\]/g,
                  (_, math: string) => `\n$$\n${math}\n$$\n`,
                )
                .replace(
                  /\\\(([\s\S]*?)\\\)/g,
                  (_, math: string) => `$${math}$`,
                )}
            </ReactMarkdown>
          </div>
        ))}
        {busy && <p role="status">Тьютор готовит ответ…</p>}
      </div>
      {!messages.length && (
        <div className="tutor-suggestions">
          {["Объясни главную тему урока", "Что мне стоит повторить?"].map(
            (text) => (
              <button
                type="button"
                className="button outline small"
                key={text}
                disabled={busy}
                onClick={() => setDraft(text)}
              >
                {text}
              </button>
            ),
          )}
        </div>
      )}
      {error && (
        <p className="notice" role="alert">
          {error} Ваш вопрос сохранён — можно отправить снова.
        </p>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void send();
        }}
      >
        <label htmlFor="tutor-question">Ваш вопрос</label>
        <textarea
          id="tutor-question"
          value={draft}
          maxLength={4000}
          rows={3}
          disabled={busy}
          placeholder="Например: объясни тему прошлого урока на простом примере"
          onChange={(event) => setDraft(event.target.value)}
        />
        <div className="tutor-form-footer">
          <small>ИИ может ошибаться. Проверяйте важные ответы.</small>
          <button
            className="button"
            disabled={busy || !draft.trim()}
            type="submit"
          >
            <Send size={16} /> {busy ? "Отправляем…" : "Отправить"}
          </button>
        </div>
      </form>
    </section>
  );
}
