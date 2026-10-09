import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
type Peer = { id: number; name: string; last?: string; unread?: number };
type Message = {
  id: number;
  sender_id: number;
  text: string;
  created_at: string;
};
export default function Dialogs() {
  const { token, user } = useAuth();
  const [params] = useSearchParams();
  const [peers, setPeers] = useState<Peer[]>([]);
  const [selected, setSelected] = useState<Peer>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!token) return;
    const teacher = params.get("teacher");
    if (teacher)
      api<Peer>(`/dialogs/teacher/${teacher}`, {}, token)
        .then(setSelected)
        .catch((e) => setError(String(e)));
  }, [token, params]);
  useEffect(() => {
    if (!token) return;
    let active = true;
    const load = () =>
      api<Peer[]>("/dialogs", {}, token)
        .then((rows) => {
          if (active) setPeers(rows);
        })
        .catch((e) => {
          if (active) setError(String(e));
        });
    void load();
    const timer = setInterval(load, 5000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [token]);
  useEffect(() => {
    if (!token || !selected) return;
    let active = true;
    let cursor = 0;
    setMessages([]);
    const load = async () => {
      try {
        const rows = await api<Message[]>(
          `/dialogs/${selected.id}?after=${cursor}`,
          {},
          token,
        );
        if (!active) return;
        if (rows.length) {
          cursor = rows[rows.length - 1].id;
          setMessages((old) => [
            ...old,
            ...rows.filter((r) => !old.some((m) => m.id === r.id)),
          ]);
        }
        await api(`/dialogs/${selected.id}/read`, { method: "POST" }, token);
      } catch (e) {
        if (active) setError(String(e));
      }
    };
    void load();
    const timer = setInterval(load, 2000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [selected, token]);
  async function send() {
    if (!selected) return;
    setBusy(true);
    try {
      await api(
        `/dialogs/${selected.id}`,
        { method: "POST", body: JSON.stringify({ text }) },
        token,
      );
      setText("");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="container page-section">
      <h1>Сообщения</h1>
      <div className="dashboard-columns">
        <aside className="panel">
          <h2>Диалоги</h2>
          {!peers.length && (
            <p>Выберите преподавателя в каталоге и нажмите «Написать».</p>
          )}
          {peers.map((p) => (
            <p key={p.id}>
              <button className="button outline" onClick={() => setSelected(p)}>
                {p.name} {p.unread ? `(${p.unread})` : ""}
              </button>
            </p>
          ))}
        </aside>
        <section className="panel">
          {selected && (
            <>
              <h2>{selected.name}</h2>
              {messages.map((m) => (
                <article className="tutor-bubble" key={m.id}>
                  <strong>
                    {m.sender_id === user?.id ? "Вы" : selected.name}
                  </strong>
                  <p>{m.text}</p>
                  <small>{new Date(m.created_at).toLocaleString()}</small>
                </article>
              ))}
              <form
                className="learning-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  void send();
                }}
              >
                <label>
                  Сообщение
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    maxLength={4000}
                    required
                  />
                </label>
                <button className="button" disabled={busy || !text.trim()}>
                  Отправить
                </button>
              </form>
            </>
          )}
          <p role="alert">{error}</p>
        </section>
      </div>
    </div>
  );
}
