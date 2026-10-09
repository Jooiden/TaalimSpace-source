import { useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
export default function PushSettings() {
  const { token } = useAuth();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function toggle(enable: boolean) {
    setBusy(true);
    try {
      if (!("serviceWorker" in navigator) || !("PushManager" in window))
        throw new Error("Этот браузер не поддерживает push.");
      const registration = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;
      let subscription = await registration.pushManager.getSubscription();
      if (enable) {
        const { public_key } = await api<{ public_key: string }>(
          "/notifications/push/key",
          {},
          token,
        );
        if (!public_key) throw new Error("Push ещё не настроен на сервере.");
        if ((await Notification.requestPermission()) !== "granted")
          throw new Error("Разрешите уведомления в настройках браузера.");
        const raw = atob(public_key.replace(/-/g, "+").replace(/_/g, "/"));
        const key = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) key[i] = raw.charCodeAt(i);
        subscription =
          subscription ||
          (await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: key,
          }));
        await api(
          "/notifications/push/subscribe",
          { method: "POST", body: JSON.stringify(subscription.toJSON()) },
          token,
        );
        setMessage("Push включены для этого браузера.");
      } else if (subscription) {
        await api(
          "/notifications/push/unsubscribe",
          { method: "POST", body: JSON.stringify(subscription.toJSON()) },
          token,
        );
        await subscription.unsubscribe();
        setMessage("Push отключены.");
      }
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel spaced">
      <h2>Уведомления браузера</h2>
      <button
        className="button"
        disabled={busy}
        onClick={() => void toggle(true)}
      >
        Включить push
      </button>{" "}
      <button
        className="button outline"
        disabled={busy}
        onClick={() => void toggle(false)}
      >
        Отключить
      </button>
      <p role="status">{message}</p>
    </section>
  );
}
