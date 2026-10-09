import { useEffect, useState } from "react";
import { api } from "../lib/api";
export default function TeacherDetails({ id }: { id: number }) {
  const [reviews, setReviews] = useState<
    { id: number; name: string; rating: number; text: string }[]
  >([]);
  const [services, setServices] = useState<
    { id: number; title: string; description: string; price: number }[]
  >([]);
  const [error, setError] = useState("");
  useEffect(() => {
    void Promise.all([
      api<typeof reviews>(`/directory/${id}/reviews`).then(setReviews),
      api<typeof services>(`/directory/${id}/services`).then(setServices),
    ]).catch((e) => setError(String(e)));
  }, [id]);
  return (
    <>
      <h3>Услуги преподавателя</h3>
      {services.map((s) => (
        <p key={s.id}>
          <strong>
            {s.title} — {s.price} сом
          </strong>
          <br />
          {s.description}
        </p>
      ))}
      <h3>Отзывы учеников</h3>
      {!reviews.length && <p>Отзывов пока нет.</p>}
      {reviews.map((r) => (
        <blockquote key={r.id}>
          <strong>
            {r.name} · ★ {r.rating}
          </strong>
          <p>{r.text}</p>
        </blockquote>
      ))}
      <p role="alert">{error}</p>
    </>
  );
}
