import { useTimeZone } from "../lib/useTimeZone";
import TeacherDetails from "../components/TeacherDetails";
import { TeacherAvatar } from "../components/teacher-card/TeacherCard";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { Teacher } from "../types";

type Offer = Teacher & { completed_lessons: number };
type Slot = {
  id: number;
  start_time: string;
  duration_min: number;
  price?: number;
  service_title?: string;
};
export default function Offers() {
  const { timeZone, formatDate } = useTimeZone();
  const { user, token } = useAuth();
  const [query, setQuery] = useState("");
  const [maxPrice, setMaxPrice] = useState(100000);
  const [rating, setRating] = useState(0);
  const [sort, setSort] = useState("rating");
  const [favorites, setFavorites] = useState<number[]>([]);
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  useEffect(() => {
    if (token)
      api<number[]>("/directory/favorites", {}, token)
        .then(setFavorites)
        .catch(() => {});
    else setFavorites([]);
  }, [token]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Offer>();
  const [slots, setSlots] = useState<Slot[]>([]);
  const [error, setError] = useState("");
  const [lessonId, setLessonId] = useState<number>();
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const control = new AbortController();
    api<Offer[]>("/offers", { signal: control.signal })
      .then(setOffers)
      .catch((e) => {
        if (!control.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!control.signal.aborted) setLoading(false);
      });
    return () => control.abort();
  }, []);
  async function choose(offer: Offer) {
    setError("");
    setLessonId(undefined);
    setSelected(offer);
    setSlots([]);
    setBusy(true);
    try {
      setSlots(await api<Slot[]>(`/offers/${offer.id}/slots`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }
  async function book(slot: Slot) {
    setBusy(true);
    setError("");
    try {
      const result = await api<{ lesson_id: number }>(
        "/booking",
        { method: "POST", body: JSON.stringify({ slot_id: slot.id }) },
        token,
      );
      setLessonId(result.lesson_id);
      setSlots((previous) => previous.filter((s) => s.id !== slot.id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось записаться");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="container page-section">
      <h1>Записаться на урок</h1>
      <p>
        Услуги зарегистрированных преподавателей. Сейчас бронирование без оплаты
        — деньги не списываются.
      </p>
      <Link to="/catalog?demo=1">Посмотреть демонстрационный каталог</Link>
      {error && (
        <p role="alert" className="notice">
          {error}
        </p>
      )}
      {loading && <p role="status">Загружаем преподавателей…</p>}
      {!loading && offers.length === 0 && !error && (
        <p>
          Услуг пока нет. Преподаватель может опубликовать свою в личном
          кабинете.
        </p>
      )}
      <div className="learning-form offers-filters panel spaced">
        <label>
          Предмет, язык или имя
          <input value={query} onChange={(e) => setQuery(e.target.value)} />
        </label>
        <label>
          Цена основной услуги до, сом
          <input
            type="number"
            min={0}
            value={maxPrice}
            onChange={(e) => setMaxPrice(Number(e.target.value))}
          />
        </label>
        <label>
          Рейтинг
          <select
            value={rating}
            onChange={(e) => setRating(Number(e.target.value))}
          >
            <option value={0}>Любой</option>
            <option value={4}>От 4</option>
            <option value={4.5}>От 4.5</option>
          </select>
        </label>
        <label>
          Сортировка
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="rating">По рейтингу</option>
            <option value="price">По цене</option>
            <option value="reviews">По отзывам</option>
          </select>
        </label>
        {user && (
          <label>
            <input
              type="checkbox"
              checked={onlyFavorites}
              onChange={(e) => setOnlyFavorites(e.target.checked)}
            />
            Только избранные
          </label>
        )}
      </div>
      <div className="dashboard-columns">
        {offers
          .filter(
            (o) =>
              (o.name + " " + o.subject + " " + o.languages.join(" "))
                .toLowerCase()
                .includes(query.toLowerCase()) &&
              o.price <= maxPrice &&
              (o.rating ?? 0) >= rating &&
              (!onlyFavorites || favorites.includes(o.id)),
          )
          .sort((a, b) =>
            sort === "price"
              ? a.price - b.price
              : sort === "reviews"
                ? b.reviews_count - a.reviews_count
                : (b.rating ?? 0) - (a.rating ?? 0),
          )
          .map((offer) => (
            <article className="panel spaced" key={offer.id}>
              <TeacherAvatar teacher={offer} live />
              <h2>{offer.name}</h2>
              {user && (
                <button
                  className="button outline small"
                  onClick={async () => {
                    try {
                      await api(
                        `/directory/favorites/${offer.id}`,
                        {
                          method: favorites.includes(offer.id)
                            ? "DELETE"
                            : "POST",
                        },
                        token,
                      );
                      setFavorites(
                        await api("/directory/favorites", {}, token),
                      );
                    } catch (e) {
                      setError(String(e));
                    }
                  }}
                >
                  {favorites.includes(offer.id)
                    ? "Убрать из избранного"
                    : "В избранное"}
                </button>
              )}
              {user && (
                <Link
                  className="button outline small"
                  to={`/messages?teacher=${offer.id}`}
                >
                  Написать
                </Link>
              )}
              <h3>{offer.subject}</h3>
              <p>{offer.bio}</p>
              <p>
                {offer.languages.join(", ")} · опыт {offer.experience} лет
              </p>
              <p>
                {offer.price} сом за занятие · длительность указана у времени
              </p>
              <p>
                {offer.rating === null
                  ? "Нет отзывов"
                  : `★ ${offer.rating} · ${offer.reviews_count} отзывов`}{" "}
                · {offer.completed_lessons} проведённых уроков
              </p>
              <button
                className="button"
                disabled={busy}
                onClick={() => void choose(offer)}
              >
                Выбрать время
              </button>
            </article>
          ))}
      </div>
      {selected && (
        <section className="panel spaced">
          <h2>{selected.name}: свободное время</h2>
          <TeacherDetails id={selected.id} />
          <p>Время отображается в вашем часовом поясе: {timeZone}.</p>
          {busy && <p role="status">Подождите…</p>}
          {!busy && !slots.length && <p>Свободных дат пока нет.</p>}
          {slots.map((slot) => (
            <div className="earning-row" key={slot.id}>
              <span>
                {formatDate(slot.start_time)} · {slot.duration_min} мин ·{" "}
                {slot.service_title} · {slot.price ?? selected.price} сом
              </span>
              {user ? (
                <button
                  className="button small"
                  disabled={busy}
                  onClick={() => void book(slot)}
                >
                  Записаться без оплаты
                </button>
              ) : (
                <Link to="/login">Войти для записи</Link>
              )}
            </div>
          ))}
          {lessonId && (
            <p role="status">
              Вы записаны!{" "}
              <Link to="/student/lessons">Открыть мои занятия</Link>
            </p>
          )}
        </section>
      )}
    </div>
  );
}
