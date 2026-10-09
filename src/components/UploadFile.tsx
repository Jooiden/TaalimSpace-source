import { useState } from "react";
import { api, BASE } from "../lib/api";
import { useAuth } from "../lib/auth";
export function UploadFile({
  path,
  photo = false,
  onSaved,
}: {
  path: string;
  photo?: boolean;
  onSaved?: () => void;
}) {
  const { token } = useAuth();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <label className="spaced">
      {photo ? "Фото преподавателя (до 5 МБ)" : "Прикрепить файл (до 10 МБ)"}
      <input
        type="file"
        disabled={busy}
        accept={
          photo
            ? "image/png,image/jpeg,image/webp"
            : "image/png,image/jpeg,image/webp,application/pdf,text/plain"
        }
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          setBusy(true);
          try {
            await api(
              path + `?name=${encodeURIComponent(file.name)}`,
              {
                method: "POST",
                headers: { "Content-Type": "application/octet-stream" },
                body: file,
              },
              token,
            );
            setMessage("Файл сохранён.");
            onSaved?.();
          } catch (e) {
            setMessage(String(e));
          } finally {
            setBusy(false);
          }
        }}
      />
      <span role="status">{message}</span>
    </label>
  );
}
export function FileDownload({ id }: { id: string }) {
  const { token } = useAuth();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function download() {
    setBusy(true);
    try {
      const r = await fetch(`${BASE}/files/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error("Файл недоступен");
      const b = await r.blob();
      const url = URL.createObjectURL(b);
      const a = document.createElement("a");
      a.href = url;
      const name = r.headers
        .get("content-disposition")
        ?.match(/filename\*=utf-8''([^;]+)/i)?.[1];
      a.download = name ? decodeURIComponent(name) : "material";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button
        className="button outline small"
        disabled={busy}
        onClick={() => void download()}
      >
        Скачать файл / изображение
      </button>
      <span role="alert">{error}</span>
    </>
  );
}
