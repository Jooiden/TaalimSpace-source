import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
export default function TestPayment({ lessonId }: { lessonId: number }) {
  const { token } = useAuth();
  const [status, setStatus] = useState<{ enabled: boolean; status: string }>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api<{ enabled: boolean; status: string }>(
      `/payments/status/${lessonId}`,
      {},
      token,
    )
      .then(setStatus)
      .catch(() => {});
  }, [lessonId, token]);
  if (!status?.enabled) return null;
  return (
    <div>
      <p>
        Тестовая оплата:{" "}
        {(
          {
            paid: "оплачено",
            pending: "ожидает оплаты",
            unpaid: "не оплачено",
            refunded: "возвращено",
            refund_required: "требуется возврат через Stripe",
          } as Record<string, string>
        )[status.status] ?? status.status}
      </p>
      {["pending", "unpaid"].includes(status.status) && (
        <button
          className="button small"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              const r = await api<{ url: string }>(
                "/payments/checkout",
                {
                  method: "POST",
                  body: JSON.stringify({ lesson_id: lessonId }),
                },
                token,
              );
              const url = new URL(r.url);
              if (
                url.protocol !== "https:" ||
                url.hostname !== "checkout.stripe.com"
              )
                throw new Error("Некорректный адрес оплаты");
              location.assign(url.href);
            } catch (e) {
              setError(String(e));
              setBusy(false);
            }
          }}
        >
          Оплатить тестовой картой
        </button>
      )}
      <p role="alert">{error}</p>
    </div>
  );
}
