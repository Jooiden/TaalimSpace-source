import { useEffect, useState, type FormEvent } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
export type Service = {
  id: number;
  title: string;
  description: string;
  price: number;
  published: boolean;
};
export default function ServiceManager({ onChange }: { onChange: () => void }) {
  const { token } = useAuth();
  const [items, setItems] = useState<Service[]>([]);
  const [editing, setEditing] = useState<Service>();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      setItems(await api("/offers/mine/services", {}, token));
    } catch (e) {
      setMessage(String(e));
    }
  }
  useEffect(() => {
    void load();
  }, [token]);
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    try {
      await api(
        "/offers/mine/services" + (editing ? `/${editing.id}` : ""),
        {
          method: editing ? "PATCH" : "POST",
          body: JSON.stringify({
            title: f.get("title"),
            description: f.get("description"),
            price: f.get("price"),
            published: f.get("published") === "on",
          }),
        },
        token,
      );
      await load();
      setEditing(undefined);
      onChange();
      setMessage("Услуга сохранена.");
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel spaced">
      <h3>Услуги с отдельными ценами</h3>
      {items.map((s) => (
        <p key={s.id}>
          {s.title} · {s.price} сом · {s.published ? "Опубликована" : "Скрыта"}{" "}
          <button
            type="button"
            className="button outline small"
            onClick={() => setEditing(s)}
          >
            Изменить
          </button>
        </p>
      ))}
      <form
        className="learning-form"
        key={editing?.id ?? "new"}
        onSubmit={save}
      >
        <label>
          Название
          <input
            name="title"
            minLength={2}
            maxLength={100}
            defaultValue={editing?.title}
            required
          />
        </label>
        <label>
          Описание
          <textarea
            name="description"
            minLength={10}
            maxLength={5000}
            defaultValue={editing?.description}
            required
          />
        </label>
        <label>
          Цена, сом
          <input
            name="price"
            type="number"
            min={0}
            max={100000}
            step="0.01"
            defaultValue={editing?.price}
            required
          />
        </label>
        <label>
          <input
            name="published"
            type="checkbox"
            defaultChecked={editing?.published ?? true}
          />
          Показывать ученикам
        </label>
        <button className="button" disabled={busy}>
          {editing ? "Сохранить" : "Добавить услугу"}
        </button>
        {editing && (
          <button type="button" onClick={() => setEditing(undefined)}>
            Новая услуга
          </button>
        )}
      </form>
      <p role="status">{message}</p>
    </section>
  );
}
