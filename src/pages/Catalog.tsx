import Offers from "./Offers";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import TeacherCard from "../components/teacher-card/TeacherCard";
import { getTeachers } from "../lib/api";
import type { CatalogFilters, TeacherPage } from "../types";

const defaults: CatalogFilters = {
  subject: "",
  language: "",
  maxPrice: 2000,
  rating: 0,
  verified: false,
  sort: "rating_desc",
};
export default function Catalog() {
  const [params] = useSearchParams();
  const [filters, setFilters] = useState<CatalogFilters>({
    ...defaults,
    subject: params.get("subject") ?? "",
  });
  const [result, setResult] = useState<TeacherPage | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [page, setPage] = useState(1);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    getTeachers(filters, controller.signal, page)
      .then((data) => {
        if (!controller.signal.aborted) setResult(data);
      })
      .catch((e: Error) => {
        if (!controller.signal.aborted) setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters, retry, page]);
  function change<K extends keyof CatalogFilters>(
    key: K,
    value: CatalogFilters[K],
  ) {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  }
  function resetFilters() {
    setFilters(defaults);
    setPage(1);
  }
  if (params.get("demo") !== "1") return <Offers />;
  return (
    <div className="container page-section">
      <div className="page-intro">
        <span className="eyebrow">ТВОЙ СЛЕДУЮЩИЙ ШАГ</span>
        <h1>Найди своего преподавателя</h1>
        <p>Того, кто объяснит понятно и поможет двигаться к твоей цели.</p>
      </div>
      <div className="catalog-layout">
        <aside className="panel filters">
          <h3>
            <SlidersHorizontal size={18} />
            Фильтры
          </h3>
          <label>
            Предмет
            <select
              value={filters.subject}
              onChange={(e) => change("subject", e.target.value)}
            >
              <option value="">Все предметы</option>
              {[
                "Математика",
                "Английский",
                "Физика",
                "Русский язык",
                "Кыргызский язык",
                "Подготовка к ОРТ",
              ].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Язык обучения
            <select
              value={filters.language}
              onChange={(e) => change("language", e.target.value)}
            >
              <option value="">Любой язык</option>
              {["Русский", "Кыргызский", "Английский"].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Цена до <strong>{filters.maxPrice} сом</strong>
            <input
              type="range"
              min="300"
              max="2000"
              step="50"
              value={filters.maxPrice}
              onChange={(e) => change("maxPrice", Number(e.target.value))}
            />
          </label>
          <label>
            Рейтинг
            <select
              value={filters.rating}
              onChange={(e) => change("rating", Number(e.target.value))}
            >
              <option value="0">Любой рейтинг</option>
              <option value="4">От 4.0</option>
              <option value="4.5">От 4.5</option>
            </select>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.verified}
              onChange={(e) => change("verified", e.target.checked)}
            />
            Только проверенные
          </label>
          <button className="text-link" onClick={resetFilters}>
            <X size={15} />
            Сбросить фильтры
          </button>
        </aside>
        <div>
          <div className="catalog-toolbar">
            <span aria-live="polite">
              {loading
                ? "Ищем преподавателей…"
                : `Найдено преподавателей: ${result?.total ?? 0}`}
            </span>
            <label className="sort-label">
              Порядок
              <select
                value={filters.sort}
                onChange={(e) => change("sort", e.target.value)}
              >
                <option value="rating_desc">По рейтингу</option>
                <option value="price_asc">Сначала дешевле</option>
                <option value="price_desc">Сначала дороже</option>
                <option value="reviews_desc">По отзывам</option>
              </select>
            </label>
          </div>
          {error ? (
            <div className="empty-state" role="alert">
              <h3>Каталог пока недоступен</h3>
              <p>{error}</p>
              <button className="button" onClick={() => setRetry((r) => r + 1)}>
                Повторить
              </button>
            </div>
          ) : loading ? (
            <div className="teacher-grid two">
              {[1, 2, 3, 4].map((i) => (
                <div className="skeleton-card" key={i} />
              ))}
            </div>
          ) : result?.items.length ? (
            <div className="teacher-grid two">
              {result.items.map((t) => (
                <TeacherCard key={t.id} teacher={t} />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <Search size={32} />
              <h3>Пока никого не нашли</h3>
              <p>Попробуй увеличить бюджет или выбрать другой предмет.</p>
              <button className="button outline" onClick={resetFilters}>
                Сбросить фильтры
              </button>
            </div>
          )}
          {!loading && !error && result && result.total > result.page_size && (
            <nav
              className="catalog-toolbar spaced"
              aria-label="Страницы каталога"
            >
              <button
                className="button outline small"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Назад
              </button>
              <span>
                Страница {page} из {Math.ceil(result.total / result.page_size)}
              </span>
              <button
                className="button outline small"
                disabled={page * result.page_size >= result.total}
                onClick={() => setPage((p) => p + 1)}
              >
                Далее
              </button>
            </nav>
          )}
        </div>
      </div>
    </div>
  );
}
