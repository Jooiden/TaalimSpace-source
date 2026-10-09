import { useEffect, useState, type FormEvent } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
type Note = { id: number; title: string; text: string; kind: string };
export default function Library() {
  const { token } = useAuth();
  const [items, setItems] = useState<Note[]>([]);
  const [edit, setEdit] = useState<Note>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      setItems(await api("/library", {}, token));
    } catch (e) {
      setError(String(e));
    }
  }
  useEffect(() => {
    if (token) void load();
  }, [token]);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    const f = new FormData(e.currentTarget);
    try {
      await api(
        "/library" + (edit ? `/${edit.id}` : ""),
        {
          method: edit ? "PATCH" : "POST",
          body: JSON.stringify({
            title: f.get("title"),
            text: f.get("text"),
            kind: f.get("kind"),
          }),
        },
        token,
      );
      await load();
      setEdit(undefined);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="container page-section">
      <h1>Заметки и практика</h1>
      <p>
        Сохраняйте материалы и карточки для повторения. Для разбора с ИИ
        откройте тьютора.
      </p>
      <form
        key={edit?.id ?? "new"}
        className="learning-form panel"
        onSubmit={save}
      >
        <label>
          Формат
          <select name="kind" defaultValue={edit?.kind ?? "note"}>
            <option value="note">Заметка</option>
            <option value="flashcard">Карточка: вопрос и ответ</option>
          </select>
        </label>
        <label>
          Заголовок / вопрос
          <input
            name="title"
            maxLength={200}
            required
            defaultValue={edit?.title}
          />
        </label>
        <label>
          Текст / ответ
          <textarea
            name="text"
            maxLength={20000}
            required
            defaultValue={edit?.text}
          />
        </label>
        <button className="button" disabled={busy}>
          Сохранить
        </button>
        {edit && (
          <button type="button" onClick={() => setEdit(undefined)}>
            Новый материал
          </button>
        )}
      </form>
      {items.map((n) => (
        <article className="panel spaced" key={n.id}>
          <h2>{n.title}</h2>
          {n.kind === "flashcard" ? (
            <details>
              <summary>Показать ответ</summary>
              <p>{n.text}</p>
            </details>
          ) : (
            <p style={{ whiteSpace: "pre-wrap" }}>{n.text}</p>
          )}
          <button onClick={() => setEdit(n)}>Изменить</button>{" "}
          <button
            disabled={busy}
            onClick={async () => {
              if (!confirm("Удалить материал?")) return;
              try {
                await api(`/library/${n.id}`, { method: "DELETE" }, token);
                await load();
              } catch (e) {
                setError(String(e));
              }
            }}
          >
            Удалить
          </button>
        </article>
      ))}
      <p role="alert">{error}</p>
    </div>
  );
}
